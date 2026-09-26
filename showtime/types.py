"""Showtime Types Module"""

from enum import Enum
from typing import Dict, NamedTuple, Optional
from typing_extensions import NotRequired, TypedDict

ShowId = int
EpisodeId = int
MovieId = int
Date = str


class TVMazeShow(NamedTuple):
    """API Show result"""
    id: int
    name: str
    premiered: str
    status: str
    url: str
    externals: Dict


class TVMazeEpisode(NamedTuple):
    """API Episode result"""
    id: int
    season: int
    number: int
    name: str
    airdate: Date
    runtime: int


class TMDBMovie(NamedTuple):
    """TMDB movie result"""
    id: MovieId
    title: str
    release_date: str | None
    runtime: int | None
    external_ids: Optional[Dict[str, Optional[str]]] = None
    original_language: Optional[str] = None


class Movie(TypedDict):
    """DB movie"""
    id: MovieId
    title: str
    release_date: Date | None
    runtime: int | None
    watched: Date
    external_ids: NotRequired[Dict[str, Optional[str]]]
    original_language: NotRequired[Optional[str]]


class ShowStatus(Enum):
    """API Show status"""
    ENDED = 'Ended'
    RUNNING = 'Running'
    IN_DEVELOPMENT = 'In Development'
    TO_BE_DETERMINED = 'To Be Determined'


class Show(TypedDict):
    """DB Show"""
    id: ShowId
    name: str
    premiered: Date
    status: str
    externals: Dict


class ShowWithCount(Show):
    """DB Show with episode counts"""
    total: int
    seen: int


class Episode(TypedDict):
    """DB Episode"""
    id: EpisodeId
    show_id: ShowId
    season: int
    number: int
    name: str
    airdate: Date
    runtime: int
    watched: Date


class DecoratedEpisode(Episode):
    """Decorated Episode"""
    show_name: str
