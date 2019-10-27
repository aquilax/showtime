import dateutil.parser

from enum import Enum
from datetime import datetime
from tinydb import TinyDB, Query


class ShowStatus(Enum):
    ENDED = 'Ended'
    RUNNING = 'Running'


class Database():

    db = None

    def __init__(self, file_name):
        self.db = TinyDB(file_name, sort_keys=True, indent=4)
        self.show_table = self.db.table('show')
        self.episode_table = self.db.table('episode')

    def add(self, show):
        Show = Query()
        if not self.show_table.contains(Show.id == show.id):
            self.show_table.insert({
                'id': show.id,
                'name': show.name,
                'premiered': show.premiered,
                'status': show.status
            })
        return show.id

    def get_shows(self):
        return self.show_table.all()

    def get_active_shows(self):
        Show = Query()
        return self.show_table.search(Show.status != ShowStatus.ENDED.value)

    def get_show(self, show_id: int):
        Show = Query()
        return self.show_table.get(Show.id == show_id)

    def get_episode(self, episode_id: int):
        Episode = Query()
        return self.episode_table.get(Episode.id == episode_id)

    def get_episodes(self, show_id):
        Episode = Query()
        episodes = self.episode_table.search(Episode.show_id == show_id)
        return sorted(episodes, key=lambda ep: ep['season'] * 1000 + ep['number'])

    def delete_episode(self, episode_id):
        Episode = Query()
        return self.episode_table.remove(Episode.id == episode_id)

    def sync_episodes(self, show_id, episodes):
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
                    self.episode_table.update({
                        'name': episode.name,
                        'airdate': episode.airdate,
                        'runtime': episode.runtime,
                        'season': episode.season,
                        'number': episode.number,
                    }, Episode.id == episode.id)
        self.episode_table.insert_multiple(queue)

    def update_watched(self, episode_id: int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, Episode.id == episode_id)

    def get_unwatched(self):
        Episode = Query()
        return self.decorate_episodes(
            sorted(self.episode_table.search(((Episode.watched == '') & (Episode.airdate <= datetime.utcnow().isoformat()))), key=lambda episode: episode['airdate'] or ''))

    def update_watched_show(self, show_id: int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, Episode.show_id == show_id)

    def update_watched_show_season(self, show_id: int, season: int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, ((Episode.show_id == show_id) & (Episode.season == season)))

    def last_seen(self, show_id, season, number):
        episodes = self.get_episodes(show_id)
        eids = []
        for episode in episodes:
            if episode['season'] > season:
                continue
            if episode['season'] < season or (episode['season'] == season and episode['number'] < number):
                eids.append(episode.eid)
                continue
        watched_value = datetime.utcnow().isoformat()
        self.episode_table.update({
            'watched': watched_value
        }, eids=eids)
        return len(eids)

    def get_next_unwatched(self, show_id):
        episodes = self.get_episodes(show_id)
        if episodes:
            for episode in episodes:
                if episode['watched'] == '':
                    return episode
        return None

    def seen_between(self, from_date, to_date):
        def test_between(d, from_date, to_date):
            if d:
                return from_date <= dateutil.parser.parse(d).date() <= to_date
            return False

        Episode = Query()
        episodes = self.episode_table.search(
            Episode.watched.test(test_between, from_date, to_date))
        return episodes

    def decorate_episodes(self, episodes):
        result = []
        shows = {show['id']: show for show in self.get_shows()}
        for episode in episodes:
            show = shows[episode['show_id']]
            episode['show_name'] = show['name']
            result.append(episode)
        return result
