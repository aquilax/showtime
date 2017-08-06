from cmd2 import Cmd
from tvmaze.api import Api

class Database():

    def add(self, show):
        print(show)


class Showtime(Cmd):

    def __init__(self, api, db):
        Cmd.__init__(self)
        self.api = api
        self.db = db

    def do_search(self, query):
        search_result = api.search.shows(query)
        for show in search_result:
            print('({id}) {name} - {permiere}'.format(
                id=show.id, name=show.name, permiere=show.premiered))

    def do_add(self, show_id):
        show = api.show.get(show_id)
        self.db.add(show)

    def do_episodes(self, show_id):
        episodes = api.show.episodes(show_id)
        for episode in episodes:
            print('S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
                season=episode.season, episode=episode.number, id=episode.id,
                name=episode.name, airdate=episode.airdate))

if __name__ == '__main__':
    api = Api()
    db = Database()
    Showtime(api, db).cmdloop()
