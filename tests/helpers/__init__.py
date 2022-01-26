from types import SimpleNamespace

tv_maze_show = SimpleNamespace(
    id=1,
    name="test-show",
    premiered="2020-01-01",
    status="Ended",
    url="https:/www.example.com/1"
)


def get_tv_maze_episode(id=1, name="The first episode", airdate="2020-01-01",
                        runtime=60, season=1, number=1):
    return SimpleNamespace(id=id,
                           name=name,
                           airdate=airdate,
                           runtime=runtime,
                           season=season,
                           number=number,
                           )


tv_maze_episode = SimpleNamespace(
    id=1,
    name="The first episode",
    airdate="2020-01-01",
    runtime=60,
    season=1,
    number=1,
)

show = {
    "id": 1,
    "name": "test-show",
    "premiered": "2020-01-01",
    "status": "Ended",
}

show2 = {
    "id": 2,
    "name": "test show 2",
    "premiered": "2020-01-01",
    "status": "Running",
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

decorated_episode = episode | {"show_name": show["name"]}
