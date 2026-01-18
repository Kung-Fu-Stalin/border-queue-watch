from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from src.utils.settings import settings


def checkpoint_keyboard():
    """Inline keyboard for checkpoint selection (registration)."""
    checkpoints = settings.CHECKPOINTS.keys()
    keyboard = [
        [
            InlineKeyboardButton(str(item).capitalize(), callback_data=item)
            for item in checkpoints
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def interval_unit_keyboard():
    """Inline keyboard for interval unit selection (registration)."""
    intervals = settings.WAIT_TIME.keys()
    keyboard = [
        [
            InlineKeyboardButton(
                str(item).capitalize(), callback_data=f"interval:unit:{item}"
            )
            for item in intervals
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def interval_value_keyboard(unit: str):
    """Inline keyboard for interval value selection (registration)."""
    values = settings.WAIT_TIME
    keyboard = [
        [
            InlineKeyboardButton(
                f"{value} {unit}", callback_data=f"interval:value:{unit}:{value}"
            )
        ]
        for value in values[unit]
    ]

    keyboard.append([InlineKeyboardButton("<- back", callback_data="interval:back")])
    return InlineKeyboardMarkup(keyboard)


# Settings modification keyboards (post-registration)
def settings_keyboard():
    keyboard = [
        # TODO: Move to buttons.json
        ["Изменить переход"],
        ["Изменить интервал"],
        ["Остановить мониторинг"],
        ["Мои настройки"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def checkpoint_settings_keyboard():
    checkpoints = settings.CHECKPOINTS.keys()
    keyboard = [[str(item).capitalize() for item in checkpoints], ["<- back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def interval_unit_settings_keyboard():
    """Reply keyboard for interval unit change (post-registration)."""
    intervals = settings.WAIT_TIME.keys()
    keyboard = [
        [str(item).capitalize() for item in intervals],
        ["<- back"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
