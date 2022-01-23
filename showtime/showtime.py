from datetime import date, datetime
from typing import Callable, List, Optional, Union, cast

from ratelimit import limits, sleep_and_retry

from showtime.api import Api
from showtime.config import Config
from showtime.database import ConnectionType, GetDatabase
from showtime.types import (DecoratedEpisode, Episode, EpisodeId, Show, ShowId,
                            TVMazeEpisode, TVMazeShow)


@sleep_and_retry
@limits(calls=20, period=10)
def _get_episodes(api: Api, show_id: ShowId) -> List[TVMazeEpisode]:
    """Downloads show information from API"""
    return cast(List[TVMazeEpisode], api.episodes_list(show_id))


class ShowtimeApp():
    def __init__(self, api: Api, get_database: Callable[[ConnectionType], GetDatabase], config: Config) -> None:
        self.api = api
        self.get_database = get_database
        self.database_filename = config.get('Database', 'Path')
        self.get_cached_database = get_database("cached")
        self.get_direct_database = get_database("direct")
        self.database = self.get_direct_database(self.database_filename)
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

    def show_follow(self, show_id: ShowId,
                    on_episode_insert: Union[Callable[[TVMazeEpisode], None], None] = None,
                    on_episode_update: Union[Callable[[TVMazeEpisode], None], None] = None,
                    on_show_added: Union[Callable[[TVMazeShow], None], None] = None) -> Optional[TVMazeShow]:
        """Follows a show (downloads show information and episodes)"""
        # add show to db
        show = self.api.show_get(show_id)
        if show:
            _show_id = self.database.add(show)
            # add episodes to db
            episodes = _get_episodes(self.api, _show_id)
            self.database.sync_episodes(_show_id, episodes, on_insert=on_episode_insert, on_update=on_episode_update)
            if on_show_added:
                on_show_added(show)
        return show

    def show_get(self, show_id: ShowId) -> Optional[Show]:
        """Returns single show"""
        return self.database.get_show(show_id)

    def show_get_completed(self) -> List[Show]:
        """Returns list of completed shows"""
        return self.database.get_completed_shows()

    def episodes_update_all_watched(self, show_id: ShowId):
        """Marks all show episodes as watched"""
        return self.database.update_watched_show(show_id, True)

    def episodes_update_all_not_watched(self, show_id: ShowId):
        """Marks all show episodes as not watched"""
        return self.database.update_watched_show(show_id, False)

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
        ## still hacky but better
        self.database.close()
        with self.get_cached_database(self.database_filename) as cached_db:
            shows = cached_db.get_active_shows()
            for show in shows:
                if on_show_sync:
                    on_show_sync(show)
                episodes = _get_episodes(self.api, show['id'])
                cached_db.sync_episodes(show['id'], episodes, on_insert=on_episode_insert, on_update=on_episode_update)
        ## Create new direct since there is no open method
        self.database = self.get_direct_database(self.database_filename)

    def episodes_patch_watchtime(self, file_name: str) -> None:
        """Patches episodes watch time from external file"""
        ## still hacky but better
        self.database.close()
        with self.get_cached_database(self.database_filename) as cached_db:
            cached_db.update_watch_times(file_name)
        ## Create new direct since there is no open method
        self.database = self.get_direct_database(self.database_filename)

    def show_search_api(self, query: str) -> List[TVMazeShow]:
        """Searches tvmaze for showname"""
        return self.api.show_search(query)

    def config_get(self) -> Config:
        """Returns configuration"""
        return self.config

    def episode_update_watched(self, episode_id: EpisodeId) -> None:
        """Marks episode as watched"""
        return self.database.update_watched(episode_id, True)

    def episode_update_not_watched(self, episode_id: EpisodeId) -> None:
        """Marks episode as not watched"""
        return self.database.update_watched(episode_id, False)

    def episode_get_next_unwatched(self, show_id: ShowId) -> Optional[Episode]:
        """Returns the next episode from a show that has not been watched"""
        episodes = self.database.get_episodes(show_id)
        if episodes:
            for episode in episodes:
                if episode['watched'] == '':
                    return episode
        return None

    def episodes_update_season_watched(self, show_id: ShowId, season: int) -> None:
        """Marks all episodes from a season as watched"""
        return self.database.update_watched_show_season(ShowId(show_id), int(season), True)

    def episodes_update_season_not_watched(self, show_id: ShowId, season: int) -> None:
        """Marks all episodes from a season as non watched"""
        return self.database.update_watched_show_season(show_id, season, False)

    def episodes_get_unwatched(self, current_datetime=datetime.utcnow().isoformat()) -> List[DecoratedEpisode]:
        """Returns list of unwatched episodes"""
        episodes = self.database.get_unwatched(current_datetime)
        sorted_episodes = sorted(episodes, key=lambda episode: episode['airdate'] or '')
        return self._decorate_episodes(sorted_episodes)

    def episodes_watched_to_last_seen(self, show_id:ShowId, season: int, episode: int) -> int:
        """Marks all episodes of a show until season/episode as watched"""
        return self.database.last_seen(show_id, season, episode)

    def episode_get(self, episode_id: EpisodeId) -> Optional[Episode]:
        """Returns episode"""
        return self.database.get_episode(episode_id)

    def episode_delete(self, episode_id: EpisodeId) -> None:
        """Deletes an episode"""
        return self.database.delete_episode(episode_id)

    def episodes_aired_unseen_between(self, from_date, to_date: date) -> List[DecoratedEpisode]:
        episodes =  self.database.aired_unseen_between(from_date, to_date)
        return self._decorate_episodes(episodes)


    def episodes_get_watched(self) -> List[Episode]:
        return self.database.get_watched_episodes()
