"""Showtime Output  Module"""

import json
from typing import Callable, Dict, List, Optional

from terminaltables import AsciiTable as Table  # type: ignore

from showtime.types import (DecoratedEpisode, Episode, Movie, Show, TMDBMovie, TVMazeEpisode,
                            TVMazeShow, ShowWithCount)

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
        """Prints status message when new episode is added"""
        self.poutput(
            f"\tAdding new episode: S{episode.season:0>2} E{episode.number:0>2} ({episode.id}) {episode.name} - {episode.airdate}")

    def status_on_episode_update(self, episode: TVMazeEpisode) -> None:
        """Prints status message when an episode is updated"""
        self.poutput(
            f"\tUpdating episode: S{episode.season:0>2} E{episode.number:0>2} ({episode.id}) {episode.name} - {episode.airdate}")

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
        title = self.table_title('Search Results', len(search_result))
        return str(Table(data, title=title).table)

    def format_movie_search_results(self, search_result: List[TMDBMovie]) -> str:
        """Formats TMDB movie search results as a table"""
        data = [['ID', 'Title', 'Released', 'Language', 'Runtime']]
        for movie in search_result:
            data.append([
                str(movie.id),
                movie.title,
                movie.release_date or '',
                movie.original_language or '',
                str(movie.runtime) if movie.runtime is not None else '',
            ])
        title = self.table_title('Movie Search Results', len(search_result))
        return str(Table(data, title=title).table)

    def movies_table(self, movies: List[Movie], title: str = 'Tracked Movies') -> str:
        """Formats tracked movies as a table"""
        data = [['ID', 'Title', 'Released', 'Language', 'Runtime', 'Watched']]
        for movie in movies:
            data.append([
                str(movie['id']),
                movie['title'],
                movie['release_date'] or '',
                movie.get('original_language') or '',
                str(movie['runtime']) if movie['runtime'] is not None else '',
                movie['watched'],
            ])
        title = self.table_title(title, len(movies))
        return str(Table(data, title=title).table)

    def movies_json(self, movies: List[Movie]) -> str:
        """Formats movies as json"""
        return json.dumps(movies, sort_keys=True, indent=4)

    def format_episodes(self, show: Show, episodes: List[Episode]) -> str:
        """Formats as table list of episodes"""
        title = f"({show['id']}) {show['name']} - {show['premiered']}"
        title = self.table_title(title, len(episodes))
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
            'Runtime',
            'Aired',
            'Watched'
        ])
        for episode in episodes:
            data.append([
                str(episode['id']),
                f"S{episode['season']:0>2}",
                f"E{episode['number']:0>2}",
                episode['name'],
                str(episode['runtime']),
                episode['airdate'],
                episode['watched']
            ])
        return data

    def format_unwatched(self, episodes: List[DecoratedEpisode], title: str = 'Episodes to watch') -> str:
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
                f"S{episode['season']:0>2}",
                f"E{episode['number']:0>2}",
                episode['name'],
                episode['airdate'],
                episode['watched']
            ])
        title = self.table_title(title, len(episodes))
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
        title = self.table_title('Followed shows', len(shows))
        return str(Table(data, title=title).table)

    def unfinished_shows_table(self, shows: List[ShowWithCount]) -> str:
        """formats list of shows with episodes count as a table"""
        data = []
        data.append([
            'ID',
            'Name',
            'Premiered',
            'Status',
            'Episodes',
            'Watched',
            'Unwatched',
        ])
        for show in shows:
            data.append([
                str(show['id']),
                show['name'],
                show['premiered'],
                show['status'],
                str(show['total']),
                str(show['seen']),
                str(show['total']-show['seen'])
            ])
        title = self.table_title('Unfinished shows', len(shows))
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
        title = self.table_title('Completed shows', len(shows))
        table = Table(data, title=title)
        table.justify_columns[0] = 'right'
        table.justify_columns[1] = 'right'
        return str(table.table)

    def summary_table(self, period_totals: Dict[str, Dict[str, int]], period: str = 'month') -> str:
        """Formats summary as a table"""
        data = []
        data.append([
            period.capitalize(),
            'Shows',
            'Episodes',
            'Movies',
            'Minutes',
        ])
        for date in sorted(period_totals.keys()):
            data.append([
                date,
                str(period_totals[date]['shows']),
                str(period_totals[date]['episodes']),
                str(period_totals[date]['movies']),
                str(period_totals[date]['minutes']),
            ])
        title = f'Watchtime per {period}'
        title = self.table_title(title, len(data) - 1)
        table = Table(data, title=title)
        table.justify_columns[1] = 'right'
        table.justify_columns[2] = 'right'
        table.justify_columns[3] = 'right'
        table.justify_columns[4] = 'right'
        return str(table.table)

    def episodes_json(self, episodes: List[DecoratedEpisode]) -> str:
        """Formats decorated episodes as json"""
        return json.dumps(episodes, sort_keys=True, indent=4)


    def table_title(self, base_title: str, count: Optional[int] = None) -> str:
        """
        Generates a padded table title, optionally appending the item count.

        :param base_title: The main text for the title.
        :param count: Optional number of elements to display.
        :return: A formatted string safe for terminaltables.
        """
        if count is not None:
            title_text = f"{base_title} ({count})"
        else:
            title_text = base_title
        
        return f" {title_text.strip()} "
