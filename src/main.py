"""Main entry point for Border Queue Watch Telegram bot.

This bot monitors border crossing queue status and sends periodic
notifications to users with their current waiting times.
"""

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from utils import (
    settings,
    get_logger,
)
from utils.notification_service import NotificationScheduler
from bot.commands import (
    start_cmd,
    stop_cmd,
    exit_cmd,
)
from bot.handlers import (
    checkpoint_callback_handler,
    car_number_callback_handler,
    confirm_car_number_callback_handler,
    resume_menu_callback_handler,
    interval_unit_callback_handler,
    interval_value_callback_handler,
    settings_menu_handler,
    update_checkpoint_callback_handler,
    update_interval_unit_callback_handler,
    update_interval_value_callback_handler,
)


logger = get_logger(__name__)


def _setup_handlers(app: Application) -> None:
    """Setup all message and callback handlers.

    Args:
        app: Telegram Application instance
    """
    # Command handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("exit", exit_cmd))

    # Settings menu (must come before car_number handler to catch button presses)
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & (filters.Regex("Изменить|Мои настройки|Остановить мониторинг")),
            settings_menu_handler,
        )
    )

    # Registration flow callbacks
    app.add_handler(
        CallbackQueryHandler(checkpoint_callback_handler, pattern="^[a-z_]+$")
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, car_number_callback_handler)
    )
    app.add_handler(
        CallbackQueryHandler(
            confirm_car_number_callback_handler, pattern="^confirm_car:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(resume_menu_callback_handler, pattern="^resume:")
    )
    app.add_handler(
        CallbackQueryHandler(interval_unit_callback_handler, pattern="^interval:unit:")
    )
    app.add_handler(
        CallbackQueryHandler(
            interval_value_callback_handler, pattern="^interval:value:"
        )
    )

    # Settings update callbacks (for active users)
    app.add_handler(
        CallbackQueryHandler(
            update_checkpoint_callback_handler, pattern="^update:checkpoint:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            update_interval_unit_callback_handler, pattern="^update:interval:unit:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            update_interval_value_callback_handler, pattern="^update:interval:value:"
        )
    )


def main() -> None:
    """Start the Telegram bot."""
    logger.info("Initializing Border Queue Watch bot...")

    # Create application
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Initialize notification scheduler
    notification_scheduler = NotificationScheduler(app)
    app.bot_data["notification_service"] = notification_scheduler

    # Setup handlers
    _setup_handlers(app)

    logger.info("Bot started. Listening for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
