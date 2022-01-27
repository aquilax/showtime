"""Showtime Database Module Tests"""

from datetime import datetime
from showtime.database import get_memory_db, transaction
from showtime.types import ShowStatus, TVMazeShow, TVMazeEpisode


def get_tv_maze_show(id=1, name="show", premiered="2020", status="great", url="http://example.com") -> TVMazeShow:
    return TVMazeShow(id=id, name=name, premiered=premiered, status=status, url=url)


def get_tv_maze_episode(id=1, season=1, number=1, name="episode1", airdate="2020-10-10", runtime=30) -> TVMazeEpisode:
    return TVMazeEpisode(id=id, season=season, number=number, name=name, airdate=airdate, runtime=runtime)


def test_add():
    show = get_tv_maze_show()
    with get_memory_db() as database:
        with transaction(database) as transacted_db:
            add_id = transacted_db.add_show(show)

    assert add_id == 1


def test_get_shows():
    show = get_tv_maze_show()
    with get_memory_db() as database:
        with transaction(database) as transacted_db:
            transacted_db.add_show(show)
        shows = database.get_shows()

    assert len(shows) == 1


def test_get_active_shows():
    show1 = get_tv_maze_show(name="show 1")
    show2 = get_tv_maze_show(id=2, name="show 2", status=ShowStatus.ENDED.value)
    with get_memory_db() as database:
        with transaction(database) as transacted_db:
            transacted_db.add_show(show1)
            transacted_db.add_show(show2)
        active = database.get_active_shows()

    assert len(active) == 1
    assert active[0]['name'] == "show 1"


def test_watch():
    show1 = get_tv_maze_show(name="show 1")
    episode1 = get_tv_maze_episode(id=1, name="episode1", number=1)
    episode2 = get_tv_maze_episode(id=2, name="episode2", number=2)
    with get_memory_db() as database:
        with transaction(database) as transacted_db:
            show_id = database.add_show(show1)
            transacted_db.add_episode(show_id, episode1)
            transacted_db.add_episode(show_id, episode2)
        with transaction(database) as transacted_db:
            transacted_db.update_watched(1, True, datetime(2020, 1, 1, 1, 0))
        episode1db = database.get_episode(1)
        with transaction(database) as transacted_db:
            transacted_db.update_watched(2, True, datetime(2020, 1, 1, 1, 1))
        episode2db = database.get_episode(2)
    assert episode1db['watched'] != episode2db['watched']
