"""Showtime Database Module"""

from contextlib import contextmanager
from datetime import date, datetime
from typing import (Iterable, Iterator, Tuple, Callable, Dict, Generator, List, Literal, Optional, Set,
                    cast)

import dateutil.parser
from tinydb import TinyDB, where
from tinydb.middlewares import CachingMiddleware
from tinydb.queries import QueryLike
from tinydb.storages import JSONStorage, MemoryStorage

from showtime.types import (Episode, EpisodeId, Show, ShowId, ShowStatus,
                            TVMazeEpisode, TVMazeShow)

SHOW = 'show'
EPISODE = 'episode'

NOT_WATCHED_VALUE = ''


def _test_between(in_date: str, from_date: date, to_date: date) -> bool:
    """Returns true if date is between from_date and to_date"""
    return from_date <= dateutil.parser.parse(in_date).date() <= to_date if in_date else False


class Database(TinyDB):
    """Class for locally storing the showtime data"""

    def flush(self):
        if hasattr(self.storage, 'flush'):
            self.storage.flush()

    def add_show(self, tv_maze_show: TVMazeShow) -> ShowId:
        """Adds a show if it is not already added"""
        if not self.table(SHOW).contains(where('id') == tv_maze_show.id):
            self.table(SHOW).insert({
                'id': tv_maze_show.id,
                'name': tv_maze_show.name,
                'premiered': tv_maze_show.premiered,
                'status': tv_maze_show.status
            })
        return ShowId(tv_maze_show.id)

    def update_show(self, show_id, tv_maze_show: TVMazeShow) -> None:
        """Updates show information"""
        self.table(SHOW).update({
            'name': tv_maze_show.name,
            'premiered': tv_maze_show.premiered,
            'status': tv_maze_show.status
        }, where('id') == show_id)

    def add_episode(self, show_id: ShowId, episode: TVMazeEpisode) -> EpisodeId:
        """Helper method used in tests"""
        self.table(EPISODE).insert({
            'id': episode.id,
            'show_id': show_id,
            'season': episode.season,
            'number': episode.number,
            'name': episode.name,
            'airdate': episode.airdate,
            'runtime': episode.runtime,
            'watched': NOT_WATCHED_VALUE
        })
        return EpisodeId(episode.id)

    def get_shows(self) -> List[Show]:
        """Returns list of all added shows"""
        return cast(List[Show], self.table(SHOW).all())

    def get_active_shows(self) -> List[Show]:
        """Gets list of shows which have not ended"""
        return cast(List[Show], self.table(SHOW).search(where('status') != ShowStatus.ENDED.value))

    def get_show(self, show_id: ShowId) -> Optional[Show]:
        """Returns single show"""
        return cast(Optional[Show], self.table(SHOW).get(where('id') == show_id))

    def get_episode(self, episode_id: EpisodeId) -> Optional[Episode]:
        """Returns single episode"""
        return cast(Optional[Episode], self.table(EPISODE).get(where('id') == episode_id))

    def delete_episode(self, episode_id: EpisodeId) -> None:
        """Deletes an episode from the database"""
        self.table(EPISODE).remove(where('id') == episode_id)

    def insert_episodes(self, episodes: List[Dict]) -> List[int]:
        """Inserts list of episodes"""
        return self.table(EPISODE).insert_multiple(episodes)

    def update_episodes(self, episodes: List[Tuple[Dict, int]]) -> List[int]:
        """Updates list of episodes"""
        updates = list(map(lambda el: (el[0], where('id') == el[1]), episodes))
        return self.table(EPISODE).update_multiple(updates)

    def _update_watched(self, watched: bool, when: datetime, query: QueryLike) -> List[int]:
        watched_value = when.isoformat() if watched else NOT_WATCHED_VALUE
        return self.table(EPISODE).update({'watched': watched_value}, query)

    def update_watched(self, episode_id: EpisodeId, watched: bool, when: datetime) -> int:
        """Updates the watched date of an episode"""
        updated = self._update_watched(watched, when, where('id') == episode_id)
        return len(updated)

    def update_watched_episodes(self, episode_ids: List[EpisodeId], watched: bool, when: datetime) -> int:
        """Updates the watched date of an episode"""
        updated = self._update_watched(watched, when, where('id').one_of(episode_ids))
        return len(updated)

    def update_watched_show(self, show_id: ShowId, watched: bool, when: datetime) -> int:
        """Updates all episodes of a show as watched now"""
        updated = self._update_watched(watched, when, where('show_id') == show_id)
        return len(updated)

    def update_watched_show_season(self, show_id: ShowId, season: int, watched: bool, when: datetime) -> int:
        """Updates all episodes of a show and season as watched now"""
        updated = self._update_watched(watched, when, (where('show_id') == show_id) & (where('season') == season))
        return len(updated)

    def _search_episodes(self, query: QueryLike) -> List[Episode]:
        episodes = self.table(EPISODE).search(query)
        return cast(List[Episode], episodes)

    def get_episodes(self, show_id: ShowId) -> List[Episode]:
        """Returns sorted list of episodes for a show"""
        episodes = self._search_episodes(where('show_id') == show_id)
        return sorted(episodes, key=lambda ep: ep['season'] * 1000 + ep['number'])

    def get_unwatched(self, when: datetime) -> List[Episode]:
        """Returns all aired episodes which are not watched yet"""
        return self._search_episodes((where('watched') == '') & (where('airdate') <= when.isoformat()))

    def seen_between(self, from_date: date, to_date: date) -> List[Episode]:
        """Returns list of episodes that were watched between two dates"""
        def is_between(in_date):
            return _test_between(in_date, from_date, to_date)
        return self._search_episodes(where('watched').test(is_between))

    def aired_unseen_between(self, from_date: date, to_date: date) -> List[Episode]:
        """Returns list of episodes that were aired but have not been seen between two dates"""
        def is_between(in_date):
            return _test_between(in_date, from_date, to_date)
        return self._search_episodes(where('airdate').test(is_between)) & (where('watched') == '')

    def get_watched_episodes(self) -> List[Episode]:
        """Returns all episodes that have not been watched"""
        return self._search_episodes(where('watched') != NOT_WATCHED_VALUE)

    def get_all_episodes(self) -> Iterator[Episode]:
        """Returns all episodes iterator"""
        return cast(Iterator[Episode], self.table(EPISODE))

    def get_shows_by_ids(self, show_ids: List[ShowId]) -> List[Show]:
        """Returns list of shows given list of show id-s"""
        shows = self.table(SHOW).search(where('id').one_of(show_ids))
        return cast(List[Show], shows)


def get_direct_write_db(file_name: str) -> Database:
    """Returns database instance with direct interface"""
    return Database(file_name, sort_keys=True, indent=4)


def get_cashed_write_db(file_name: str) -> Database:
    """Returns database instance with cached interface"""
    return Database(file_name, storage=CachingMiddleware(JSONStorage), sort_keys=True, indent=4)


def get_memory_db() -> Database:
    """Returns in-memory database instance"""
    return Database(storage=MemoryStorage)


@contextmanager
def transaction(database: Database) -> Generator[Database, None, None]:
    """Returns database and flushes the data on exit"""
    try:
        yield database
    finally:
        database.flush()
