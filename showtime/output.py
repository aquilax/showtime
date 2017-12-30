import json
from terminaltables import SingleTable as Table


class Output():

    def __init__(self, print_function, error_function, feedback_function):
        self.print_function = print_function
        self.error_function = error_function
        self.feedback_function = feedback_function

    def poutput(self, str):
        self.print_function(str)

    def json(self, data):
        self.print_function(json.dumps(data, sort_keys=True, indent=4))

    def perror(self, str):
        self.error_function(str)

    def pfeedback(self, str):
        self.feedback_function(str)

    def format_search_results(self, search_result):
        data = []
        data.append([
            'ID',
            'Name',
            'Premiered',
            'Status'
            'URL'
        ])
        for show in search_result:
            data.append([
                show.id,
                show.name,
                show.premiered,
                show.status,
                show.url
            ])
        return Table(data, title='Search Results').table

    def format_episodes(self, show, episodes):
        title = '({id}) {name} - {premiered}'.format(
                id=show['id'], name=show['name'], premiered=show['premiered'])
        data = self.get_episodes_data(episodes)
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
        data = []
        data.append([
            'ID',
            'Show'
            'S',
            'E',
            'Name',
            'Aired',
            'Watched'
        ])
        for episode in episodes:
            data.append([
                episode['id'],
                episode['show_name'],
                'S{season:0>2}'.format(season=episode['season']),
                'E{episode:0>2}'.format(episode=episode['number']),
                episode['name'],
                episode['airdate'],
                episode['watched']
            ])
        title = 'Episodes to watch'
        return Table(data, title=title).table

    def shows_table(self, shows):
        data = []
        data.append([
            'ID',
            'Name',
            'Premiered',
            'Status'
        ])
        for show in shows:
            data.append([
                show['id'],
                show['name'],
                show['premiered'],
                show['status'],
            ])
        title = 'Followed shows'
        return Table(data, title=title).table
