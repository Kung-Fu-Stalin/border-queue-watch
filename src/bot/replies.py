from telegram import Update
from telegram.ext import CallbackContext

from src.bot.control import checkpoint_selector


async def select_checkpoint_reply(update: Update, context: CallbackContext) -> None:
    place = await update.message.reply_text(
        "Coose your destiny...",
        reply_markup=checkpoint_selector(),
    )
    print("--->", place)


async def start_cmd(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Добро пожаловать")
    await select_checkpoint_reply(update, context)
