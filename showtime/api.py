"""API client module"""

from dataclasses import dataclass
import json
from urllib.parse import urlencode, urlparse, urlunparse
import urllib.request
from typing import Any, Dict, List, Optional

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
        url=show['url'],
        externals=show['externals']
    )


def search_to_model(show_wrapped) -> TVMazeShow:
    return show_to_model(show_wrapped['show'])


@dataclass
class HTTPResponse:
    data: str


class HTTPClient():
    """HTTP Client"""

    def request(self, _method: str, url: str, fields: dict[str, str]={}) -> Any:
        headers = {
            "User-Agent": "showtime-cli",
            "Accept": "application/json"
        }

        url_parts = list(urlparse(url))
        url_parts[4] = urlencode(fields)
        final_url = urlunparse(url_parts)
        print(final_url)
        request = urllib.request.Request(final_url, headers=headers)
        with urllib.request.urlopen(request) as response:
            return HTTPResponse(data=response.read())


class Api():
    """API Client"""

    def __init__(self, http: HTTPClient) -> None:
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
        return list(map(search_to_model, raw_shows))


def get_default_pool_manager():
    return HTTPClient()


