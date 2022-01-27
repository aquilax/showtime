"""API client module"""

import urllib3
import json
from typing import Dict, List, Optional

from showtime.types import ShowId, TVMazeEpisode, TVMazeShow

API_BASE_URL = "https://api.tvmaze.com"


def episode_to_model(episode: Dict) -> TVMazeEpisode:
    return TVMazeEpisode(
        id=episode['id'],
        season=episode['season'],
        number=episode['number'],
        name=episode['name'],
        airdate=episode['airdate'],
        runtime=episode['runtime'],
    )

def show_to_model(show: Dict) -> TVMazeShow:
    return TVMazeShow(
        id=show['id'],
        name=show['name'],
        premiered=show['premiered'],
        status=show['status'],
        url=show['url']
    )


class Api():
    """API Client"""

    def __init__(self, http: urllib3.PoolManager) -> None:
        self.http = http

    def episodes_list(self, show_id: ShowId) -> List[TVMazeEpisode]:
        """returns list of episodes for a show"""
        response = self.http.request('GET', f"{API_BASE_URL}/shows/{show_id}/episodes")
        raw_episodes = json.loads(response.data.decode('utf-8'))
        return list(map(episode_to_model, raw_episodes))

    def show_get(self, show_id: ShowId) -> Optional[TVMazeShow]:
        """returns show information"""
        response = self.http.request('GET', f"{API_BASE_URL}/shows/{show_id}")
        raw_show = json.loads(response.data.decode('utf-8'))
        return show_to_model(raw_show)

    def show_search(self, query: str) -> List[TVMazeShow]:
        """returns list of shows matching search string"""
        response = self.http.request('GET', f"{API_BASE_URL}/search/shows", fields={'q': query})
        raw_shows = json.loads(response.data.decode('utf-8'))
        return list(map(show_to_model, raw_shows))


def get_default_pool_manager():
    return urllib3.PoolManager(maxsize=1, block=True, headers={'user-agent': 'showtime-cli'})
