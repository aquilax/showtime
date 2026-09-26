# showtime

Small command line tracker for TV series using TVMaze and movies using TMDB.

## Installation

```sh
pip install showtime-cli
```

## Movies

Movie search and add use TMDB. Set a TMDB API Read Access Token with
`TMDB_ACCESS_TOKEN`, or add it to `~/.showtime.ini`:

```ini
[TMDB]
AccessToken = your-tmdb-read-access-token
```

The token is needed for `movie_search`, `movie_add`, and IMDb imports. Movie
tracking and watched status are stored locally:

```text
movie_search <query>
movie_add <tmdb_id>
movie_add_watched <tmdb_id>
movie_remove <tmdb_id>
movies [query]
movie_watch <tmdb_id>
movie_unwatch <tmdb_id>
movie_import_imdb_ratings <filename>
```

IMDb imports read the `Const`, `Your Rating`, `Date Rated`, and `Title Type`
columns. Movie and TV Movie rows are resolved through TMDB, added if needed,
and marked watched on their IMDb rating date. Other title types and unresolved
IMDb IDs are skipped.
