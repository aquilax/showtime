from ratelimit import rate_limited
from cmd2 import Cmd
from tvmaze.api import Api
from showtime.database import Database
from showtime.output import Output
from showtime.config import Config

class Showtime(Cmd):

    prompt = '(showtime) '

    def __init__(self, api, db, config):
        Cmd.__init__(self)
        self.api = api
        self.db = db
        self.config = config
        self.output = Output(self.poutput, self.perror, self.pfeedback)

    def do_search(self, query):
        'Search shows [search Breaking Bad]'
        search_result = self.api.search.shows(query)
        search_result_tabe = self.output.format_search_results(search_result)
        self.output.poutput(search_result_tabe)

    def do_follow(self, show_id):
        'Follow show by id [follow 3]'
        show = self.api.show.get(show_id)
        self.db.add(show)
        episodes = self._get_episodes(int(show.id))
        self.db.sync_episodes(show.id, episodes);
        self.output.poutput('Added show: ({id}) {name} - {permiered}'.format(
                id=show.id, name=show.name, permiered=show.premiered))

    def do_shows(self, line):
        'Show all followed shows [shows]'
        shows = self.db.get_shows()
        shows_table = self.output.shows_table(shows)
        self.output.poutput(shows_table)

    def do_episodes(self, show_id):
        'Show all episodes for a show [episodes]'
        show = self.db.get_show(int(show_id))
        if not show:
            self.output.perror('Show {id} not found'.format(id=show_id))
            return
        episodes = self.db.get_episodes(int(show_id))

        episodes_tabe = self.output.format_episodes(show, episodes)
        self.output.poutput(episodes_tabe)

    @rate_limited(20, 10)
    def _get_episodes(self, show_id: int):
        return self.api.show.episodes(show_id)

    def do_sync(self, update):
        'Syncronise episodes with TVMaze [sync|sync update]'
        self.pfeedback('Syncing shows...')
        shows = self.db.get_active_shows() if update else self.db.get_shows()
        for show in shows:
            self.output.poutput('({id}) {name} - {permiered}'.format(
                id=show['id'], name=show['name'], permiered=show['permiered']))
            episodes = self._get_episodes(int(show['id']))
            self.db.sync_episodes(show['id'], episodes);
        self.pfeedback('Done')

    def do_watch(self, episode_id):
        'Mark episode as watched [watch 33]'
        self.db.update_watched(int(episode_id), True)

    def do_unwatch(self, episode_id):
        'Mark episode as not watched [unwatch 33]'
        self.db.update_watched(int(episode_id), False)

    def do_watch_all(self, show_id):
        'Mark all episodes in a show as watched'
        self.db.update_watched_show(int(show_id), True)

    def do_unwatch_all(self, show_id):
        'Mark all episodes in a show as not watched'
        self.db.update_watched_show(int(show_id), False)

    def do_watch_all_season(self, line):
        'Mark all episodes in a show and season as watched'
        show_id, season = line.split(' ')
        self.db.update_watched_show_season(int(show_id), int(season), True)

    def do_unwatch_all_season(self, line):
        'Mark all episodes in a show and season as not watched'
        show_id, season = line.split(' ')
        self.db.update_watched_show_season(int(show_id), int(season), False)

    def do_unwatched(self, line):
        'Show list of all episodes not watched yet'
        episodes = self.db.get_unwatched()
        episodes_tabe = self.output.format_unwatched(episodes)
        self.output.poutput(episodes_tabe)

    def do_config(self, line):
        'Show current configuration'
        self.output.poutput('Database path: {path}'.format(path=self.config.get('Database', 'Path')))

def main():
    api = Api()
    config = Config()
    config.load_config()
    db = Database(config.get('Database', 'Path'))
    Showtime(api, db, config).cmdloop()


if __name__ == '__main__':
    main()
