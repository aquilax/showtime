"""Showtime Commands Module"""

import os
import sys
from datetime import date, datetime, timedelta
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, cast

import cmd2
import dateutil.parser
from cmd2 import Cmd, Statement

from showtime.api import Api, get_default_pool_manager
from showtime.config import Config
from showtime.database import get_cashed_write_db, get_memory_db
from showtime.output import Output
from showtime.showtime import ShowtimeApp
from showtime.types import Episode, EpisodeId, Show, ShowId

from . import __version__

SHOW_CATEGORY = 'Show management'
EPISODE_CATEGORY = 'Episode management'


class Showtime(Cmd):
    """Showtime app"""

    current_show = None
    _show_ids: List[ShowId] = []
    _episode_ids: List[EpisodeId] = []

    def __init__(self, app: ShowtimeApp, dry_run=False) -> None:
        """Inits Showtime"""
        config = app.config_get()
        Cmd.__init__(
            self, persistent_history_file=config.get('History', 'Path'))
        self.app = app
        self.dry_run = dry_run
        self.output = Output(self.poutput, self.perror, self.pfeedback, self.ppaged)
        self.prompt = self._get_prompt('')

    def _get_current_datetime(self) -> datetime:
        return datetime.utcnow()

    def _get_prompt(self, name: str = '') -> str:
        """Changes the prompt"""
        dry_run_prompt = "DRY-RUN " if self.dry_run else ''
        if name:
            return f"({dry_run_prompt}showtime: {name}) "
        return f'({dry_run_prompt}showtime) '

    def _get_list(self, ids: str) -> List[ShowId]:
        """Returns list from comma separated values"""
        return [ShowId(x) for x in ids.split(',')]

    def _get_show_id(self, query: str) -> ShowId:
        """Tries to get show_id from user input"""
        if query:
            try:
                return ShowId(query)
            except ValueError:
                shows = self.app.show_search(query)
                self._show_ids = [ShowId(s['id']) for s in shows]
                if len(shows) == 1:
                    return ShowId(shows[0]['id'])
                if len(shows) > 1:
                    select_list: List[Tuple[Any, Optional[str]]] = [(show['id'], show['name']) for show in shows]
                    return ShowId(self.select(select_list, 'Please select one:'))
        if self.current_show:
            return ShowId(self.current_show['id'])
        raise Exception('Please provide a show_id')

    def complete_next(self, text: str, line: int, start_index: int, end_index: int) -> List[str]:
        return self.complete_watch_next(text, line, start_index, end_index)

    def complete_watch_next(self, text: str, _line: int, _start_index: int, _end_index: int) -> List[str]:
        return [str(id) for id in self._show_ids if str(id).startswith(text)]

    def complete_watch(self, text: str, _line: int, _start_index: int, _end_index: int) -> List[str]:
        return [str(id) for id in self._episode_ids if str(id).startswith(text)]

    def complete_episodes(self, text: str, _line: int, _start_index: int, _end_index: int) -> List[str]:
        return [str(id) for id in self._show_ids if str(id).startswith(text)]

    @cmd2.with_category(SHOW_CATEGORY)
    def do_search(self, statement: Statement) -> None:
        """Search shows [search <query>]"""
        search_result = self.app.show_search_api(statement)
        search_result_table = self.output.format_search_results(search_result)
        self.output.poutput(search_result_table)

    @cmd2.with_category(SHOW_CATEGORY)
    def do_follow(self, statement: Statement) -> None:
        """Follow show(s) by id [follow <show_id>[,<show_id>...]]"""
        show_ids = self._get_list(statement)

        for show_id in show_ids:
            self.app.show_follow(show_id,
                                 on_episode_insert=self.output.status_on_episode_insert,
                                 on_episode_update=self.output.status_on_episode_update,
                                 on_show_added=self.output.status_on_show_added)

    @cmd2.with_category(SHOW_CATEGORY)
    def do_shows(self, query: Statement) -> None:
        """Show all followed shows [shows <query>]"""
        shows = self.app.show_search(query)
        self._show_ids = [ShowId(s['id']) for s in shows]
        shows_table = self.output.shows_table(shows)
        self.output.ppaged(shows_table)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_episodes(self, query: Statement) -> None:
        """Show all episodes for a show [episodes <show_id>]"""
        show_id = self._get_show_id(query)
        show = self.app.show_get(show_id)
        if not show:
            self.output.perror(f'Show {show_id} not found')
            return
        episodes = self.app.episodes_get(ShowId(show['id']))
        self._episode_ids = [s['id'] for s in episodes]
        episodes_table = self.output.format_episodes(show, episodes)
        self.output.ppaged(episodes_table)

    @cmd2.with_category(SHOW_CATEGORY)
    def do_set_show(self, statement: Statement) -> None:
        """Set show in context [set_show <show_id>]"""
        show_id = self._get_show_id(statement)
        show = self.app.show_get(show_id)
        if not show:
            self.output.perror(f'Show {show_id} not found')
            return
        self.current_show = show
        self.prompt = self._get_prompt(show['name'])

    @cmd2.with_category(SHOW_CATEGORY)
    def do_unset_show(self, _: Statement) -> None:
        """Remove show from the context [unset_show]"""
        self.current_show = None
        self.prompt = self._get_prompt()

    @cmd2.with_category(SHOW_CATEGORY)
    def do_completed(self, _: Statement) -> None:
        """Show list of completed shows"""
        shows = self.app.show_get_completed()
        completed_shows_table = self.output.completed_shows_table(shows)
        self.output.ppaged(completed_shows_table)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_sync(self, _: Statement) -> None:
        """Synchronize episodes with TVMaze [sync]"""
        self.output.pfeedback('Syncing shows...')
        self.app.sync(on_show_sync=self.output.status_on_show_sync,
                      on_episode_insert=self.output.status_on_episode_insert,
                      on_episode_update=self.output.status_on_episode_update)
        self.output.pfeedback('Done')

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_watch(self, statement: Statement) -> None:
        """Mark episodes as watched [watch <episode_id,...>]"""
        when = self._get_current_datetime()
        for episode_id in [e.strip() for e in statement.split(',')]:
            self.app.episode_update_watched(EpisodeId(episode_id), when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_next(self, statement: Statement) -> None:
        """Mark next unwatched episode as watched [next <show_id>]"""
        self.do_watch_next(statement)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_watch_next(self, statement: Statement) -> None:
        """Mark next unwatched episode as watched [watch_next <show_id>]"""
        show_id = self._get_show_id(statement)
        show = self.app.show_get(show_id)
        if not show:
            self.output.perror(f'Show {show_id} not found')
            return
        episode = self.app.episode_get_next_unwatched(show_id)
        if episode:
            episodes_table = self.output.format_episodes(show, [episode])
            self.output.poutput(episodes_table)
            response = input('Did you watch this episode [Y/n]:')
            if response.lower() in ['y', '']:
                when = self._get_current_datetime()
                self.app.episode_update_watched(EpisodeId(episode['id']), when)
                return
            self.output.pfeedback('Canceling...')
            return
        self.output.perror(f"No episodes left unwatched for `{show['name']}`")

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_delete_episode(self, statement: Statement) -> None:
        """Delete episode [delete_episode <episode_id>]"""
        episode_id = EpisodeId(statement)
        episode = self.app.episode_get(episode_id)
        if episode:
            show = self.app.show_get(ShowId(episode['show_id']))
            episodes_table = self.output.format_episodes(cast(Show, show), [episode])
            self.output.poutput(episodes_table)
            response = input('Do you want to delete this episode [y/N]:')
            if response.lower() in ['y']:
                return self.app.episode_delete(EpisodeId(episode['id']))
            return self.output.pfeedback('Canceling...')
        self.output.perror('Invalid episode_id')

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_unwatch(self, statement: Statement) -> None:
        """Mark episode as not watched [unwatch <episode_id>]"""
        when = self._get_current_datetime()
        self.app.episode_update_not_watched(EpisodeId(statement), when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_watch_all(self, statement: Statement) -> None:
        """Mark all episodes in a show as watched [watch_all <show_id>]"""
        show_id = self._get_show_id(statement)
        when = self._get_current_datetime()
        self.app.episodes_update_all_watched(show_id, when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_unwatch_all(self, statement: Statement) -> None:
        """Mark all episodes in a show as not watched [unwatch_all <show_id>]"""
        show_id = self._get_show_id(statement)
        when = self._get_current_datetime()
        self.app.episodes_update_all_not_watched(show_id, when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_watch_all_season(self, statement: Statement) -> None:
        """Mark all episodes in a show and season as watched [watch_all_season <show_id> <season>]"""
        show_id, season = statement.split(' ')
        when = self._get_current_datetime()
        self.app.episodes_update_season_watched(ShowId(show_id), int(season), when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_unwatch_all_season(self, statement: Statement) -> None:
        """Mark all episodes in a show and season as not watched [unwatch_all_season <show_id> <season>]"""
        show_id, season = statement.split(' ')
        when = self._get_current_datetime()
        self.app.episodes_update_season_not_watched(ShowId(show_id), int(season), when)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_unwatched(self, _: Statement) -> None:
        """Show list of all episodes not watched yet [unwatched]"""
        when = self._get_current_datetime()
        episodes = self.app.episodes_get_unwatched(when)
        episodes_table = self.output.format_unwatched(episodes)
        self.output.poutput(episodes_table)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_last_seen(self, statement: Statement) -> None:
        """Mark all episodes as seen up to the defined one [last_seen <show_id> <season> <episode>]"""
        show_id, season, episode = statement.split(' ')
        when = self._get_current_datetime()
        count = self.app.episodes_watched_to_last_seen(ShowId(show_id), int(season), int(episode), when)
        self.output.poutput(f'{count} episodes marked as seen')

    def do_config(self, _: Statement) -> None:
        """Show current configuration [config]"""
        config = self.app.config_get()
        path = config.get('Database', 'Path')
        self.output.poutput(f'Database path: {path}')

    def do_export(self, statement: Statement) -> None:
        """Export seen episodes between dates[export <from_date> <to_date>]"""
        try:
            from_date_s, to_date_s = statement.split(' ')
            from_date = dateutil.parser.parse(from_date_s).date()
            to_date = dateutil.parser.parse(to_date_s).date()

        except (dateutil.parser.ParserError, OverflowError):
            self.output.perror("Invalid date")
            return

        episodes = self.app.episodes_watched_between(from_date, to_date)
        self.output.json(sorted(episodes, key=lambda k: k['watched']))

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_watched_between(self, statement: Statement) -> None:
        """Export seen episodes between dates[export <from_date> <to_date>]"""
        try:
            from_date_s, to_date_s = statement.split(' ')
            from_date = dateutil.parser.parse(from_date_s).date()
            to_date = dateutil.parser.parse(to_date_s).date()

        except (dateutil.parser.ParserError, OverflowError):
            self.output.perror("Invalid date")
            return

        episodes = self.app.episodes_watched_between(from_date, to_date)
        sorted_episodes = sorted(episodes, key=lambda k: k['watched'])
        episodes_table = self.output.format_unwatched(sorted_episodes)
        self.output.ppaged(episodes_table)

    @cmd2.with_category(EPISODE_CATEGORY)
    def do_new_unwatched(self, statement: Statement) -> None:
        """Show unwatched episodes aired in the last 7 days[new_unwatched <days>]"""
        spl_statement = statement.split(' ')
        days = int(spl_statement[0]) if len(spl_statement) > 0 and spl_statement[0] != '' else 7
        d_start_date = dateutil.parser.parse(spl_statement[1]).date() if len(spl_statement) > 1 else date.today()

        delta = timedelta(days=days - 1)
        from_date = d_start_date - delta
        to_date = d_start_date
        episodes = self.app.episodes_aired_unseen_between(from_date, to_date)
        episodes_table = self.output.format_unwatched(
            sorted(episodes, key=lambda k: k['airdate']))
        self.output.ppaged(episodes_table)

    def do_version(self, _: Statement) -> None:
        """Show current version"""
        self.output.poutput(__version__)

    def do_patch_watchtime(self, file_name: Statement) -> None:
        """Update watchtimes from csv file"""
        self.app.episodes_patch_watchtime(file_name)

    def do_watching_stats(self, _: Statement) -> None:
        """Statistics about watchtime"""
        watched = self.app.episodes_get_watched()
        minutes = reduce(
            (lambda acc, ep: acc + ep['runtime'] if ep['runtime'] else 0), watched, 0)

        def month_groupper(acc: Dict[str, Dict[str, int]], episode: Episode) -> Dict[str, Dict[str, int]]:
            """Groups watched episodes by month"""
            date = episode['watched'][0:7]
            runtime = episode['runtime'] if episode['runtime'] else 0
            if not date in acc:
                acc[date] = {'episodes': 0, 'minutes': 0}
            acc[date]['episodes'] = acc[date]['episodes'] + 1
            acc[date]['minutes'] = acc[date]['minutes'] + runtime
            return acc

        month_totals: Dict[str, Dict[str, int]] = reduce(month_groupper, watched, {})
        self.output.poutput(f"Total watched episodes: {len(watched)}")
        self.output.poutput(f"Total watchtime in minutes: {minutes}")
        summary_table = self.output.summary_table(month_totals)
        self.output.ppaged(summary_table)


def main() -> None:
    api = Api(get_default_pool_manager())
    config = Config()
    config.load()
    dry_run = os.getenv('SHOWTIME_DRY_RUN') != None
    database_filename = config.get('Database', 'Path')
    database = get_memory_db() if dry_run else get_cashed_write_db(database_filename)
    app = ShowtimeApp(api, database, config)
    sys.exit(Showtime(app, dry_run=dry_run).cmdloop())


if __name__ == '__main__':
    main()
