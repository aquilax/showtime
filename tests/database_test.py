"""Showtime Database Module Tests"""

from datetime import datetime

import pytest
from showtime.database import Database, get_memory_db, transaction
from showtime.types import ShowStatus, TVMazeShow, TVMazeEpisode

from helpers import decorated_episode, episode, show, tv_maze_show, tv_maze_episode


def get_tv_maze_show(id=1, name="show", premiered="2020", status="great", url="http://example.com", externals={"tmdb": "111"}) -> TVMazeShow:
    return TVMazeShow(id=id, name=name, premiered=premiered, status=status, url=url, externals=externals)


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


@pytest.fixture
def test_database() -> Database:
    return get_memory_db()


def test_flush(test_database):
    result = test_database.flush()
    assert result is None


def test_add_show(test_database):
    result = test_database.add_show(tv_maze_show)
    assert result == 1


def test_update_show(test_database):
    result = test_database.update_show(1, tv_maze_show)
    assert result == []


def test_add_episode(test_database):
    result = test_database.add_episode(1, tv_maze_episode)
    assert result == 1


def test_get_shows(test_database):
    result = test_database.get_shows()
    assert result == []


def test_get_active_shows(test_database):
    result = test_database.get_active_shows()
    assert result == []


def test_get_show(test_database):
    result = test_database.get_show(1)
    assert result is None


def test_get_episode(test_database):
    result = test_database.get_episode(1)
    assert result is None


def test_delete_episode(test_database):
    result = test_database.delete_episode(1)
    assert result == []


def test_insert_episodes(test_database):
    result = test_database.insert_episodes([episode])
    assert result == [1]


def test_update_episodes(test_database):
    result = test_database.update_episodes([(episode, 1)])
    assert result == []


def test_update_watched(test_database):
    result = test_database.update_watched(1, True, datetime(2021, 1, 1, 1))
    assert result == []


def test_update_watched_episodes(test_database):
    result = test_database.update_watched([1], True, datetime(2021, 1, 1, 1))
    assert result == []


def test_update_watched_show(test_database):
    result = test_database.update_watched_show(1, True, datetime(2021, 1, 1, 1))
    assert result == []


def test_update_watched_show_season(test_database):
    result = test_database.update_watched_show_season(1, 1, True, datetime(2021, 1, 1, 1))
    assert result == []


def test_get_episodes(test_database):
    result = test_database.get_episodes(1)
    assert result == []


def test_get_unwatched(test_database):
    result = test_database.get_unwatched(datetime(2021, 1, 1, 1))
    assert result == []


def test_seen_between(test_database):
    result = test_database.seen_between(datetime(2021, 1, 1, 1), datetime(2022, 1, 1, 1))
    assert result == []


def test_aired_unseen_between(test_database):
    result = test_database.aired_unseen_between(datetime(2021, 1, 1, 1), datetime(2022, 1, 1, 1))
    assert result == []


def test_get_watched_episodes(test_database):
    result = test_database.get_watched_episodes()
    assert result == []


def test_get_all_episodes(test_database):
    result = test_database.get_all_episodes()
    assert list(result) == []


def test_get_shows_by_ids(test_database):
    result = test_database.get_shows_by_ids([1])
    assert result == []
