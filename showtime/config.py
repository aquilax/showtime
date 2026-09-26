"""Showtime Configuration"""

import os
from configparser import ConfigParser


class Config(ConfigParser):
    """Configuration class"""

    common_locations = [
        os.path.expanduser('~/.showtime.ini')
    ]

    def load(self, file_name: str = '') -> None:
        """Loads configuration file"""
        self.add_section('Database')
        self.set('Database', 'Path', str(os.path.join(os.getcwd(), 'showtime.json')))

        self.add_section('History')
        self.set('History', 'Path', str(os.path.expanduser('~/.showtime_history')))

        self.add_section('TMDB')
        self.set('TMDB', 'AccessToken', '')

        if file_name == '':
            for location in self.common_locations:
                if os.path.exists(location):
                    file_name = location

        if file_name:
            self.read(file_name)

        tmdb_access_token = os.getenv('TMDB_ACCESS_TOKEN')
        if tmdb_access_token:
            self.set('TMDB', 'AccessToken', tmdb_access_token)
