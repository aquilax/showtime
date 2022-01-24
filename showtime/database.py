"""Showtime Database Module"""

from contextlib import contextmanager
import csv
from datetime import date, datetime
from typing import Callable, Dict, Generator, List, Literal, Optional, Set, Union, cast

import dateutil.parser
from tinydb import TinyDB, where
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage, MemoryStorage

from showtime.types import (Episode, EpisodeId, Show, ShowId,
                            ShowStatus, TVMazeEpisode, TVMazeShow)

SHOW = 'show'
EPISODE = 'episode'


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
            'watched': ''
        })
        return EpisodeId(episode.id)

    def get_shows(self) -> List[Show]:
        """Returns list of all added shows"""
        return cast(List[Show], self.table(SHOW).all())

    def get_active_shows(self) -> List[Show]:
        """Gets list of shows which have not ended"""
        return cast(List[Show], self.table(SHOW).search(where('status') != ShowStatus.ENDED.value))

    def get_show(self, show_id: ShowId) -> Union[Show, None]:
        """Returns single show"""
        return cast(Union[Show, None], self.table(SHOW).get(where('id') == show_id))

    def get_episode(self, episode_id: EpisodeId) -> Optional[Episode]:
        """Returns single episode"""
        return cast(Union[Episode, None], self.table(EPISODE).get(where('id') == episode_id))

    def get_episodes(self, show_id: ShowId) -> List[Episode]:
        """Returns sorted list of episodes for a show"""
        episodes = cast(List[Episode], self.table(EPISODE).search(where('show_id') == show_id))
        return sorted(episodes, key=lambda ep: ep['season'] * 1000 + ep['number'])

    def delete_episode(self, episode_id: EpisodeId) -> None:
        """Deletes an episode from the database"""
        self.table(EPISODE).remove(where('id') == episode_id)
        return None

    def sync_episodes(self, show_id: ShowId, episodes: List[TVMazeEpisode],
                      on_insert: Union[Callable[[TVMazeEpisode], None], None] = None,
                      on_update: Union[Callable[[TVMazeEpisode], None], None] = None) -> None:
        """Updates episodes from API results"""
        existing_episodes = self.get_episodes(show_id)
        queue = []
        for episode in episodes:
            matched = [x for x in existing_episodes if x['id'] == episode.id]
            if not matched:
                if on_insert:
                    on_insert(episode)
                queue.append({
                    'id': episode.id,
                    'show_id': show_id,
                    'season': episode.season,
                    'number': episode.number,
                    'name': episode.name,
                    'airdate': episode.airdate,
                    'runtime': episode.runtime,
                    'watched': ''
                })
            else:
                matched_episode = matched.pop()
                if (
                    matched_episode['name'] != episode.name or
                    matched_episode['airdate'] != episode.airdate or
                    matched_episode['runtime'] != episode.runtime or
                    matched_episode['season'] != episode.season or
                    matched_episode['number'] != episode.number
                ):
                    if on_update:
                        on_update(episode)
                    self.table(EPISODE).update({
                        'name': episode.name,
                        'airdate': episode.airdate,
                        'runtime': episode.runtime,
                        'season': episode.season,
                        'number': episode.number,
                    }, where('id') == matched_episode['id'])
        self.table(EPISODE).insert_multiple(queue)

    def update_watched(self, episode_id: EpisodeId, watched: bool, when: Optional[datetime] = None) -> None:
        """Updates the watched date of an episode"""
        watched_date = when if when else datetime.utcnow().isoformat()
        watched_value = watched_date if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, where('id') == episode_id)

    def get_unwatched(self, current_datetime: datetime) -> List[Episode]:
        """Returns all aired episodes which are not watched yet"""
        episodes = self.table(EPISODE).search(((where('watched') == '') & (where('airdate') <= current_datetime.isoformat())))
        return cast(List[Episode], episodes)

    def update_watched_show(self, show_id: ShowId, watched: bool, when:Optional[datetime] = None) -> None:
        """Updates all episodes of a show as watched now"""
        watched_date = when if when else datetime.utcnow().isoformat()
        watched_value = watched_date if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, where('show_id') == show_id)

    def update_watched_show_season(self, show_id: ShowId, season: int, watched: bool,
                                   when:Optional[datetime] = None) -> None:
        """Updates all episodes of a show and season as watched now"""
        watched_date = when if when else datetime.utcnow().isoformat()
        watched_value = watched_date if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, ((where('show_id') == show_id) & (where('season') == season)))

    def last_seen(self, show_id: ShowId, season: int, number: int, when:Optional[datetime] = None) -> int:
        """Updates all show episodes as seen up to season and number"""
        watched_date = when if when else datetime.utcnow().isoformat()
        episodes = self.get_episodes(show_id)
        episode_ids = []
        for episode in episodes:
            if episode['season'] > season:
                continue
            if episode['season'] < season or (episode['season'] == season and episode['number'] <= number):
                episode_ids.append(episode['id'])
                continue
        self.table(EPISODE).update({
            'watched': watched_date
        }, where('id').one_of(episode_ids))
        return len(episode_ids)

    def seen_between(self, from_date: date, to_date: date) -> List[Episode]:
        """Returns list of episodes that were watched between two dates"""
        def is_between(in_date):
            return _test_between(in_date, from_date, to_date)
        episodes = self.table(EPISODE).search(where('watched').test(is_between))
        return cast(List[Episode], episodes)

    def aired_unseen_between(self, from_date: date, to_date: date) -> List[Episode]:
        """Returns list of episodes that were aired but have not been seen between two dates"""
        def is_between(in_date):
            return _test_between(in_date, from_date, to_date)
        episodes = self.table(EPISODE).search((where('airdate').test(is_between)) & (where('watched') == ''))
        return cast(List[Episode], episodes)

    def update_watch_times(self, patch_file_name: str) -> None:
        """Updates watch times from a patch file"""
        with open(patch_file_name, newline='', encoding='UTF-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                self.table(EPISODE).update({
                    'watched': row[1]
                }, where('id') == int(row[0]))
        self.close()

    def get_watched_episodes(self) -> List[Episode]:
        """Returns all episodes that have not been watched"""
        episodes = self.table(EPISODE).search(where('watched') != '')
        return cast(List[Episode], episodes)

    def get_completed_shows(self) -> List[Show]:
        """Returns all shows that have been completed"""
        completed: Set[ShowId] = set()
        partial: Set[ShowId] = set()
        last_watched: Dict[ShowId, str] = {}
        for episode in self.table(EPISODE):
            show_id = episode['show_id']
            if show_id in partial:
                continue
            if episode['watched'] == '':
                partial.add(show_id)
                if show_id in completed:
                    completed.remove(show_id)
                continue
            if (not show_id in last_watched) or (last_watched[show_id] < episode['watched']):
                last_watched[show_id] = episode['watched']

            completed.add(show_id)
        last_watched_list = sorted(last_watched.items(), key=lambda t: t[1])
        show_order = [t[0] for t in last_watched_list]
        shows = cast(List[Show], self.table(SHOW).search(where('id').one_of(list(completed))))
        return sorted(shows, key=lambda row: show_order.index(row['id']))


def get_direct_write_db(file_name: str) -> Database:
    """Returns database instance with direct interface"""
    return Database(file_name, sort_keys=True, indent=4)


def get_cashed_write_db(file_name: str) -> Database:
    """Returns database instance with cached interface"""
    return Database(file_name, storage=CachingMiddleware(JSONStorage), sort_keys=True, indent=4)


def get_memory_db() -> Database:
    """Returns in-memory database instance"""
    return Database(storage=MemoryStorage)


GetDatabase = Callable[[str], Database]
ConnectionType = Literal["direct", "cached", "memory"]

@contextmanager
def transaction(database: Database) -> Generator[Database, None, None]:
    try:
        yield database
    finally:
        database.flush()
