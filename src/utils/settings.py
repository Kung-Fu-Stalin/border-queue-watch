from pathlib import Path

from dynaconf import Dynaconf

from src.utils.errors import (
    YamlNotFoundError,
    EnvNotFoundError,
    TokenNotFoundError,
    ButtonsNotFoundError,
    MessagesNotFoundError,
    IncorrectParseModeError,
)

PROJECT_ROOT_DIR = Path(__file__).parent.parent.parent
SRC_DIR = Path(PROJECT_ROOT_DIR, "src")
CONFIG_DIR = Path(SRC_DIR, "config")
RESOURCES_DIR = Path(SRC_DIR, "resources")
ENV_PATH = Path(PROJECT_ROOT_DIR, ".env")
YAML_PATH = Path(CONFIG_DIR, "config.yml").resolve()
BUTTONS_PATH = Path(RESOURCES_DIR, "buttons.json").resolve()
MESSAGES_PATH = Path(RESOURCES_DIR, "messages.yaml").resolve()
PARSE_MODES = ("Markdown", "MarkdownV2")

if not YAML_PATH.exists():
    raise YamlNotFoundError(YAML_PATH)

if not ENV_PATH.exists():
    raise EnvNotFoundError(ENV_PATH)

if not BUTTONS_PATH.exists():
    raise ButtonsNotFoundError(BUTTONS_PATH)

if not MESSAGES_PATH.exists():
    raise MessagesNotFoundError(MESSAGES_PATH)


settings = Dynaconf(
    envvar_prefix=False,
    root_path=PROJECT_ROOT_DIR.resolve(),
    load_dotenv=True,
    settings_files=[YAML_PATH],
    env_files=[ENV_PATH],
)
settings.BUTTONS_PATH = BUTTONS_PATH
settings.MESSAGES_PATH = MESSAGES_PATH
settings.DATABASE_PATH = Path(PROJECT_ROOT_DIR, "db.sqlite")

if not settings.get("TELEGRAM_TOKEN"):
    raise TokenNotFoundError()

if settings.PARSE_MODE not in PARSE_MODES:
    raise IncorrectParseModeError(settings.PARSE_MODE, PARSE_MODES)
