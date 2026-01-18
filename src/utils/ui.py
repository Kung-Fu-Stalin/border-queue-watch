import json
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.utils.settings import settings


class UIObjectsBase(ABC):
    def __init__(self, filepath: Path | str):
        self.filepath = Path(filepath)
        self.data = self._open_file()
        self._set_attributes()

    @abstractmethod
    def _open_file(self) -> dict[str, Any]:
        pass

    def _set_attributes(self) -> None:
        for key, value in self.data.items():
            setattr(self, key, value)


class JSONUIObjects(UIObjectsBase):
    def _open_file(self) -> dict[str, Any]:
        with open(self.filepath, "r", encoding="utf-8") as file:
            return json.load(file)


class YAMLUIObjects(UIObjectsBase):
    def _open_file(self) -> dict[str, Any]:
        with open(self.filepath, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)


class UIObjectsFactory:
    _registry = {
        ".json": JSONUIObjects,
        ".yaml": YAMLUIObjects,
        ".yml": YAMLUIObjects,
    }

    @classmethod
    def create(cls, filepath: Path | str) -> UIObjectsBase:
        path = Path(filepath)
        try:
            ui_class = cls._registry[path.suffix.lower()]
        except KeyError:
            raise ValueError(f"Unsupported UI objects format: {path.suffix}")

        return ui_class(path)


messages_ui = UIObjectsFactory.create(settings.MESSAGES_PATH)
buttons_ui = UIObjectsFactory.create(settings.BUTTONS_PATH)
