from telegram import Update
from telegram.ext import ContextTypes

from src.utils import messages_ui
from src.bot.control import (
    checkpoint_keyboard,
    interval_unit_keyboard,
    interval_value_keyboard,
)


async def select_checkpoint_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(
        messages_ui.choose_checkpoint,
        reply_markup=checkpoint_keyboard(),
    )


async def enter_car_number_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(messages_ui.enter_car_number)


async def select_interval_unit_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.effective_chat.send_message(
        messages_ui.choose_interval_unit,
        reply_markup=interval_unit_keyboard(),
    )


async def select_interval_value_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE, unit: str
) -> None:
    await update.effective_chat.send_message(
        messages_ui.choose_interval_value.format(unit=unit.capitalize()),
        reply_markup=interval_value_keyboard(unit),
    )
