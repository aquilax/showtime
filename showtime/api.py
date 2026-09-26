"""API client module"""

from dataclasses import dataclass
import json
from urllib.parse import urlencode, urlparse, urlunparse
import urllib.request
from typing import Any, Dict, List, Optional

from showtime.types import MovieId, ShowId, TMDBMovie, TVMazeEpisode, TVMazeShow

API_BASE_URL = "https://api.tvmaze.com"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"


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


def movie_to_model(movie: Dict) -> TMDBMovie:
    return TMDBMovie(
        id=movie['id'],
        title=movie['title'],
        release_date=movie.get('release_date') or None,
        runtime=movie.get('runtime'),
        original_language=movie.get('original_language'),
    )


@dataclass
class HTTPResponse:
    data: bytes


class HTTPClient():
    """HTTP Client"""

    def request(self, _method: str, url: str, fields: Optional[dict[str, str]]=None,
                headers: Optional[dict[str, str]]=None) -> Any:
        request_headers = {
            "User-Agent": "showtime-cli",
            "Accept": "application/json"
        }
        if headers:
            request_headers.update(headers)

        url_parts = list(urlparse(url))
        url_parts[4] = urlencode(fields or {})
        final_url = urlunparse(url_parts)
        request = urllib.request.Request(final_url, headers=request_headers)
        with urllib.request.urlopen(request) as response:
            return HTTPResponse(data=response.read())


class Api():
    """API Client"""

    def __init__(self, http: HTTPClient, tmdb_access_token: Optional[str]=None) -> None:
        self.http = http
        self.tmdb_access_token = tmdb_access_token

    def _tmdb_headers(self) -> dict[str, str]:
        if not self.tmdb_access_token:
            raise RuntimeError(
                "TMDB access token is required. Set TMDB_ACCESS_TOKEN or TMDB.AccessToken in your config."
            )
        return {"Authorization": f"Bearer {self.tmdb_access_token}"}

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

    def movie_search(self, query: str) -> List[TMDBMovie]:
        """Returns movies matching the search string"""
        response = self.http.request(
            'GET', f"{TMDB_API_BASE_URL}/search/movie", fields={'query': query, 'include_adult': 'true'}, headers=self._tmdb_headers()
        )
        raw_movies = json.loads(response.data.decode('utf-8'))
        return list(map(movie_to_model, raw_movies['results']))

    def movie_get(self, movie_id: MovieId) -> TMDBMovie:
        """Returns movie information"""
        response = self.http.request(
            'GET', f"{TMDB_API_BASE_URL}/movie/{movie_id}", headers=self._tmdb_headers()
        )
        raw_movie = json.loads(response.data.decode('utf-8'))
        return movie_to_model(raw_movie)

    def movie_external_ids(self, movie_id: MovieId) -> Dict[str, Optional[str]]:
        """Returns all external identifiers for a TMDB movie"""
        response = self.http.request(
            'GET', f"{TMDB_API_BASE_URL}/movie/{movie_id}/external_ids", headers=self._tmdb_headers()
        )
        raw_ids = json.loads(response.data.decode('utf-8'))
        return {key: value for key, value in raw_ids.items() if key != 'id'}

    def movie_find_by_imdb_id(self, imdb_id: str) -> Optional[MovieId]:
        """Returns the TMDB movie ID matching an IMDb identifier"""
        response = self.http.request(
            'GET', f"{TMDB_API_BASE_URL}/find/{imdb_id}",
            fields={'external_source': 'imdb_id'}, headers=self._tmdb_headers()
        )
        result = json.loads(response.data.decode('utf-8'))
        movies = result.get('movie_results', [])
        return MovieId(movies[0]['id']) if movies else None


def get_default_pool_manager():
    return HTTPClient()


