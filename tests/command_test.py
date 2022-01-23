"""Commands tests"""
from datetime import date
from unittest.mock import MagicMock, Mock

import cmd2_ext_test
import pytest
from cmd2 import CommandResult
from helpers import decorated_episode, episode, show, tv_maze_show

from showtime.command import Showtime
from showtime.showtime import ShowtimeApp


class ShowtimeTester(cmd2_ext_test.ExternalTestMixin, Showtime):
    def __init__(self, *args, **kwargs):
        # gotta have this or neither the plugin or cmd2 will initialize
        super().__init__(*args, **kwargs)

@pytest.fixture
def test_app():
    api = Mock()
    database = Mock()
    config = Mock()

    attrs = {'get.return_value': None}
    config = Mock(**attrs)

    showtime = ShowtimeApp(api, database, config)
    showtime.config_get = MagicMock(return_value=config)

    app = ShowtimeTester(showtime)

    config.get.assert_called_with('History', 'Path')

    app.fixture_setup()
    yield app
    app.fixture_teardown()


def test_config(test_app):
    """tests config command"""
    out = test_app.app_cmd("config")

    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == 'Database path: None'
    assert out.data is None


def test_search(test_app):
    """tests search command"""
    test_app.app.show_search_api = MagicMock(return_value=[tv_maze_show])

    out = test_app.app_cmd("search show name")

    test_app.app.show_search_api.assert_called_with('show name')
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+Search Results--+------------+-----------+--------------------------+
| ID | Name      | Premiered  | StatusURL |                          |
+----+-----------+------------+-----------+--------------------------+
| 1  | test-show | 2020-01-01 | Ended     | https:/www.example.com/1 |
+----+-----------+------------+-----------+--------------------------+
""".strip()
    assert out.data == None


def test_episodes(test_app):
    """tests episodes command"""
    test_app.app.show_get = MagicMock(return_value=show)
    test_app.app.episodes_get = MagicMock(return_value=[episode])

    out = test_app.app_cmd("episodes 1")

    test_app.app.show_get.assert_called_with(1)
    test_app.app.episodes_get.assert_called_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+(1) test-show - 2020-01-01----------+------------+---------+
| ID | S   | E   | Name              | Aired      | Watched |
+----+-----+-----+-------------------+------------+---------+
| 1  | S01 | E01 | The first episode | 2020-01-01 |         |
+----+-----+-----+-------------------+------------+---------+
""".strip()
    assert out.data == None

def test_set_show(test_app):
    test_app.app.show_get = MagicMock(return_value=show)

    out = test_app.app_cmd("set_show 1")

    test_app.app.show_get.assert_called_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_unset_show(test_app):
    out = test_app.app_cmd("unset_show")

    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_completed(test_app):
    test_app.app.show_get_completed = MagicMock(return_value=[show])

    out = test_app.app_cmd("completed")

    test_app.app.show_get_completed.assert_called_with()
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+Completed shows-+------------+--------+
| ID | Name      | Premiered  | Status |
+----+-----------+------------+--------+
| 1  | test-show | 2020-01-01 | Ended  |
+----+-----------+------------+--------+
""".strip()
    assert out.data == None

def test_sync(test_app):
    test_app.app.sync = MagicMock()
    out = test_app.app_cmd("sync")

    test_app.app.sync.assert_called_once()
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_watch(test_app):
    test_app.app.episode_update_watched = MagicMock()
    out = test_app.app_cmd("watch 1,2")

    test_app.app.episode_update_watched.assert_called_with(2)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_next(test_app):
    test_app.app.show_get = MagicMock(return_value=show)
    test_app.app.episode_get_next_unwatched = MagicMock(return_value=episode)

    out = test_app.app_cmd("next 1")

    test_app.app.show_get.assert_called_once_with(1)
    test_app.app.episode_get_next_unwatched.assert_called_once_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+(1) test-show - 2020-01-01----------+------------+---------+
| ID | S   | E   | Name              | Aired      | Watched |
+----+-----+-----+-------------------+------------+---------+
| 1  | S01 | E01 | The first episode | 2020-01-01 |         |
+----+-----+-----+-------------------+------------+---------+
Did you watch this episode [Y/n]:
""".strip()
    assert out.data == None

def test_delete(test_app):
    test_app.app.episode_get = MagicMock(return_value=episode)
    test_app.app.show_get = MagicMock(return_value=show)

    out = test_app.app_cmd("delete_episode 1")

    test_app.app.episode_get.assert_called_with(1)
    test_app.app.show_get.assert_called_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+(1) test-show - 2020-01-01----------+------------+---------+
| ID | S   | E   | Name              | Aired      | Watched |
+----+-----+-----+-------------------+------------+---------+
| 1  | S01 | E01 | The first episode | 2020-01-01 |         |
+----+-----+-----+-------------------+------------+---------+
Do you want to delete this episode [y/N]:
""".strip()
    assert out.data == None

def test_unwatch(test_app):
    test_app.app.episode_update_not_watched = MagicMock()

    out = test_app.app_cmd("unwatch 1")

    test_app.app.episode_update_not_watched.assert_called_once_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_watch_all(test_app):
    test_app.app.episodes_update_all_watched = MagicMock()

    out = test_app.app_cmd("watch_all 1")

    test_app.app.episodes_update_all_watched.assert_called_once_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_unwatch_all(test_app):
    test_app.app.episodes_update_all_not_watched = MagicMock()

    out = test_app.app_cmd("unwatch_all 1")

    test_app.app.episodes_update_all_not_watched.assert_called_once_with(1)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_watch_all_season(test_app):
    test_app.app.episodes_update_season_watched = MagicMock()

    out = test_app.app_cmd("watch_all_season 1 2")

    test_app.app.episodes_update_season_watched.assert_called_once_with(1, 2)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_unwatch_all_season(test_app):
    test_app.app.episodes_update_season_not_watched = MagicMock()

    out = test_app.app_cmd("unwatch_all_season 1 2")

    test_app.app.episodes_update_season_not_watched.assert_called_once_with(1, 2)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_unwatched(test_app):
    test_app.app.episodes_get_unwatched = MagicMock(return_value=[decorated_episode])

    out = test_app.app_cmd("unwatched")

    test_app.app.episodes_get_unwatched.assert_called_once()
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+Episodes to watch-----+-----+-------------------+------------+---------+
| ID | Show      | S   | E   | Name              | Aired      | Watched |
+----+-----------+-----+-----+-------------------+------------+---------+
| 1  | test-show | S01 | E01 | The first episode | 2020-01-01 |         |
+----+-----------+-----+-----+-------------------+------------+---------+
""".strip()
    assert out.data == None

def test_last_seen(test_app):
    test_app.app.episodes_watched_to_last_seen = MagicMock(return_value=4)

    out = test_app.app_cmd("last_seen 1 2 3")

    test_app.app.episodes_watched_to_last_seen.assert_called_once_with(1, 2, 3)
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """4 episodes marked as seen""".strip()
    assert out.data == None

def test_export(test_app):
    test_app.app.episodes_watched_between = MagicMock(return_value=[decorated_episode])

    out = test_app.app_cmd("export 2020-01-01 2021-01-01")

    test_app.app.episodes_watched_between.assert_called_once_with(date(2020, 1, 1), date(2021, 1, 1))
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
[
    {
        "airdate": "2020-01-01",
        "id": 1,
        "name": "The first episode",
        "number": 1,
        "runtime": 60,
        "season": 1,
        "show_id": "1",
        "show_name": "test-show",
        "watched": ""
    }
]
""".strip()
    assert out.data == None

def test_new_unwatched(test_app):
    test_app.app.episodes_aired_unseen_between = MagicMock(return_value=[decorated_episode])

    out = test_app.app_cmd("new_unwatched 4 2020-01-01")

    test_app.app.episodes_aired_unseen_between.assert_called_once_with(date(2019, 12, 29), date(2020, 1, 1))
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
+Episodes to watch-----+-----+-------------------+------------+---------+
| ID | Show      | S   | E   | Name              | Aired      | Watched |
+----+-----------+-----+-----+-------------------+------------+---------+
| 1  | test-show | S01 | E01 | The first episode | 2020-01-01 |         |
+----+-----------+-----+-----+-------------------+------------+---------+
""".strip()
    assert out.data == None

def test_patch_watchtime(test_app):
    test_app.app.episodes_patch_watchtime = MagicMock()

    out = test_app.app_cmd("patch_watchtime /tmp/patch.csv")

    test_app.app.episodes_patch_watchtime.assert_called_once_with("/tmp/patch.csv")
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """""".strip()
    assert out.data == None

def test_watching_stats(test_app):
    test_app.app.episodes_get_watched = MagicMock(return_value=[episode | {'watched': '2020-01-01'}])

    out = test_app.app_cmd("watching_stats")

    test_app.app.episodes_get_watched.assert_called_once()
    assert isinstance(out, CommandResult)
    assert str(out.stdout).strip() == """
Total watched episodes: 1
Total watchtime in minutes: 60
+Watchtime per month-+---------+
| Month   | Episodes | Minutes |
+---------+----------+---------+
| 2020-01 |        1 |      60 |
+---------+----------+---------+
""".strip()
    assert out.data == None
