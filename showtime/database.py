from enum import Enum
from datetime import datetime
import os
import json
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

    def get_episodes(self, show_id):
        Episode = Query()
        return self.episode_table.search(Episode.show_id == show_id)

    def sync_episodes(self, show_id, episodes):
        exising_episodes = self.get_episodes(show_id)
        for episode in episodes:
            matched = [x for x in exising_episodes if x['id'] == episode.id]
            if not matched:
                print('Adding new episode: S{season:0>2} E{episode:0>2} ({id}) {name} - {airdate}'.format(
                    season=episode.season, episode=episode.number, id=episode.id,
                    name=episode.name, airdate=episode.airdate))

                self.episode_table.insert({
                    'id': episode.id,
                    'show_id': show_id,
                    'season': episode.season,
                    'number': episode.number,
                    'name': episode.name,
                    'airdate': episode.airdate,
                    'runtime': episode.runtime,
                    'watched': ''
                })

    def update_watched(self, episode_id: int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, Episode.id == episode_id)

    def get_unwatched(self):
        Episode = Query()
        return self.episode_table.search(Episode.watched == '')

    def update_watched_show(self, show_id:int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, Episode.show_id == show_id)

    def update_watched_show_season(self, show_id:int, season:int, watched: bool):
        Episode = Query()
        watched_value = datetime.utcnow().isoformat() if watched else ''
        self.episode_table.update({
            'watched': watched_value
        }, ((Episode.show_id == show_id) & (Episode.season == season)))

