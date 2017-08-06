from cmd2 import Cmd
from tvmaze.api import Api
from database import Database

class Showtime(Cmd):

    def __init__(self, api, db):
        Cmd.__init__(self)
        self.api = api
        self.db = db

    def do_search(self, query):
        search_result = api.search.shows(query)
        for show in search_result:
            print('({id}) {name} - {permiered} {url}'.format(
                id=show.id, name=show.name, permiered=show.premiered,
                url=show.url))

    def do_add(self, show_id):
        show = api.show.get(show_id)
        self.db.add(show)
        print('Added show: ({id}) {name} - {permiered}'.format(
                id=show.id, name=show.name, permiered=show.premiered))

    def do_episodes(self, show_id):
        show = db.get_show(int(show_id))
        episodes = db.get_episodes(int(show_id))
        print('Episodes for ({id}) {name} - {permiered}'.format(
                id=show['id'], name=show['name'], permiered=show['permiered']))
        for episode in episodes:
            watched = ''
            if 'watched' in episode:
                watched = episode['watched']
            print('S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate} : {watched}'.format(
                season=episode['season'], episode=episode['number'],
                id=episode['id'], name=episode['name'],
                airdate=episode['airdate'], watched=watched))

    def do_sync(self, line):
        print('Syncing shows...')
        shows = self.db.get_shows()
        for show in shows:
            print('({id}) {name} - {permiered}'.format(
                id=show['id'], name=show['name'], permiered=show['permiered']))
            episodes = self.api.show.episodes(show['id'])
            self.db.sync_episodes(show['id'], episodes);
        print('Done')

    def do_watched(self, episode_id):
        self.db.mark_watched(int(episode_id))

    def do_unwatched(self, line):
        episodes = self.db.get_unwatched()
        for episode in episodes:
            print('S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
                season=episode['season'], episode=episode['number'],
                id=episode['id'], name=episode['name'],
                airdate=episode['airdate']))


if __name__ == '__main__':
    api = Api()
    db = Database('/tmp/temp.json')
    Showtime(api, db).cmdloop()
