"""Commands tests"""
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import cmd2_ext_test
from cmd2 import CommandResult
from showtime.command import Showtime
import pytest

from showtime.showtime import ShowtimeApp


class ShowtimeTester(cmd2_ext_test.ExternalTestMixin, Showtime):
    def __init__(self, *args, **kwargs):
        # gotta have this or neither the plugin or cmd2 will initialize
        super().__init__(*args, **kwargs)


tv_maze_show = SimpleNamespace(
    id=1,
    name="test-show",
    premiered="2020-01-01",
    status="Ended",
    url="https:/www.example.com/1"
)

show = {
    "id": 1,
    "name": "test-show",
    "premiered": "2020-01-01",
    "status": "Ended",
}

episode = {
    "id": 1,
    "show_id": "1",
    "season": 1,
    "number": 1,
    "name": "The first episode",
    "airdate": "2020-01-01",
    "runtime": 60,
    "watched": "",
}


@pytest.fixture
def test_app():
    api = Mock()
    database = Mock()

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
