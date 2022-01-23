"""Showtime Types Module"""

from enum import Enum
from typing import NamedTuple
from typing_extensions import TypedDict

ShowId = int
EpisodeId = int
Date = str


class TVMazeShow(NamedTuple):
    """API Show result"""
    id: int
    name: str
    premiered: str
    status: str
    url: str


class TVMazeEpisode(NamedTuple):
    """API Episode result"""
    id: int
    season: int
    number: int
    name: str
    airdate: Date
    runtime: int


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
