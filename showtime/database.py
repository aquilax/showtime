"""Showtime Database"""

import csv
import dateutil.parser

from datetime import datetime, date
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware
from showtime.types import EpisodeId, ShowId, Episode, Show, DecoratedEpisode, TVMazeShow, TVMazeEpisode, ShowStatus
from typing import cast, List, Union, Callable, TypeVar

SHOW = 'show'
EPISODE = 'episode'

def _test_between(date: str, from_date: date, to_date: date)-> bool:
    """Returns true if date is between from_date and to_date"""
    return from_date <= dateutil.parser.parse(date).date() <= to_date if date else False

class Database(TinyDB):
    """Class for locally storing the showtime data"""

    def add(self, show: TVMazeShow) -> ShowId:
        """Adds a show if it is not already added"""
        ShowQ = Query()
        if not self.table(SHOW).contains(ShowQ.id == show.id):
            self.table(SHOW).insert({
                'id': show.id,
                'name': show.name,
                'premiered': show.premiered,
                'status': show.status
            })
        return ShowId(show.id)

    def get_shows(self) -> List[Show]:
        """Returns list of all addded shows"""
        return cast(List[Show], self.table(SHOW).all())

    def get_active_shows(self)-> List[Show]:
        """Gets list of shows which have not ended"""
        ShowQ = Query()
        return cast(List[Show], self.table(SHOW).search(ShowQ.status != ShowStatus.ENDED.value))

    def get_show(self, show_id: ShowId) -> Union[Show, None]:
        """Returns single show"""
        ShowQ = Query()
        return cast(Union[Show, None], self.table(SHOW).get(ShowQ.id == show_id))

    def get_episode(self, episode_id: EpisodeId) -> Union[Episode, None]:
        """Returns single episode"""
        EpisodeQ = Query()
        return cast(Union[Episode, None], self.table(EPISODE).get(EpisodeQ.id == episode_id))

    def get_episodes(self, show_id: ShowId)-> List[Episode]:
        """Returns sorted list of episodes for a show"""
        EpisodeQ = Query()
        episodes = self.table(EPISODE).search(EpisodeQ.show_id == show_id)
        return cast(List[Episode], sorted(episodes, key=lambda ep: ep['season'] * 1000 + ep['number']))

    def delete_episode(self, episode_id: EpisodeId) -> List[int]:
        """Deletes an episode from the database"""
        EpisodeQ = Query()
        return cast(List[int], self.table(EPISODE).remove(EpisodeQ.id == episode_id))

    def sync_episodes(self, show_id: ShowId, episodes: List[TVMazeEpisode], on_insert: Union[Callable[[TVMazeEpisode], None], None]=None, on_update: Union[Callable[[TVMazeEpisode], None], None]=None) -> None:
        """Updates episodes fro API reuslts"""
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
                    EpisodeQ = Query()
                    self.table(EPISODE).update({
                        'name': episode.name,
                        'airdate': episode.airdate,
                        'runtime': episode.runtime,
                        'season': episode.season,
                        'number': episode.number,
                    }, EpisodeQ.id == matched_episode['id'])
        self.table(EPISODE).insert_multiple(queue)

    def update_watched(self, episode_id: EpisodeId, watched: bool) -> None:
        """Updates the watched date of an episode"""
        EpisodeQ = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, EpisodeQ.id == episode_id)

    def get_unwatched(self) -> List[DecoratedEpisode]:
        """Returns all aired episodes which are not watched yet"""
        EpisodeQ = Query()
        return self.decorate_episodes(
            sorted(self.table(EPISODE).search(((EpisodeQ.watched == '') & (EpisodeQ.airdate <= datetime.utcnow().isoformat()))), key=lambda episode: episode['airdate'] or ''))

    def update_watched_show(self, show_id: ShowId, watched: bool) -> None:
        """Updates all episodes of a show as watched now"""
        EpisodeQ = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, EpisodeQ.show_id == show_id)

    def update_watched_show_season(self, show_id: ShowId, season: int, watched: bool) -> None:
        """Updates all episodes of a show and season as watched now"""
        EpisodeQ = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.table(EPISODE).update({
            'watched': watched_value
        }, ((EpisodeQ.show_id == show_id) & (EpisodeQ.season == season)))

    def last_seen(self, show_id: ShowId, season: int, number: int) -> int:
        """Updates all show episodes as seen up to season and number"""
        episodes = self.get_episodes(show_id)
        eids = []
        for episode in episodes:
            if episode['season'] > season:
                continue
            if episode['season'] < season or (episode['season'] == season and episode['number'] < number):
                eids.append(episode['id'])
                continue
        watched_value = datetime.utcnow().isoformat()
        self.table(EPISODE).update({
            'watched': watched_value
        }, eids=eids)
        return len(eids)

    def get_next_unwatched(self, show_id: ShowId)-> Union[Episode, None]:
        """Returns the first episode from a show that has not been watched"""
        episodes = self.get_episodes(show_id)
        if episodes:
            for episode in episodes:
                if episode['watched'] == '':
                    return episode
        return None

    def seen_between(self, from_date: date, to_date: date) -> List[Episode]:
        """Returns list of episodes that were watched between two dates"""
        EpisodeQ = Query()
        episodes = self.table(EPISODE).search(
            EpisodeQ.watched.test(_test_between, from_date, to_date))
        return cast(List[Episode], episodes)

    def aired_unseen_between(self, from_date: date, to_date: date) -> List[DecoratedEpisode]:
        """Returns list of episodes that were aired but have not been seen between two dates"""
        EpisodeQ = Query()
        episodes = self.table(EPISODE).search(
            (EpisodeQ.airdate.test(_test_between, from_date, to_date)) &
            (EpisodeQ.watched == ''))
        return self.decorate_episodes(episodes)

    def decorate_episodes(self, episodes: List[Episode]) -> List[DecoratedEpisode]:
        """Adds show information to list of episodes"""
        result: List[DecoratedEpisode] = []
        shows = {show['id']: show for show in self.get_shows()}
        for episode in episodes:
            decorated_episode = cast(DecoratedEpisode, episode)
            show = shows[episode['show_id']]
            decorated_episode['show_name'] = show['name']
            result.append(decorated_episode)
        return result

    def update_watch_times(self, patch_file_name: str)-> None:
        """Updates watch times from a patch file"""
        EpisodeQ = Query()
        with open(patch_file_name, newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                self.table(EPISODE).update({
                    'watched': row[1]
                }, EpisodeQ.id == int(row[0]))
        self.close()

    def get_watched_episodes(self) -> List[Episode]:
        """Returns all episodes that have not been watched"""
        EpisodeQ = Query()
        return cast(List[Episode], self.table(EPISODE).search(EpisodeQ.watched != ''))


def getDirectWriteDB(file_name: str) -> Database:
    """Returns database instance with direct interface"""
    return Database(file_name, sort_keys=True, indent=4)


def getCashedWriteDB(file_name: str) -> Database:
    """Returns database instance with cached interface"""
    return Database(file_name, storage=CachingMiddleware(JSONStorage), sort_keys=True, indent=4)


def getMemoryDB() -> Database:
    """Returns in-memory database instance"""
    return Database(storage=MemoryStorage)
