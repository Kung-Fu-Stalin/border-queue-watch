# Puller exceptions
class BorderAPIError(Exception):
    pass


class DataNotFoundError(BorderAPIError):
    pass


class InvalidTransportTypeError(BorderAPIError):
    pass


# Settings Error
class SettingsError(Exception):
    pass


# DB Error
class DBError(Exception):
    pass
