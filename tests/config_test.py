"""Showtime Config Module Tests"""

from unittest.mock import MagicMock

import pytest

from showtime.config import Config


@pytest.fixture
def test_config() -> Config:
    config = Config()
    config.read = MagicMock()
    return config


def test_load_file_name(test_config):
    test_config.load('test_file_name.ini')
    test_config.read.assert_called_once_with('test_file_name.ini')


def test_load_tmdb_token_from_config(tmp_path, monkeypatch):
    config_file = tmp_path / 'showtime.ini'
    config_file.write_text('[TMDB]\nAccessToken = config-token\n')
    monkeypatch.setattr(Config, 'common_locations', [])
    config = Config()

    config.load(str(config_file))

    assert config.get('TMDB', 'AccessToken') == 'config-token'


def test_environment_tmdb_token_overrides_config(tmp_path, monkeypatch):
    config_file = tmp_path / 'showtime.ini'
    config_file.write_text('[TMDB]\nAccessToken = config-token\n')
    monkeypatch.setattr(Config, 'common_locations', [])
    monkeypatch.setenv('TMDB_ACCESS_TOKEN', 'environment-token')
    config = Config()

    config.load(str(config_file))

    assert config.get('TMDB', 'AccessToken') == 'environment-token'
