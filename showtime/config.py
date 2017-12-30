import os
from configparser import ConfigParser


class Config(ConfigParser):

    common_locatons = [
        os.path.expanduser('~/.showtime.ini')
    ]

    def load_config(self, file_name=''):
        self.add_section('Database')
        self.set('Database', 'Path', str(os.path.join(os.getcwd(), 'showtime.json')))
        if file_name == '':
            for location in self.common_locatons:
                if os.path.exists(location):
                    file_name = location

        if file_name:
            self.read(file_name)
