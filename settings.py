"""Module to work with default or environment settings."""
from dataclasses import dataclass

from environs import Env

DEFAULT_HOST = 'minechat.dvmn.org'
DEFAULT_SEND_PORT = 5050
DEFAULT_LISTEN_PORT = 5000
DEFAULT_NICKNAME = 'Anonymous'
DEFAULT_HISTORY_FILE = 'minechat.history'


@dataclass
class Settings:
    """Settings for Minechat scripts."""

    host: str
    send_port: int
    listen_port: int
    nickname: str
    history_file: str
    token: str


def get_settings():
    """Read settings from environment variables, use defaults if they are missing."""
    env = Env()
    env.read_env()

    return Settings(
        host=env('HOST', DEFAULT_HOST),
        send_port=env.int('SEND_PORT', DEFAULT_SEND_PORT),
        listen_port=env.int('LISTEN_PORT', DEFAULT_LISTEN_PORT),
        nickname=env('NICKNAME', DEFAULT_NICKNAME),
        history_file=env('HISTORY_FILE', DEFAULT_HISTORY_FILE),
        token=env('TOKEN', None),
    )


settings = get_settings()
