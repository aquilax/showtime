from unittest.mock import MagicMock, Mock
import pytest
from helpers import tv_maze_show, tv_maze_episode

from showtime.api import Api


@pytest.fixture
def test_api() -> Api:
    tv_maze_api = Mock()
    tv_maze_api.show = Mock()
    tv_maze_api.search = Mock()
    api = Api(tv_maze_api)
    return api


def test_episodes_list(test_api):
    test_api.api.show.episodes = MagicMock(return_value=[tv_maze_episode])

    result = test_api.episodes_list(1)

    test_api.api.show.episodes.assert_called_once_with(1)
    assert result == [tv_maze_episode]


def test_show_get(test_api):
    test_api.api.show.get = MagicMock(return_value=tv_maze_show)

    result = test_api.show_get(1)

    test_api.api.show.get.assert_called_once_with(1)
    assert result == tv_maze_show


def test_show_search(test_api):
    test_api.api.search.shows = MagicMock(return_value=[tv_maze_show])

    result = test_api.show_search("name")

    test_api.api.search.shows.assert_called_once_with("name")
    assert result == [tv_maze_show]
