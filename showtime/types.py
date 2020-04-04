from enum import Enum
from typing import NamedTuple
from typing_extensions import TypedDict
from collections import namedtuple

ShowId = int
EpisodeId = int
Date = str


class TVMazeShow(NamedTuple):
    id: int
    name: str
    premiered: str
    status: str
    url: str

class TVMazeEpisode(NamedTuple):
    id: int
    season: int
    number: int
    name: str
    airdate: Date
    runtime: int


class ShowStatus(Enum):
    ENDED = 'Ended'
    RUNNING = 'Running'
    IN_DEVELOPMENT = 'In Development'
    TO_BE_DETERMINED = 'To Be Determined'


class Show(TypedDict):
    id: ShowId
    name: str
    premiered: Date
    status: str


class Episode(TypedDict):
    id: EpisodeId
    show_id: ShowId
    season: int
    number: int
    name: str
    airdate: Date
    runtime: int
    watched: Date


class DecoratedEpisode(Episode):
    show_name: str
