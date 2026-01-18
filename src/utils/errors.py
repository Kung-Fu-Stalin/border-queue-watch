# Puller exceptions
class BorderAPIError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class DataNotFoundError(BorderAPIError):
    pass


class InvalidTransportTypeError(BorderAPIError):
    def __init__(self, transport_type, valid_types):
        msg = (
            f"Invalid transport type: '{transport_type}'. "
            f"Valid types: {valid_types}"
        )
        super().__init__(msg)


# Settings Error
class SettingsError(Exception):
    pass


class YamlNotFoundError(SettingsError):
    def __init__(self, yaml_path):
        super().__init__(f"Config file not found: {yaml_path}")


class EnvNotFoundError(SettingsError):
    def __init__(self, env_path):
        super().__init__(f"Environment file not found: {env_path}")


class TokenNotFoundError(SettingsError):
    def __init__(self):
        super().__init__("Environment variable TELEGRAM_TOKEN is not set")


class ButtonsNotFoundError(SettingsError):
    def __init__(self, buttons_path):
        super().__init__(f"Buttons file not found: {buttons_path}")


class MessagesNotFoundError(SettingsError):
    def __init__(self, messages_path):
        super().__init__(f"Messages file not found: {messages_path}")


class IncorrectParseModeError(SettingsError):
    def __init__(self, parse_mode, available_modes):
        super().__init__(
            f"Incorrect parse mode: {parse_mode}! "
            f"Available modes: {available_modes}"
        )
