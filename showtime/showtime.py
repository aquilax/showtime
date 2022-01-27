import csv
from datetime import date, datetime
from typing import Callable, Dict, List, Optional, Set, Union, cast

import dateutil.parser
from ratelimit import limits, sleep_and_retry

from showtime.api import Api
from showtime.config import Config
from showtime.database import Database, transaction, NOT_WATCHED_VALUE
from showtime.types import (DecoratedEpisode, Episode, EpisodeId, Show, ShowId,
                            TVMazeEpisode, TVMazeShow)


@sleep_and_retry
@limits(calls=20, period=10)
def _get_episodes(api: Api, show_id: ShowId) -> List[TVMazeEpisode]:
    """Downloads show information from API"""
    return cast(List[TVMazeEpisode], api.episodes_list(show_id))


def needs_update(episode: Episode, tv_maze_episode: TVMazeEpisode):
    return (episode['name'] != tv_maze_episode.name or
        episode['airdate'] != tv_maze_episode.airdate or
        episode['runtime'] != tv_maze_episode.runtime or
        episode['season'] != tv_maze_episode.season or
        episode['number'] != tv_maze_episode.number)


class ShowtimeApp():
    def __init__(self, api: Api, database: Database, config: Config) -> None:
        self.api = api
        self.database = database
        self.config = config

    def _decorate_episodes(self, episodes: List[Episode]) -> List[DecoratedEpisode]:
        """Adds show information to list of episodes"""
        result: List[DecoratedEpisode] = []
        shows = {show['id']: show for show in self.database.get_shows()}
        for episode in episodes:
            show_id = ShowId(episode['show_id'])
            show = shows[show_id]
            show_name = show['name']
            decorated_episode = cast(DecoratedEpisode, episode | {"show_name": show_name})
            result.append(decorated_episode)
        return result

    def show_search(self, query: str) -> List[Show]:
        """Searches shows using the database"""
        shows = self.database.get_shows()
        if query:
            query = query.lower()
            shows = [s for s in shows if query in s['name'].lower()]
        return sorted(shows, key=lambda k: k['name'])

    def _sync_episodes(self, db: Database, show_id: ShowId, tv_maze_episodes: List[TVMazeEpisode],                      on_insert: Optional[Callable[[TVMazeEpisode], None]] = None,
                       on_update: Optional[Callable[[TVMazeEpisode], None]] = None):
        """Synchronizes followed shows data with the upstream api"""
        insert_queue = []
        update_queue = []
        existing_episodes = db.get_episodes(show_id)
        for episode in tv_maze_episodes:
            matched = [x for x in existing_episodes if x['id'] == episode.id]
            if not matched:
                if on_insert:
                    on_insert(episode)
                insert_queue.append({
                    'id': episode.id,
                    'show_id': show_id,
                    'season': episode.season,
                    'number': episode.number,
                    'name': episode.name,
                    'airdate': episode.airdate,
                    'runtime': episode.runtime,
                    'watched': NOT_WATCHED_VALUE
                })
            else:
                matched_episode = matched.pop()
                if needs_update(matched_episode, episode):
                    if on_update:
                        on_update(episode)
                    update_queue.append(({
                        'name': episode.name,
                        'airdate': episode.airdate,
                        'runtime': episode.runtime,
                        'season': episode.season,
                        'number': episode.number,
                    }, matched_episode['id']))
        db.insert_episodes(insert_queue)
        db.update_episodes(update_queue)

    def show_follow(self, show_id: ShowId,
                    on_episode_insert: Union[Callable[[TVMazeEpisode], None], None] = None,
                    on_episode_update: Union[Callable[[TVMazeEpisode], None], None] = None,
                    on_show_added: Union[Callable[[TVMazeShow], None], None] = None) -> Optional[TVMazeShow]:
        """Follows a show (downloads show information and episodes)"""
        # add show to db
        show = self.api.show_get(show_id)
        if show:
            with transaction(self.database) as transacted_db:
                _show_id = transacted_db.add_show(show)
                # add episodes to db
                episodes = _get_episodes(self.api, _show_id)
                self._sync_episodes(transacted_db, _show_id, episodes,
                                    on_insert=on_episode_insert, on_update=on_episode_update)
                if on_show_added:
                    on_show_added(show)
        return show

    def show_get(self, show_id: ShowId) -> Optional[Show]:
        """Returns single show"""
        return self.database.get_show(show_id)

    def show_get_completed(self) -> List[Show]:
        """Returns all shows that have been completed"""
        completed: Set[ShowId] = set()
        partial: Set[ShowId] = set()
        last_watched: Dict[ShowId, str] = {}
        for episode in self.database.get_all_episodes():
            show_id = ShowId(episode['show_id'])
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
        shows = self.database.get_shows_by_ids(list(completed))
        return sorted(shows, key=lambda row: show_order.index(row['id']))

    def episodes_update_all_watched(self, show_id: ShowId, when: datetime):
        """Marks all show episodes as watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched_show(show_id, True, when)

    def episodes_update_all_not_watched(self, show_id: ShowId, when: datetime):
        """Marks all show episodes as not watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched_show(show_id, False, when)

    def episodes_watched_between(self, from_date, to_date: date) -> List[DecoratedEpisode]:
        """Returns all watched episodes between two dates"""
        episodes = self.database.seen_between(from_date, to_date)
        return self._decorate_episodes(episodes)

    def episodes_get(self, show_id: ShowId) -> List[Episode]:
        """Returns all episodes for a show"""
        return self.database.get_episodes(show_id)

    def sync(self,
             on_show_sync: Union[Callable[[Show], None], None] = None,
             on_episode_insert: Union[Callable[[TVMazeEpisode], None], None] = None,
             on_episode_update: Union[Callable[[TVMazeEpisode], None], None] = None):
        """Updates episode information for followed shows from tvmaze"""
        with transaction(self.database) as transacted_db:
            shows = transacted_db.get_active_shows()
            for show in shows:
                show_id = ShowId(show['id'])
                if on_show_sync:
                    on_show_sync(show)
                tv_maze_show = self.api.show_get(show_id)
                if tv_maze_show:
                    transacted_db.update_show(show_id, tv_maze_show)
                    tv_maze_episodes = _get_episodes(self.api, show_id)
                    self._sync_episodes(transacted_db, show_id, tv_maze_episodes,
                                        on_insert=on_episode_insert, on_update=on_episode_update)

    def episodes_patch_watchtime(self, file_name: str) -> None:
        """Patches episodes watch time from external file"""
        with open(file_name, newline='', encoding='UTF-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            with transaction(self.database) as transacted_db:
                for row in reader:
                    episode_id = EpisodeId(row[0])
                    when = dateutil.parser.parse(row[1])
                    transacted_db.update_watched(episode_id, True, when)

    def show_search_api(self, query: str) -> List[TVMazeShow]:
        """Searches tvmaze for showname"""
        return self.api.show_search(query)

    def config_get(self) -> Config:
        """Returns configuration"""
        return self.config

    def episode_update_watched(self, episode_id: EpisodeId, when: datetime) -> int:
        """Marks episode as watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched(episode_id, True, when)

    def episode_update_not_watched(self, episode_id: EpisodeId, when: datetime) -> int:
        """Marks episode as not watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched(episode_id, False, when)

    def episode_get_next_unwatched(self, show_id: ShowId) -> Optional[Episode]:
        """Returns the next episode from a show that has not been watched"""
        episodes = self.database.get_episodes(show_id)
        if episodes:
            for episode in episodes:
                if episode['watched'] == '':
                    return episode
        return None

    def episodes_update_season_watched(self, show_id: ShowId, season: int, when: datetime) -> int:
        """Marks all episodes from a season as watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched_show_season(ShowId(show_id), int(season), True, when)

    def episodes_update_season_not_watched(self, show_id: ShowId, season: int, when: datetime) -> int:
        """Marks all episodes from a season as non watched"""
        with transaction(self.database) as transacted_db:
            return transacted_db.update_watched_show_season(show_id, season, False, when)

    def episodes_get_unwatched(self, when: datetime) -> List[DecoratedEpisode]:
        """Returns list of unwatched episodes"""
        episodes = self.database.get_unwatched(when)
        sorted_episodes = sorted(episodes, key=lambda episode: episode['airdate'] or '')
        return self._decorate_episodes(sorted_episodes)

    def episodes_watched_to_last_seen(self, show_id: ShowId, season: int, episode_number: int, when: datetime) -> int:
        """Marks all episodes of a show until season/episode as watched"""
        with transaction(self.database) as transacted_db:
            episodes = transacted_db.get_episodes(show_id)
            episode_ids = []
            for episode in episodes:
                if episode['season'] > season:
                    continue
                if episode['season'] < season or (episode['season'] == season and episode['number'] <= episode_number):
                    episode_ids.append(episode['id'])
                    continue
            return transacted_db.update_watched_episodes(episode_ids, True, when)

    def episode_get(self, episode_id: EpisodeId) -> Optional[Episode]:
        """Returns episode"""
        return self.database.get_episode(episode_id)

    def episode_delete(self, episode_id: EpisodeId) -> None:
        """Deletes an episode"""
        return self.database.delete_episode(episode_id)

    def episodes_aired_unseen_between(self, from_date, to_date: date) -> List[DecoratedEpisode]:
        """Returns aired but not watched episodes between dates"""
        episodes = self.database.aired_unseen_between(from_date, to_date)
        return self._decorate_episodes(episodes)

    def episodes_get_watched(self) -> List[Episode]:
        """Returns all watched episodes"""
        return self.database.get_watched_episodes()
