import pytest
from collections import namedtuple
from showtime.database import getMemoryDB, ShowStatus

Show = namedtuple('Show', ['id', 'name', 'premiered', 'status'])


def test_add():
    show = Show(id=1, name="show", premiered="2020", status="great")
    with getMemoryDB() as db:
        addId = db.add(show)

    assert addId == 1


def test_get_shows():
    show = Show(id=1, name="show", premiered="2020", status="great")
    with getMemoryDB() as db:
        db.add(show)
        shows = db.get_shows()

    assert len(shows) == 1


def test_get_active_shows():
    show1 = Show(id=1, name="show 1", premiered="2020", status="great")
    show2 = Show(id=2, name="show 2", premiered="2020",
                 status=ShowStatus.ENDED.value)
    with getMemoryDB() as db:
        db.add(show1)
        db.add(show2)
        active = db.get_active_shows()

    assert len(active) == 1
    assert active[0]['name'] == "show 1"
