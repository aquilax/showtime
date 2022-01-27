"""Showtime Output  Module"""

import json
from typing import Callable, Dict, List

from terminaltables import AsciiTable as Table # type: ignore

from showtime.types import (DecoratedEpisode, Episode, Show, TVMazeEpisode,
                            TVMazeShow)

PrintFunction = Callable[[str], None]

class Output():
    """Output handler"""

    def __init__(self, print_function: PrintFunction, error_function: PrintFunction,
                 feedback_function: PrintFunction, paged_function: PrintFunction) -> None:
        self.print_function = print_function
        self.error_function = error_function
        self.feedback_function = feedback_function
        self.paged_function = paged_function

    def poutput(self, output: str) -> None:
        """Outputs a string"""
        self.print_function(output)

    def ppaged(self, output: str) -> None:
        """Outputs a string with pagination"""
        self.paged_function(output)

    def json(self, data: List[Episode]) -> None:
        """Outputs json"""
        self.print_function(json.dumps(data, sort_keys=True, indent=4))

    def perror(self, output: str) -> None:
        """Outputs an error message"""
        self.error_function(output)

    def pfeedback(self, output: str) -> None:
        """Outputs a feedback message"""
        self.feedback_function(output)

    def status_on_episode_insert(self, episode: TVMazeEpisode) -> None:
        """Prints status messsage when new episode is added"""
        self.poutput('\tAdding new episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
            season=episode.season, episode=episode.number, id=episode.id,
            name=episode.name, airdate=episode.airdate))

    def status_on_episode_update(self, episode: TVMazeEpisode) -> None:
        """Prints status messsage when an episode is updated"""
        self.poutput('\tUpdating episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
            season=episode.season, episode=episode.number, id=episode.id,
            name=episode.name, airdate=episode.airdate))

    def status_on_show_added(self, show: TVMazeShow) -> None:
        """Prints status when show is added"""
        self.poutput(f"Added show: ({show.id}) {show.name} - {show.premiered}")

    def status_on_show_sync(self, show: Show) -> None:
        """Prints status when show is synced"""
        self.poutput(f"{show['id']}\t{show['name']} ({show['premiered']})")

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
        return Table(data, title='Search Results').table

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

    def completed_shows_table(self, shows: List[Show]) -> str:
        """formats list of completed shows as a table"""
        data = []
        data.append([
            '#',
            'ID',
            'Name',
            'Premiered',
            'Status'
        ])
        i = 0
        for show in shows:
            data.append([
                str(i+1),
                str(show['id']),
                show['name'],
                show['premiered'],
                show['status'],
            ])
            i = i + 1
        title = 'Completed shows'
        table = Table(data, title=title)
        table.justify_columns[0] = 'right'
        table.justify_columns[1] = 'right'
        return str(table.table)

    def summary_table(self, month_totals: Dict[str, Dict[str, int]]) -> str:
        """Formats summary as a table"""
        data = []
        data.append([
            'Month',
            'Episodes',
            'Minutes',
        ])
        for date in sorted(month_totals.keys()):
            data.append([
                date,
                str(month_totals[date]['episodes']),
                str(month_totals[date]['minutes']),
            ])
        title = 'Watchtime per month'
        table = Table(data, title=title)
        table.justify_columns[1] = 'right'
        table.justify_columns[2] = 'right'
        return str(table.table)
