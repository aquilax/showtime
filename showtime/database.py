import csv
import dateutil.parser

from enum import Enum
from datetime import datetime
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware
from showtime.types import EpisodeId, ShowId


SHOW = 'show'
EPISODE = 'episode'


class ShowStatus(Enum):
    ENDED = 'Ended'
    RUNNING = 'Running'


def _test_between(d, from_date, to_date):
    if d:
        return from_date <= dateutil.parser.parse(d).date() <= to_date
    return False


class Database(TinyDB):

    db = None

    def __init__(self, *args, **kwargs):
        self.db = TinyDB(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def add(self, show):
        Show = Query()
        if not self.db.table(SHOW).contains(Show.id == show.id):
            self.db.table(SHOW).insert({
                'id': show.id,
                'name': show.name,
                'premiered': show.premiered,
                'status': show.status
            })
        return show.id

    def get_shows(self):
        return self.db.table(SHOW).all()

    def get_active_shows(self):
        Show = Query()
        return self.db.table(SHOW).search(Show.status != ShowStatus.ENDED.value)

    def get_show(self, show_id: ShowId):
        Show = Query()
        return self.db.table(SHOW).get(Show.id == show_id)

    def get_episode(self, episode_id: EpisodeId):
        Episode = Query()
        return self.db.table(EPISODE).get(Episode.id == episode_id)

    def get_episodes(self, show_id: ShowId):
        Episode = Query()
        episodes = self.db.table(EPISODE).search(Episode.show_id == show_id)
        return sorted(episodes, key=lambda ep: ep['season'] * 1000 + ep['number'])

    def delete_episode(self, episode_id: EpisodeId):
        Episode = Query()
        return self.db.table(EPISODE).remove(Episode.id == episode_id)

    def sync_episodes(self, show_id: ShowId, episodes):
        existing_episodes = self.get_episodes(show_id)
        queue = []
        for episode in episodes:
            matched = [x for x in existing_episodes if x['id'] == episode.id]
            if not matched:
                print('\tAdding new episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
                    season=episode.season, episode=episode.number, id=episode.id,
                    name=episode.name, airdate=episode.airdate))

                queue.append({
                    'id': episode.id,
                    'show_id': show_id,
                    'season': episode.season,
                    'number': episode.number,
                    'name': episode.name,
                    'airdate': episode.airdate,
                    'runtime': episode.runtime,
                    'watched': ''
                })
            else:
                matched_episode = matched.pop()
                if (
                    matched_episode['name'] != episode.name or
                    matched_episode['airdate'] != episode.airdate or
                    matched_episode['runtime'] != episode.runtime or
                    matched_episode['season'] != episode.season or
                    matched_episode['number'] != episode.number
                ):
                    print('\tUpdating episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
                        season=episode.season, episode=episode.number, id=episode.id,
                        name=episode.name, airdate=episode.airdate))
                    Episode = Query()
                    self.db.table(EPISODE).update({
                        'name': episode.name,
                        'airdate': episode.airdate,
                        'runtime': episode.runtime,
                        'season': episode.season,
                        'number': episode.number,
                    }, Episode.id == episode.id)
        self.db.table(EPISODE).insert_multiple(queue)

    def update_watched(self, episode_id: EpisodeId, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.db.table(EPISODE).update({
            'watched': watched_value
        }, Episode.id == episode_id)

    def get_unwatched(self):
        Episode = Query()
        return self.decorate_episodes(
            sorted(self.db.table(EPISODE).search(((Episode.watched == '') & (Episode.airdate <= datetime.utcnow().isoformat()))), key=lambda episode: episode['airdate'] or ''))

    def update_watched_show(self, show_id: ShowId, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.db.table(EPISODE).update({
            'watched': watched_value
        }, Episode.show_id == show_id)

    def update_watched_show_season(self, show_id: ShowId, season: int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.db.table(EPISODE).update({
            'watched': watched_value
        }, ((Episode.show_id == show_id) & (Episode.season == season)))

    def last_seen(self, show_id: ShowId, season, number):
        episodes = self.get_episodes(show_id)
        eids = []
        for episode in episodes:
            if episode['season'] > season:
                continue
            if episode['season'] < season or (episode['season'] == season and episode['number'] < number):
                eids.append(episode.eid)
                continue
        watched_value = datetime.utcnow().isoformat()
        self.db.table(EPISODE).update({
            'watched': watched_value
        }, eids=eids)
        return len(eids)

    def get_next_unwatched(self, show_id: ShowId):
        episodes = self.get_episodes(show_id)
        if episodes:
            for episode in episodes:
                if episode['watched'] == '':
                    return episode
        return None

    def seen_between(self, from_date, to_date):
        Episode = Query()
        episodes = self.db.table(EPISODE).search(
            Episode.watched.test(_test_between, from_date, to_date))
        return episodes

    def aired_unseen_between(self, from_date, to_date):
        Episode = Query()
        episodes = self.db.table(EPISODE).search(
            (Episode.airdate.test(_test_between, from_date, to_date)) &
            (Episode.watched == ''))
        return self.decorate_episodes(episodes)

    def decorate_episodes(self, episodes):
        result = []
        shows = {show['id']: show for show in self.get_shows()}
        for episode in episodes:
            show = shows[episode['show_id']]
            episode['show_name'] = show['name']
            result.append(episode)
        return result

    def update_watch_times(self, patch_file_name):
        Episode = Query()
        with open(patch_file_name, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                self.db.table(EPISODE).update({
                    'watched': row[1]
                }, Episode.id == int(row[0]))
                print(row[0])
        self.db.close()

    def get_watched_episodes(self):
        Episode = Query()
        return self.db.table(EPISODE).search(Episode.watched != '')

def getDirectWriteDB(file_name: str) -> Database:
    return Database(file_name, sort_keys=True, indent=4)


def getCashedWriteDB(file_name: str) -> Database:
    return Database(file_name, storage=CachingMiddleware(JSONStorage), sort_keys=True, indent=4)


def getMemoryDB() -> Database:
    return Database(storage=MemoryStorage)
