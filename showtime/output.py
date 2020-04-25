import json
from typing import List, Dict, Callable
from terminaltables import AsciiTable as Table
from showtime.types import TVMazeEpisode, TVMazeShow, Episode, DecoratedEpisode, Show

PrintFunction = Callable[[str], None]

class Output():
    """Output handler"""

    def __init__(self, print_function: PrintFunction, error_function: PrintFunction, feedback_function: PrintFunction) -> None:
        self.print_function = print_function
        self.error_function = error_function
        self.feedback_function = feedback_function

    def poutput(self, str: str) -> None:
        """Outputs a string"""
        self.print_function(str)

    def json(self, data: List[Episode]) -> None:
        """Outputs json"""
        self.print_function(json.dumps(data, sort_keys=True, indent=4))

    def perror(self, str: str) -> None:
        """Outputs an error message"""
        self.error_function(str)

    def pfeedback(self, str: str) -> None:
        """Outputs a feedback message"""
        self.feedback_function(str)

    def status_on_insert(self, episode: TVMazeEpisode) -> None:
        """Prints status messsage when new episode is added"""
        self.poutput('\tAdding new episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
            season=episode.season, episode=episode.number, id=episode.id,
            name=episode.name, airdate=episode.airdate))

    def status_on_update(self, episode: TVMazeEpisode) -> None:
        """Prints status messsage when an episode is updated"""
        self.poutput('\tUpdating episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
            season=episode.season, episode=episode.number, id=episode.id,
            name=episode.name, airdate=episode.airdate))

    def format_search_results(self, search_result: List[TVMazeShow]) -> str:
        """Formats as table API search results"""
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
                str(show.id),
                show.name,
                show.premiered,
                show.status,
                show.url
            ])
        return str(Table(data, title='Search Results').table)

    def format_episodes(self, show: Show, episodes: List[Episode]) -> str:
        """Formats as table list of episodes"""
        title = '({id}) {name} - {premiered}'.format(
                id=show['id'], name=show['name'], premiered=show['premiered'])
        data = self._get_episodes_data(episodes)
        return str(Table(data, title=title).table)

    def _get_episodes_data(self, episodes: List[Episode]) -> List[List[str]]:
        """Formats episodes as table list"""
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
                str(episode['id']),
                'S{season:0>2}'.format(season=episode['season']),
                'E{episode:0>2}'.format(episode=episode['number']),
                episode['name'],
                episode['airdate'],
                episode['watched']
            ])
        return data

    def format_unwatched(self, episodes: List[DecoratedEpisode]) -> str:
        """Formats unwatched episodes as table"""
        data = []
        data.append([
            'ID',
            'Show',
            'S',
            'E',
            'Name',
            'Aired',
            'Watched'
        ])
        for episode in episodes:
            data.append([
                str(episode['id']),
                episode['show_name'],
                'S{season:0>2}'.format(season=episode['season']),
                'E{episode:0>2}'.format(episode=episode['number']),
                episode['name'],
                episode['airdate'],
                episode['watched']
            ])
        title = 'Episodes to watch'
        return str(Table(data, title=title).table)

    def shows_table(self, shows: List[Show]) -> str:
        """formats list of shows as a table"""
        data = []
        data.append([
            'ID',
            'Name',
            'Premiered',
            'Status'
        ])
        for show in shows:
            data.append([
                str(show['id']),
                show['name'],
                show['premiered'],
                show['status'],
            ])
        title = 'Followed shows'
        return str(Table(data, title=title).table)

    def summary_table(self, month_totals: Dict[str, int]) -> str:
        """Formats summary as a table"""
        data = []
        data.append([
            'Month',
            'Episodes',
        ])
        for date in sorted(month_totals.keys()):
            data.append([
                date,
                str(month_totals[date])
            ])
        title = 'Episodes per month'
        table = Table(data, title=title)
        table.justify_columns[1] = 'right'
        return str(table.table)
