from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def checkpoint_selector():
    keyboard = [
        [
            InlineKeyboardButton("Brest", callback_data="brest"),
            InlineKeyboardButton("Berestovica", callback_data="berestovica"),
            InlineKeyboardButton("Bruzgi", callback_data="bruzgi"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def notifications_selector():
    keyboard = [
        [
            InlineKeyboardButton("10 сек"),
            InlineKeyboardButton("15 сек"),
            InlineKeyboardButton("20 сек"),
            InlineKeyboardButton("30 сек"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def user_selector():
    keyboard = [
        [
            "Сменить пункт",
            "Сменить номер авто",
            "Сменить частоту уведомлений",
            "Получить данные с камеры",
        ]
    ]
    return ReplyKeyboardMarkup(keyboard)
