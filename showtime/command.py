import os
import readline
import atexit
import datetime
import dateutil.parser

from showtime.types import EpisodeId, ShowId
from . import __version__
from ratelimit import rate_limited
from cmd2 import Cmd
from tvmaze.api import Api
from showtime.database import Database
from showtime.output import Output
from showtime.config import Config
from typing import List


class Showtime(Cmd):

    current_show = None
    _show_ids: List[ShowId] = []
    _episode_ids: List[EpisodeId] = []

    def __init__(self, api, db, config):
        Cmd.__init__(self)
        self.api = api
        self.db = db
        self.config = config
        self.output = Output(self.poutput, self.perror, self.pfeedback)
        self.prompt = self._get_prompt()

    def _get_prompt(self, name: str = ''):
        if name:
            return '(showtime: {name}) '.format(name=name)
        return '(showtime) '

    def _get_list(self, ids: str) -> List[ShowId]:
        return [int(x) for x in ids.split(',')]

    def _search_shows(self, query: str):
        shows = self.db.get_shows()
        if query:
            query = query.lower()
            shows = [s for s in shows if query in s['name'].lower()]
        self._show_ids = [ShowId(s['id']) for s in shows]
        return sorted(shows, key=lambda k: k['name'])

    def _get_show_id(self, query: str) -> int:
        if query:
            try:
                return ShowId(query)
            except ValueError:
                shows = self._search_shows(query)
                if len(shows) == 1:
                    return ShowId(shows[0]['id'])
        if self.current_show:
            return ShowId(self.current_show['id'])
        raise Exception('Please provide a show_id')

    @rate_limited(20, 10)
    def _get_episodes(self, show_id: ShowId):
        return self.api.show.episodes(show_id)

    def do_search(self, query):
        '''Search shows [search <query>]'''
        search_result = self.api.search.shows(query)
        search_result_table = self.output.format_search_results(search_result)
        self.output.poutput(search_result_table)

    def do_follow(self, show_ids: str):
        '''Follow show(s) by id [follow <show_id>[,<show_id>...]]'''
        list_show_ids = self._get_list(show_ids)
        for show_id in list_show_ids:
            # add show to db
            show = self.api.show.get(show_id)
            self.db.add(show)
            # add episodes to db
            episodes = self._get_episodes(ShowId(show.id))
            self.db.sync_episodes(ShowId(show.id), episodes)
            self.output.poutput('Added show: ({id}) {name} - {premiered}'.format(
                id=show.id, name=show.name, premiered=show.premiered))

    def do_shows(self, query: str):
        '''Show all followed shows [shows <query>]'''
        shows = self._search_shows(query)
        shows_table = self.output.shows_table(shows)
        self.output.poutput(shows_table)

    def do_episodes(self, query: str):
        '''Show all episodes for a show [episodes <show_id>]'''
        show_id = self._get_show_id(query)
        show = self.db.get_show(show_id)
        if not show:
            self.output.perror('Show {id} not found'.format(id=show_id))
            return
        episodes = self.db.get_episodes(int(show_id))
        self._episode_ids = [s['id'] for s in episodes]
        episodes_tabe = self.output.format_episodes(show, episodes)
        self.output.poutput(episodes_tabe)

    def complete_episodes(self, text, line, start_index, end_index):
        return [str(id) for id in self._show_ids if str(id).startswith(text)]

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

    def do_watch_next(self, query: str):
        '''Mark next unwatched episode as watched [watch_next <show_id>]'''
        show_id = self._get_show_id(query)
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

    def do_delete_episode(self, query):
        '''Delete episode [delete_episode <episode_id>]'''
        episode_id = EpisodeId(episode_id)
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
        return [str(id) for id in self._show_ids if str(id).startswith(text)]

    def complete_watch(self, text, line, start_index, end_index):
        return [str(id) for id in self._episode_ids if str(id).startswith(text)]

    def do_unwatch(self, episode_id: str):
        '''Mark episode as not watched [unwatch <episode_id>]'''
        self.db.update_watched(EpisodeId(episode_id), False)

    def do_watch_all(self, query: str):
        '''Mark all episodes in a show as watched [watch_all <show_id>]'''
        show_id = self._get_show_id(query)
        self.db.update_watched_show(show_id, True)

    def do_unwatch_all(self, query: str):
        '''Mark all episodes in a show as not watched [unwatch_all <show_id>]'''
        show_id = self._get_show_id(query)
        self.db.update_watched_show(show_id, False)

    def do_watch_all_season(self, query):
        '''Mark all episodes in a show and season as watched [watch_all_season <show_id> <season>]'''
        show_id, season = query.split(' ')
        self.db.update_watched_show_season(ShowId(show_id), int(season), True)

    def do_unwatch_all_season(self, query):
        '''Mark all episodes in a show and season as not watched [unwatch_all_season <show_id> <season>]'''
        show_id, season = query.split(' ')
        self.db.update_watched_show_season(ShowId(show_id), int(season), False)

    def do_unwatched(self, _) -> None:
        '''Show list of all episodes not watched yet [unwatched]'''
        episodes = self.db.get_unwatched()
        episodes_tabe = self.output.format_unwatched(episodes)
        self.output.poutput(episodes_tabe)

    def do_last_seen(self, query: str) -> None:
        '''Mark all episodes as seen up to the defined one [last_seen <show_id> <season> <episode>]'''
        show_id, season, episode = query.split(' ')
        count = self.db.last_seen(ShowId(show_id), int(season), int(episode))
        self.output.poutput('{count} episodes marked as seen'.format(count=count))

    def do_config(self, _) -> None:
        '''Show current configuration [config]'''
        self.output.poutput('Database path: {path}'.format(path=self.config.get('Database', 'Path')))

    def do_export(self, _) -> None:
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

    def do_new_unwatched(self, days) -> None:
        '''Show unwatched episodes aired in the last 7 days[new_unwatched <days>]'''
        delta = datetime.timedelta(days=(int(days) if days else 7))
        from_date = (datetime.date.today() - delta)
        to_date = datetime.date.today()
        shows = self.db.aired_unseen_between(from_date, to_date)
        episodes_tabe = self.output.format_unwatched(sorted(shows, key=lambda k: k['airdate']))
        self.output.poutput(episodes_tabe)

    def do_version(self, _) -> None:
        '''Show current version'''
        self.output.poutput(__version__)


def main() -> None:
    # Persistent history
    history_file = os.path.expanduser('~/.showtime_history')
    if not os.path.exists(history_file):
        with open(history_file, "w") as file:
            file.write("")
    readline.read_history_file(history_file)
    atexit.register(readline.write_history_file, history_file)

    api = Api()
    config = Config()
    config.load()
    db = Database(config.get('Database', 'Path'))
    Showtime(api, db, config).cmdloop()


if __name__ == '__main__':
    main()
