"""Keyboard builders for Telegram bot UI.

This module provides functions to create inline and reply keyboards for:
- Registration flow (checkpoint, interval, confirmation)
- Settings management (updating checkpoint and interval)
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from src.utils.settings import settings


def checkpoint_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for checkpoint selection during registration.

    Returns:
        InlineKeyboardMarkup with checkpoint options
    """
    checkpoints = settings.CHECKPOINTS.keys()
    keyboard = [
        [
            InlineKeyboardButton(str(item).capitalize(), callback_data=item)
            for item in checkpoints
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def checkpoint_update_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for checkpoint change in settings.

    Returns:
        InlineKeyboardMarkup with checkpoint options
    """
    checkpoints = settings.CHECKPOINTS.keys()
    keyboard = [
        [
            InlineKeyboardButton(
                str(item).capitalize(), callback_data=f"update:checkpoint:{item}"
            )
            for item in checkpoints
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def interval_unit_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for time unit selection (registration).

    Returns:
        InlineKeyboardMarkup with unit options (seconds/minutes/hours)
    """
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


def interval_unit_keyboard_update() -> InlineKeyboardMarkup:
    """Create inline keyboard for time unit selection (settings update).

    Returns:
        InlineKeyboardMarkup with unit options
    """
    intervals = settings.WAIT_TIME.keys()
    keyboard = [
        [
            InlineKeyboardButton(
                str(item).capitalize(), callback_data=f"update:interval:unit:{item}"
            )
            for item in intervals
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def interval_value_keyboard(unit: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for interval value selection (registration).

    Args:
        unit: Time unit key (secs, mins, hours)

    Returns:
        InlineKeyboardMarkup with available values for selected unit
    """
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


def interval_value_update_keyboard(unit: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for interval value selection (settings update).

    Args:
        unit: Time unit key (secs, mins, hours)

    Returns:
        InlineKeyboardMarkup with available values for selected unit
    """
    values = settings.WAIT_TIME
    keyboard = [
        [
            InlineKeyboardButton(
                f"{value} {unit}", callback_data=f"update:interval:value:{unit}:{value}"
            )
        ]
        for value in values[unit]
    ]

    keyboard.append(
        [InlineKeyboardButton("<- back", callback_data="update:interval:back")]
    )
    return InlineKeyboardMarkup(keyboard)


def car_number_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for car number confirmation.

    Returns:
        InlineKeyboardMarkup with Yes/No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="confirm_car:yes"),
            InlineKeyboardButton("❌ Нет", callback_data="confirm_car:no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def resume_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for resume confirmation.

    Returns:
        InlineKeyboardMarkup with Continue/Cancel buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Продолжить", callback_data="resume:continue"),
            InlineKeyboardButton("❌ Отмена", callback_data="resume:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard() -> ReplyKeyboardMarkup:
    """Create reply keyboard for active user settings menu.

    Returns:
        ReplyKeyboardMarkup with control options
    """
    keyboard = [
        ["Изменить переход", "Изменить интервал"],
        ["Мои настройки", "Остановить мониторинг"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def checkpoint_settings_keyboard() -> ReplyKeyboardMarkup:
    """Create reply keyboard for checkpoint selection in settings.

    Returns:
        ReplyKeyboardMarkup with checkpoint options
    """
    checkpoints = settings.CHECKPOINTS.keys()
    keyboard = [[str(item).capitalize() for item in checkpoints], ["<- back"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def interval_unit_settings_keyboard() -> ReplyKeyboardMarkup:
    """Create reply keyboard for interval unit selection in settings.

    Returns:
        ReplyKeyboardMarkup with time unit options
    """
    intervals = settings.WAIT_TIME.keys()
    keyboard = [
        [str(item).capitalize() for item in intervals],
        ["<- back"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
