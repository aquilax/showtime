from typing import List, Optional

from tvmaze.api import Api as TVMazeApi # type: ignore

from showtime.types import ShowId, TVMazeEpisode, TVMazeShow


class Api():
    def __init__(self, api: TVMazeApi) -> None:
        self.api = api

    def episodes_list(self, show_id: ShowId) -> TVMazeEpisode:
        return self.api.show.episodes(show_id)

    def show_get(self, show_id: ShowId) -> Optional[TVMazeShow]:
        return self.api.show.get(show_id)

    def show_search(self, query: str) -> List[TVMazeShow]:
        return self.api.search.shows(query)
