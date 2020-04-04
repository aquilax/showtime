import pytest
from collections import namedtuple
from showtime.database import getMemoryDB
from showtime.types import ShowStatus, TVMazeShow

def get_tv_maze_show(id=1, name="show", premiered="2020", status="great", url="http://example.com") -> TVMazeShow:
    return TVMazeShow(id=id, name=name, premiered=premiered, status=status, url=url)

def test_add():
    show = get_tv_maze_show()
    with getMemoryDB() as db:
        addId = db.add(show)

    assert addId == 1


def test_get_shows():
    show = get_tv_maze_show()
    with getMemoryDB() as db:
        db.add(show)
        shows = db.get_shows()

    assert len(shows) == 1


def test_get_active_shows():
    show1 = get_tv_maze_show(name="show 1")
    show2 = get_tv_maze_show(id=2, name="show 2", status=ShowStatus.ENDED.value)
    with getMemoryDB() as db:
        db.add(show1)
        db.add(show2)
        active = db.get_active_shows()

    assert len(active) == 1
    assert active[0]['name'] == "show 1"
