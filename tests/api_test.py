from types import SimpleNamespace
from unittest.mock import MagicMock, Mock
import pytest
from helpers import tv_maze_show, tv_maze_episode

from showtime.api import Api


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
