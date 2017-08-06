from terminaltables import SingleTable as Table

class Output():

    def __init__(self, print_function):
        self.print_function = print_function

    def poutput(self, str):
        self.print_function(str)

    def format_search_results(self, search_result):
        data = []
        data.append([
            'ID',
            'Name',
            'Premiered',
            'URL'
        ])
        for show in search_result:
            data.append([
                show.id,
                show.name,
                show.premiered,
                show.url
            ])
        return Table(data, title='Search Results').table

    def format_episodes(self, show, episodes):
        title = '({id}) {name} - {permiered}'.format(
                id=show['id'], name=show['name'], permiered=show['permiered'])
        data =self.get_episodes_data(episodes)
        return Table(data, title=title).table

    def get_episodes_data(self, episodes):
        data = []
        data.append([
            'ID',
            'S',
            'E',
            'Name',
            'Aired',
            'Watched'
        ])
        for episode in episodes:
            data.append([
                episode['id'],
                'S{season:0>2}'.format(season=episode['season']),
                'E{episode:0>2}'.format(episode=episode['number']),
                episode['name'],
                episode['airdate'],
                episode['watched']
            ])
        return data

    def format_unwatched(self, episodes):
        title = 'Episodes to watch'
        data =self.get_episodes_data(episodes)
        return Table(data, title=title).table
