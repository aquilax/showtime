from types import SimpleNamespace
from unittest.mock import MagicMock, Mock
import pytest
from helpers import tv_maze_show, tv_maze_episode

from showtime.api import Api
from showtime.types import TMDBMovie


def get_response(data: str):
    return SimpleNamespace(data=data.encode('utf-8'))


@pytest.fixture
def test_api() -> Api:
    http = Mock()
    api = Api(http)
    return api


def test_episodes_list(test_api):
    response = get_response("""
[
    {
        "id": 1,
        "show_id": 1,
        "season": 1,
        "number": 1,
        "name": "The first episode",
        "airdate": "2020-01-01",
        "runtime": 60,
        "watched": ""
    }
]
""")
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.episodes_list(1)

    test_api.http.request.assert_called_once_with('GET', 'https://api.tvmaze.com/shows/1/episodes')
    assert result == [tv_maze_episode]


def test_show_get(test_api):
    response = get_response("""
{
    "id":1,
    "name": "test-show",
    "premiered": "2020-01-01",
    "status": "Ended",
    "url": "https:/www.example.com/1",
    "externals":{"tmdb": "111"}
}
""")
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.show_get(1)

    test_api.http.request.assert_called_once_with('GET', 'https://api.tvmaze.com/shows/1')
    assert result == tv_maze_show


def test_show_search(test_api):
    response = get_response("""
[
    {
        "score": 0.000,
        "show": {
            "id":1,
            "name": "test-show",
            "premiered": "2020-01-01",
            "status": "Ended",
            "url": "https:/www.example.com/1",
            "externals":{"tmdb": "111"}
        }
    }
]
""")
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.show_search("name")

    test_api.http.request.assert_called_once_with('GET', 'https://api.tvmaze.com/search/shows', fields={'q': 'name'})
    assert result == [tv_maze_show]


def test_movie_search(test_api):
    test_api.tmdb_access_token = 'test-token'
    response = get_response('''
{
    "results": [
        {"id": 42, "title": "Test Movie", "release_date": "2020-01-01"}
    ]
}
''')
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.movie_search('test')

    test_api.http.request.assert_called_once_with(
        'GET', 'https://api.themoviedb.org/3/search/movie', fields={'query': 'test'},
        headers={'Authorization': 'Bearer test-token'}
    )
    assert result == [TMDBMovie(42, 'Test Movie', '2020-01-01', None)]


def test_movie_get(test_api):
    test_api.tmdb_access_token = 'test-token'
    response = get_response('''
{"id": 42, "title": "Test Movie", "release_date": "2020-01-01", "runtime": 120}
''')
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.movie_get(42)

    test_api.http.request.assert_called_once_with(
        'GET', 'https://api.themoviedb.org/3/movie/42', headers={'Authorization': 'Bearer test-token'}
    )
    assert result == TMDBMovie(42, 'Test Movie', '2020-01-01', 120)


def test_movie_external_ids(test_api):
    test_api.tmdb_access_token = 'test-token'
    response = get_response('''
{"id": 42, "imdb_id": "tt1234567", "wikidata_id": "Q123", "facebook_id": null}
''')
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.movie_external_ids(42)

    test_api.http.request.assert_called_once_with(
        'GET', 'https://api.themoviedb.org/3/movie/42/external_ids',
        headers={'Authorization': 'Bearer test-token'}
    )
    assert result == {'imdb_id': 'tt1234567', 'wikidata_id': 'Q123', 'facebook_id': None}


def test_movie_find_by_imdb_id(test_api):
    test_api.tmdb_access_token = 'test-token'
    response = get_response('''
{"movie_results": [{"id": 42, "title": "Test Movie"}], "tv_results": []}
''')
    test_api.http.request = MagicMock(return_value=response)

    result = test_api.movie_find_by_imdb_id('tt1234567')

    test_api.http.request.assert_called_once_with(
        'GET', 'https://api.themoviedb.org/3/find/tt1234567',
        fields={'external_source': 'imdb_id'}, headers={'Authorization': 'Bearer test-token'}
    )
    assert result == 42


def test_movie_find_by_imdb_id_not_found(test_api):
    test_api.tmdb_access_token = 'test-token'
    test_api.http.request = MagicMock(return_value=get_response('{"movie_results": []}'))

    assert test_api.movie_find_by_imdb_id('tt1234567') is None


def test_movie_search_requires_token(test_api):
    with pytest.raises(RuntimeError, match='TMDB access token is required'):
        test_api.movie_search('test')
