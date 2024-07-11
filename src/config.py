import os
from abc import ABC, abstractmethod
from typing import Any

from dotenv import dotenv_values


class Config(ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        pass


class StagingConfig(Config):
    def __init__(self, *args, **kwargs) -> None:
        self._config_envs = {
            **dotenv_values(".env"),
            **os.environ,
        }

    def __getitem__(self, key: str) -> Any:
        return self._config_envs.get(key)


class TestingConfig(Config):
    def __init__(self, configs_dict, *args, **kwargs):
        self._configs_dict = configs_dict

    def __getitem__(self, key: str) -> Any:
        return self._configs_dict.get(key)
