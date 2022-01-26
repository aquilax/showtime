"""API client module"""

from typing import List, Optional

from tvmaze.api import Api as TVMazeApi # type: ignore

from showtime.types import ShowId, TVMazeEpisode, TVMazeShow


class Api():
    """API Client"""

    def __init__(self, api: TVMazeApi) -> None:
        self.api = api

    def episodes_list(self, show_id: ShowId) -> TVMazeEpisode:
        """returns list of episodes for a show"""
        return self.api.show.episodes(show_id)

    def show_get(self, show_id: ShowId) -> Optional[TVMazeShow]:
        """returns show information"""
        return self.api.show.get(show_id)

    def show_search(self, query: str) -> List[TVMazeShow]:
        """returns list of shows matching search string"""
        return self.api.search.shows(query)
