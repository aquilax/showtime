from datetime import date, datetime
from unittest.mock import MagicMock, Mock, call

import pytest
from helpers import decorated_episode, episode, show, show2, tv_maze_show, tv_maze_episode, get_tv_maze_episode

from showtime.showtime import ShowtimeApp
from showtime.types import TMDBMovie


@pytest.fixture
def test_app() -> ShowtimeApp:
    api = Mock()
    database = Mock()
    config = Mock()
    showtime = ShowtimeApp(api, database, config)
    return showtime


def test_show_search(test_app):
    test_app.database.get_shows = MagicMock(return_value=[show])

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
    test_app.database.get_shows_by_ids = MagicMock(return_value=[show])
    test_app.database.get_all_episodes = MagicMock(return_value=iter([
        episode | {'watched': '2020-01-01'}
    ]))

    result = test_app.show_get_completed()

    test_app.database.get_all_episodes.assert_called_once()
    test_app.database.get_shows_by_ids.assert_called_once_with([1])
    assert result == [show]


def test_episodes_update_all_watched(test_app):
    test_app.database.update_watched_show = MagicMock(return_value=None)

    result = test_app.episodes_update_all_watched(1, datetime(2020, 1, 1, 1, 0))

    assert result is None
    test_app.database.update_watched_show.assert_called_once_with(1, True, datetime(2020, 1, 1, 1, 0))


def test_episodes_update_all_not_watched(test_app):
    test_app.database.update_watched_show = MagicMock(return_value=None)

    result = test_app.episodes_update_all_not_watched(1, datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched_show.assert_called_once_with(1, False, datetime(2020, 1, 1, 1, 0))
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

def test_movie_search(test_app):
    movies = [
        {'id': 42, 'title': 'Test Movie', 'release_date': '2020-01-01', 'runtime': 120, 'watched': ''},
        {'id': 43, 'title': 'Other Film', 'release_date': None, 'runtime': None, 'watched': ''},
    ]
    test_app.database.get_movies = MagicMock(return_value=movies)

    result = test_app.movie_search('test')

    assert result == [movies[0]]


def test_movie_search_api(test_app):
    movie = TMDBMovie(42, 'Test Movie', '2020-01-01', 120)
    test_app.api.movie_search = MagicMock(return_value=[movie])

    result = test_app.movie_search_api('test')

    test_app.api.movie_search.assert_called_once_with('test')
    assert result == [movie]


def test_movie_add(test_app):
    movie = TMDBMovie(42, 'Test Movie', '2020-01-01', 120, {'imdb_id': 'tt1234567'})
    test_app.api.movie_get = MagicMock(return_value=movie)
    test_app.api.movie_external_ids = MagicMock(return_value={'imdb_id': 'tt1234567'})
    test_app.database.add_movie = MagicMock(return_value=42)

    result = test_app.movie_add(42)

    test_app.api.movie_get.assert_called_once_with(42)
    test_app.api.movie_external_ids.assert_called_once_with(42)
    test_app.database.add_movie.assert_called_once_with(movie)
    assert result == movie


def test_movie_add_watched(test_app):
    movie = TMDBMovie(42, 'Test Movie', '2020-01-01', 120, {'imdb_id': 'tt1234567'})
    when = datetime(2020, 1, 1, 1, 0)
    test_app.api.movie_get = MagicMock(return_value=movie)
    test_app.api.movie_external_ids = MagicMock(return_value={'imdb_id': 'tt1234567'})
    test_app.database.add_movie = MagicMock(return_value=42)
    test_app.database.update_movie_watched = MagicMock(return_value=[1])

    result = test_app.movie_add_watched(42, when)

    test_app.api.movie_get.assert_called_once_with(42)
    test_app.api.movie_external_ids.assert_called_once_with(42)
    test_app.database.add_movie.assert_called_once_with(movie)
    test_app.database.update_movie_watched.assert_called_once_with(42, True, when)
    assert result == movie


def test_import_imdb_ratings_adds_movies_and_skips_other_rows(test_app, tmp_path):
    export_file = tmp_path / 'ratings.csv'
    export_file.write_text(
        'Const,Your Rating,Date Rated,Title Type\n'
        'tt1111111,8,2020-01-02,Movie\n'
        'tt2222222,7,2021-03-04,TV Movie\n'
        'tt3333333,9,2022-05-06,TV Series\n'
        'tt4444444,,2023-07-08,Movie\n'
        'tt5555555,6,2024-09-10,Movie\n',
        encoding='utf-8',
    )
    tracked_movie = {
        'id': 1,
        'title': 'Already Tracked',
        'release_date': '2019-01-01',
        'runtime': 90,
        'watched': '',
        'external_ids': {'imdb_id': 'tt1111111'},
    }
    test_app.database.get_movies = MagicMock(return_value=[tracked_movie])
    test_app.database.update_movie_watched = MagicMock(return_value=[1])
    test_app.api.movie_find_by_imdb_id = MagicMock(return_value=2)
    test_app.api.movie_get = MagicMock(return_value=TMDBMovie(2, 'New Movie', '2021-01-01', 100))
    test_app.api.movie_external_ids = MagicMock(return_value={'imdb_id': 'tt2222222'})
    test_app.database.add_movie = MagicMock(return_value=2)

    result = test_app.import_imdb_ratings(str(export_file))

    assert result == (2, 3)
    test_app.api.movie_find_by_imdb_id.assert_has_calls([call('tt2222222'), call('tt5555555')])
    test_app.database.update_movie_watched.assert_any_call(1, True, datetime(2020, 1, 2))
    test_app.database.update_movie_watched.assert_any_call(2, True, datetime(2021, 3, 4))


def test_import_imdb_ratings_backfills_existing_external_ids(test_app, tmp_path):
    export_file = tmp_path / 'ratings.csv'
    export_file.write_text(
        'Const,Your Rating,Date Rated,Title Type\n'
        'tt1234567,8,2020-01-02,Movie\n',
        encoding='utf-8',
    )
    tracked_movie = {'id': 1, 'title': 'Already Tracked', 'release_date': None, 'runtime': None, 'watched': ''}
    test_app.database.get_movies = MagicMock(return_value=[tracked_movie])
    test_app.database.update_movie_external_ids = MagicMock(return_value=[1])
    test_app.database.update_movie_watched = MagicMock(return_value=[1])
    test_app.api.movie_external_ids = MagicMock(return_value={'imdb_id': 'tt1234567', 'wikidata_id': 'Q123'})

    result = test_app.import_imdb_ratings(str(export_file))

    assert result == (1, 0)
    test_app.database.update_movie_external_ids.assert_called_once_with(1, {
        'imdb_id': 'tt1234567', 'wikidata_id': 'Q123'
    })
    test_app.database.update_movie_watched.assert_called_once_with(1, True, datetime(2020, 1, 2))


def test_import_imdb_ratings_rejects_missing_headers(test_app, tmp_path):
    export_file = tmp_path / 'ratings.csv'
    export_file.write_text('Const,Title\ntt1234567,Movie\n', encoding='utf-8')

    with pytest.raises(ValueError, match='IMDb export must include'):
        test_app.import_imdb_ratings(str(export_file))


def test_movie_remove(test_app):
    test_app.database.delete_movie = MagicMock(return_value=[1])

    result = test_app.movie_remove(42)

    test_app.database.delete_movie.assert_called_once_with(42)
    assert result == [1]


def test_movie_update_watched(test_app):
    test_app.database.update_movie_watched = MagicMock(return_value=[1])
    when = datetime(2020, 1, 1, 1, 0)

    result = test_app.movie_update_watched(42, True, when)

    test_app.database.update_movie_watched.assert_called_once_with(42, True, when)
    assert result == [1]


def test_config_get(test_app):
    result = test_app.config.get()
    assert result is not None


def test_episode_update_watched(test_app):
    test_app.database.update_watched = MagicMock(return_value=None)

    result = test_app.episode_update_watched(1, datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched.assert_called_once_with(1, True, datetime(2020, 1, 1, 1, 0))
    assert result is None


def test_episode_update_not_watched(test_app):
    test_app.database.update_watched = MagicMock(return_value=None)

    result = test_app.episode_update_not_watched(1, datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched.assert_called_once_with(1, False, datetime(2020, 1, 1, 1, 0))
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

    result = test_app.episodes_update_season_watched(1, 1,  datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched_show_season.assert_called_once_with(1, 1, True,  datetime(2020, 1, 1, 1, 0))
    assert result is None


def test_episodes_update_season_not_watched(test_app):
    test_app.database.update_watched_show_season = MagicMock(return_value=None)

    result = test_app.episodes_update_season_not_watched(1, 1,  datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched_show_season.assert_called_once_with(1, 1, False,  datetime(2020, 1, 1, 1, 0))
    assert result is None


def test_episodes_get_unwatched(test_app):
    test_app.database.get_unwatched = MagicMock(return_value=[episode])
    test_app.database.get_shows = MagicMock(return_value=[show, show2])

    result = test_app.episodes_get_unwatched(datetime(2020, 1, 1, 1, 0))

    test_app.database.get_unwatched.assert_called_once_with(datetime(2020, 1, 1, 1, 0))
    test_app.database.get_shows.assert_called_once()
    assert result == [decorated_episode]


def test_episodes_watched_to_last_seen(test_app):
    test_app.database.get_episodes = MagicMock(return_value=[
        episode,
        episode | {'id': 2, 'number': 2},
        episode | {'id': 3, 'number': 3},
        episode | {'id': 4, 'season': 2, 'number': 1},
        episode | {'id': 5, 'season': 2, 'number': 2},
        episode | {'id': 6, 'season': 2, 'number': 3},
    ])
    test_app.database.update_watched_episodes = MagicMock(return_value=4)

    result = test_app.episodes_watched_to_last_seen(1, 2, 1, datetime(2020, 1, 1, 1, 0))

    test_app.database.update_watched_episodes.assert_called_once_with([1, 2, 3, 4], True, datetime(2020, 1, 1, 1, 0))
    assert result == 4


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


def test_show_follow(test_app):
    test_app.database.get_active_shows = MagicMock(return_value=[show])
    test_app.api.show_get = MagicMock(return_value=tv_maze_show)
    test_app.api.episodes_list = MagicMock(return_value=[tv_maze_episode, get_tv_maze_episode(id=2)])
    test_app.database.get_episodes = MagicMock(return_value=[episode | {'name': 'old episode name name'}])

    result = test_app.sync()

    test_app.database.get_active_shows.assert_called_once()
    test_app.api.show_get.assert_called_once_with(1)
    test_app.database.update_show.assert_called_once_with(1, tv_maze_show)
    test_app.api.episodes_list.assert_called_once_with(1)
    test_app.database.get_episodes.assert_called_once_with(1)
    test_app.database.insert_episodes.assert_called_once_with([{
        'id': 2,
        'show_id': 1,
        'season': 1,
        'number': 1,
        'name': 'The first episode',
        'airdate': '2020-01-01',
        'runtime': 60,
        'watched': ''
    }])
    test_app.database.update_episodes.assert_called_once_with([({
        'name': tv_maze_episode.name,
        'airdate': tv_maze_episode.airdate,
        'runtime': tv_maze_episode.runtime,
        'season': tv_maze_episode.season,
        'number': tv_maze_episode.number,
    }, 1)])
    assert result == None


def test_sync(test_app):
    result = test_app.episodes_get_watched()


def test_episodes_patch_watchtime(test_app):
    pass
