from telegram import Update
from telegram.ext import ContextTypes

from src.bot.replies import select_checkpoint_reply
from src.utils import db_manager, get_logger
from src.utils.ui import messages_ui


logger = get_logger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    # Check if user already registered
    if db_manager.user_exists(user_id):
        await update.message.reply_text(messages_ui.user_exists)
        return

    # Start registration flow
    await select_checkpoint_reply(update, context)


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop command - pause monitoring without deleting user data."""
    user_id = update.effective_user.id

    # Check if user exists
    if not db_manager.user_exists(user_id):
        await update.message.reply_text(messages_ui.user_not_found)
        return

    # Remove user from notification service
    notification_service = context.application.bot_data.get("notification_service")
    if notification_service:
        notification_service.remove_user(user_id)
        logger.info(f"User {user_id} stopped monitoring")

    await update.message.reply_text(messages_ui.monitoring_stopped)


async def exit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exit command - remove all user data and exit."""
    user_id = update.effective_user.id

    # Check if user exists
    if not db_manager.user_exists(user_id):
        await update.message.reply_text(messages_ui.user_not_found)
        return

    try:
        # Remove user from notification service
        notification_service = context.application.bot_data.get("notification_service")
        if notification_service:
            notification_service.remove_user(user_id)

        # Delete user from database
        db_manager.delete_user(user_id)
        logger.info(f"User {user_id} deleted all data and exited")

        await update.message.reply_text(messages_ui.user_deleted)
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        await update.message.reply_text(messages_ui.deletion_error.format(error=str(e)))
