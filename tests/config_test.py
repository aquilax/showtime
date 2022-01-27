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


def test_load_default(test_config):
    test_config.load('')
    test_config.read.assert_called_once()
