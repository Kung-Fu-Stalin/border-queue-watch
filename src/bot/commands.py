from telegram import Update
from telegram.ext import ContextTypes

from src.bot.replies import select_checkpoint_reply
from src.bot.control import settings_keyboard
from src.utils import db_manager, get_logger
from src.utils.ui import messages_ui


logger = get_logger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command.

    If user already registered: show their settings
    If user is paused: offer to resume
    If new user: start registration flow
    """
    user_id = update.effective_user.id

    # Check if user already registered
    if db_manager.user_exists(user_id):
        user_status = db_manager.get_user_status(user_id)
        user_data = db_manager.get_user(user_id)
        interval_str = (
            f"{user_data['interval_seconds'] // 60} мин"
            if user_data["interval_seconds"] >= 60
            else f"{user_data['interval_seconds']} сек"
        )

        # If user is active (monitoring running)
        if user_status:
            message = messages_ui.registered_menu.format(
                car_number=user_data["car_number"],
                checkpoint=user_data["checkpoint_name"].capitalize(),
                interval=interval_str,
            )
            await update.message.reply_text(
                message,
                reply_markup=settings_keyboard(),
            )
        else:
            # If user is paused (monitoring stopped)
            from src.bot.replies import resume_confirmation_reply

            await resume_confirmation_reply(
                update,
                context,
                car_number=user_data["car_number"],
                checkpoint=user_data["checkpoint_name"].capitalize(),
                interval=interval_str,
            )
        return

    # Start registration flow for new user
    await select_checkpoint_reply(update, context)


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command - pause monitoring without deleting user data."""
    user_id = update.effective_user.id

    # Check if user exists
    if not db_manager.user_exists(user_id):
        await update.message.reply_text(messages_ui.user_not_found)
        return

    # Set user as inactive (paused)
    db_manager.set_user_active(user_id, False)

    # Remove user from notification service
    notification_service = context.application.bot_data.get("notification_service")
    if notification_service:
        notification_service.remove_user(user_id)
        logger.info(f"User {user_id} stopped monitoring")

    await update.message.reply_text(messages_ui.monitoring_stopped)


async def exit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /exit command - remove all user data and exit."""
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
