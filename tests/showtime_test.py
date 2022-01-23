from datetime import date
from unittest.mock import MagicMock, Mock

import pytest
from helpers import decorated_episode, episode, show, show2, tv_maze_show

from showtime.showtime import ShowtimeApp


@pytest.fixture
def test_app() -> ShowtimeApp:
    api = Mock()
    database = Mock()
    config = Mock()
    showtime = ShowtimeApp(api, database, config)
    return showtime


def test_show_search(test_app):
    test_app.database.get_shows = MagicMock(return_value=[show, show2])

    result = test_app.show_search("test-show")

    assert result == [show]


def test_show_get(test_app):
    test_app.database.get_show = MagicMock(return_value=show)

    result = test_app.show_get(1)

    assert result == show


def test_show_get_not_found(test_app):
    test_app.database.get_show = MagicMock(return_value=None)

    result = test_app.show_get(1)

    assert result is None


def test_show_get_completed(test_app):
    test_app.database.get_completed_shows = MagicMock(return_value=[show, show2])

    result = test_app.show_get_completed()

    assert result == [show, show2]


def test_episodes_update_all_watched(test_app):
    test_app.database.update_watched_show = MagicMock(return_value=None)

    result = test_app.episodes_update_all_watched(1)

    assert result is None
    test_app.database.update_watched_show.assert_called_once_with(1, True)


def test_episodes_update_all_not_watched(test_app):
    test_app.database.update_watched_show = MagicMock(return_value=None)

    result = test_app.episodes_update_all_not_watched(1)

    test_app.database.update_watched_show.assert_called_once_with(1, False)
    assert result is None


def test_episodes_watched_between(test_app):
    test_app.database.seen_between = MagicMock(return_value=[episode])
    test_app.database.get_shows = MagicMock(return_value=[show, show2])

    result = test_app.episodes_watched_between(date(2020, 1, 1), date(2021, 1, 1))

    test_app.database.seen_between.assert_called_once_with(date(2020, 1, 1), date(2021, 1, 1))
    test_app.database.get_shows.assert_called_once()
    assert result == [decorated_episode]


def test_episodes_get(test_app):
    test_app.database.get_episodes = MagicMock(return_value=[episode])

    result = test_app.episodes_get(1)

    test_app.database.get_episodes.assert_called_once_with(1)
    assert result == [episode]


def test_show_search_api(test_app):
    test_app.api.show_search = MagicMock(return_value=[tv_maze_show])

    result = test_app.show_search_api("test")

    test_app.api.show_search.assert_called_once_with("test")
    assert result == [tv_maze_show]


def test_config_get(test_app):
    result = test_app.config.get()
    assert result is not None


def test_episode_update_watched(test_app):
    test_app.database.update_watched = MagicMock(return_value=None)

    result = test_app.episode_update_watched(1)

    test_app.database.update_watched.assert_called_once_with(1, True)
    assert result is None


def test_episode_update_not_watched(test_app):
    test_app.database.update_watched = MagicMock(return_value=None)

    result = test_app.episode_update_not_watched(1)

    test_app.database.update_watched.assert_called_once_with(1, False)
    assert result is None


def test_episode_get_next_unwatched(test_app):
    watched = episode | {'watched': '2020-01-01'}
    unwatched = episode | {'watched': ''}
    test_app.database.get_episodes = MagicMock(return_value=[watched, unwatched])

    result = test_app.episode_get_next_unwatched(1)

    test_app.database.get_episodes.assert_called_once_with(1)
    assert result == unwatched


def test_episodes_update_season_watched(test_app):
    test_app.database.update_watched_show_season = MagicMock(return_value=None)

    result = test_app.episodes_update_season_watched(1, 1)

    test_app.database.update_watched_show_season.assert_called_once_with(1, 1, True)
    assert result is None


def test_episodes_update_season_not_watched(test_app):
    test_app.database.update_watched_show_season = MagicMock(return_value=None)

    result = test_app.episodes_update_season_not_watched(1, 1)

    test_app.database.update_watched_show_season.assert_called_once_with(1, 1, False)
    assert result is None


def test_episodes_get_unwatched(test_app):
    test_app.database.get_unwatched = MagicMock(return_value=[episode])
    test_app.database.get_shows = MagicMock(return_value=[show, show2])

    result = test_app.episodes_get_unwatched()

    test_app.database.get_unwatched.assert_called_once()
    test_app.database.get_shows.assert_called_once()
    assert result == [decorated_episode]


def test_episodes_watched_to_last_seen(test_app):
    test_app.database.last_seen = MagicMock(return_value=None)

    result = test_app.episodes_watched_to_last_seen(1, 2, 3)

    test_app.database.last_seen.assert_called_once_with(1, 2, 3)
    assert result is None


def test_episode_get(test_app):
    test_app.database.get_episode = MagicMock(return_value=episode)

    result = test_app.episode_get(1)

    test_app.database.get_episode.assert_called_once_with(1)
    assert result == episode


def test_episode_delete(test_app):
    test_app.database.delete_episode = MagicMock(return_value=None)

    result = test_app.episode_delete(1)

    test_app.database.delete_episode.assert_called_once_with(1)
    assert result is None


def test_episodes_aired_unseen_between(test_app):
    test_app.database.aired_unseen_between = MagicMock(return_value=[episode])
    test_app.database.get_shows = MagicMock(return_value=[show, show2])

    result = test_app.episodes_aired_unseen_between(date(2020, 1, 1), date(2021, 1, 1))

    test_app.database.get_shows.assert_called_once()
    test_app.database.aired_unseen_between.assert_called_once_with(date(2020, 1, 1), date(2021, 1, 1))
    assert result == [decorated_episode]


def test_episodes_get_watched(test_app):
    test_app.database.get_watched_episodes = MagicMock(return_value=[episode])

    result = test_app.episodes_get_watched()

    test_app.database.get_watched_episodes.assert_called_once()
    assert result == [episode]


def test_sync(test_app):
    result = test_app.episodes_get_watched()


def test_episodes_patch_watchtime(test_app):
    pass


def test_show_follow(test_app):
    pass
