import os
import readline
import atexit
import datetime
import dateutil.parser

from ratelimit import rate_limited
from cmd2 import Cmd
from tvmaze.api import Api
from showtime.database import Database
from showtime.output import Output
from showtime.config import Config


class Showtime(Cmd):

    current_show = None
    show_ids = []
    episode_ids = []

    def __init__(self, api, db, config):
        Cmd.__init__(self)
        self.api = api
        self.db = db
        self.config = config
        self.output = Output(self.poutput, self.perror, self.pfeedback)
        self.prompt = self._get_prompt()

    def _get_prompt(self, name: str=''):
        if name:
            return '(showtime: {name}) '.format(name=name)
        return '(showtime) '

    def _get_list(self, ids: str):
        return [int(x) for x in ids.split(',')]

    def _get_show_id(self, show_id: str) -> int:
        if show_id:
            try:
                return int(show_id)
            except ValueError:
                shows = self.search_shows(show_id)
                if len(shows) == 1:
                    return int(shows[0]['id'])
        if self.current_show:
            return int(self.current_show['id'])
        raise Exception('Please provide show_id')

    @rate_limited(20, 10)
    def _get_episodes(self, show_id: int):
        return self.api.show.episodes(show_id)

    def do_search(self, query):
        '''Search shows [search <query>]'''
        search_result = self.api.search.shows(query)
        search_result_tabe = self.output.format_search_results(search_result)
        self.output.poutput(search_result_tabe)

    def do_follow(self, show_ids):
        '''Follow show(s) by id [follow <show_id>[,<show_id>...]]'''
        show_ids = self._get_list(show_ids)
        for show_id in show_ids:
            show = self.api.show.get(show_id)
            self.db.add(show)
            episodes = self._get_episodes(int(show.id))
            self.db.sync_episodes(show.id, episodes)
            self.output.poutput('Added show: ({id}) {name} - {premiered}'.format(
                id=show.id, name=show.name, premiered=show.premiered))

    def search_shows(self, query):
        shows = self.db.get_shows()
        if query:
            query = query.lower()
            shows = [s for s in shows if query in s['name'].lower()]
        self.show_ids = [s['id'] for s in shows]
        return sorted(shows, key=lambda k: k['name'])

    def do_shows(self, query):
        '''Show all followed shows [shows <query>]'''
        shows = self.search_shows(query)
        shows_table = self.output.shows_table(shows)
        self.output.poutput(shows_table)

    def do_episodes(self, show_id):
        '''Show all episodes for a show [episodes <show_id>]'''
        show_id = self._get_show_id(show_id)
        show = self.db.get_show(show_id)
        if not show:
            self.output.perror('Show {id} not found'.format(id=show_id))
            return
        episodes = self.db.get_episodes(int(show_id))
        self.episode_ids = [s['id'] for s in episodes]
        episodes_tabe = self.output.format_episodes(show, episodes)
        self.output.poutput(episodes_tabe)

    def complete_episodes(self, text, line, start_index, end_index):
        return [str(id) for id in self.show_ids if str(id).startswith(text)]

    def do_set_show(self, show_id):
        '''Set show in context [set_show <show_id>]'''
        show_id = self._get_show_id(show_id)
        show = self.db.get_show(show_id)
        if not show:
            self.output.perror('Show {id} not found'.format(id=show_id))
            return
        self.current_show = show
        self.prompt = self._get_prompt(show['name'])

    def do_unset_show(self, _):
        '''Remove show from the context [unset_show]'''
        self.current_show = None
        self.prompt = self._get_prompt()

    def do_sync(self, _):
        '''Synchronize episodes with TVMaze [sync]'''
        self.pfeedback('Syncing shows...')
        shows = self.db.get_active_shows()
        for show in shows:
            self.output.poutput('{id}\t{name} ({premiered})'.format(
                id=show['id'], name=show['name'], premiered=show['premiered']))
            episodes = self._get_episodes(int(show['id']))
            self.db.sync_episodes(show['id'], episodes)
        self.pfeedback('Done')

    def do_watch(self, episode_ids):
        '''Mark episode as watched [watch <episode_id,...>]'''
        for episode_id in [e.strip() for e in episode_ids.split(',')]:
            self.db.update_watched(int(episode_id), True)

    def do_next(self, show_id):
        '''Mark next unwatched episode as watched [next <show_id>]'''
        return self.do_watch_next(show_id)

    def do_watch_next(self, show_id):
        '''Mark next unwatched episode as watched [watch_next <show_id>]'''
        show_id = self._get_show_id(show_id)
        show = self.db.get_show(show_id)
        if not show:
            self.output.perror('Show {id} not found'.format(id=show_id))
            return
        episode = self.db.get_next_unwatched(show_id)
        if episode:
            episodes_tabe = self.output.format_episodes(show, [episode])
            self.output.poutput(episodes_tabe)
            response = input('Did you watch this episode [Y/n]:')
            if response.lower() in ['y', '']:
                self.db.update_watched(int(episode['id']), True)
                return
            self.pfeedback('Canceling...')
            return
        self.output.perror('No episodes left unwatched for `{name}`'.format(name=show['name']))

    def do_delete_episode(self, episode_id):
        '''Delete episode [delete_episode <episode_id>]'''
        episode_id = int(episode_id)
        episode = self.db.get_episode(episode_id)
        if episode:
            show = self.db.get_show(episode['show_id'])
            episodes_tabe = self.output.format_episodes(show, [episode])
            self.output.poutput(episodes_tabe)
            response = input('Do you want to delete this episode [y/N]:')
            if response.lower() in ['y']:
                self.db.delete_episode(int(episode['id']))
                return
            self.pfeedback('Canceling...')
            return
        self.output.perror('Invalid episode_id')

    def complete_next(self, text, line, start_index, end_index):
        return self.complete_watch_next(text, line, start_index, end_index)

    def complete_watch_next(self, text, line, start_index, end_index):
        return [str(id) for id in self.show_ids if str(id).startswith(text)]

    def complete_watch(self, text, line, start_index, end_index):
        return [str(id) for id in self.episode_ids if str(id).startswith(text)]

    def do_unwatch(self, episode_id):
        '''Mark episode as not watched [unwatch <episode_id>]'''
        self.db.update_watched(int(episode_id), False)

    def do_watch_all(self, show_id):
        '''Mark all episodes in a show as watched [watch_all <show_id>]'''
        show_id = self._get_show_id(show_id)
        self.db.update_watched_show(show_id, True)

    def do_unwatch_all(self, show_id):
        '''Mark all episodes in a show as not watched [unwatch_all <show_id>]'''
        show_id = self._get_show_id(show_id)
        self.db.update_watched_show(show_id, False)

    def do_watch_all_season(self, line):
        '''Mark all episodes in a show and season as watched [watch_all_season <show_id> <season>]'''
        show_id, season = line.split(' ')
        self.db.update_watched_show_season(int(show_id), int(season), True)

    def do_unwatch_all_season(self, line):
        '''Mark all episodes in a show and season as not watched [unwatch_all_season <show_id> <season>]'''
        show_id, season = line.split(' ')
        self.db.update_watched_show_season(int(show_id), int(season), False)

    def do_unwatched(self, _):
        '''Show list of all episodes not watched yet [unwatched]'''
        episodes = self.db.get_unwatched()
        episodes_tabe = self.output.format_unwatched(episodes)
        self.output.poutput(episodes_tabe)

    def do_config(self, _):
        '''Show current configuration [config]'''
        self.output.poutput('Database path: {path}'.format(path=self.config.get('Database', 'Path')))

    def do_last_seen(self, line):
        '''Mark all episodes as seen up to the defined one [last_seen <show_id> <season> <episode>]'''
        show_id, season, episode = line.split(' ')
        count = self.db.last_seen(int(show_id), int(season), int(episode))
        self.output.poutput('{count} episodes marked as seen'.format(count=count))

    def do_export(self, line):
        '''Export seen episodes between dates[export <from_date> <to_date>]'''
        from_date = datetime.date(datetime.MINYEAR, 1, 1)
        to_date = datetime.date.today()
        try:
            from_date_s, to_date_s = line.split(' ')
            from_date = dateutil.parser.parse(from_date_s).date()
            to_date = dateutil.parser.parse(to_date_s).date()
        except:
            pass
        shows = self.db.seen_between(from_date, to_date)
        self.output.json(shows)

def main():
    # Persistent history
    history_file = os.path.expanduser('~/.showtime_history')
    if not os.path.exists(history_file):
        with open(history_file, "w") as fobj:
            fobj.write("")
    readline.read_history_file(history_file)
    atexit.register(readline.write_history_file, history_file)

    api = Api()
    config = Config()
    config.load_config()
    db = Database(config.get('Database', 'Path'))
    Showtime(api, db, config).cmdloop()


if __name__ == '__main__':
    main()
