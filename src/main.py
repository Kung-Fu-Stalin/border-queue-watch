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
from utils.notification_service import NotificationService
from bot.commands import (
    start_cmd,
    stop_cmd,
    exit_cmd,
)
from bot.handlers import (
    checkpoint_callback_handler,
    car_number_callback_handler,
    interval_unit_callback_handler,
    interval_value_callback_handler,
)


logger = get_logger(__name__)


def main():
    logger.info("Starting bot...")
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    # Initialize notification service (includes scheduler)
    app.bot_data["notification_service"] = NotificationService(app)

    # Add handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("exit", exit_cmd))
    app.add_handler(
        CallbackQueryHandler(checkpoint_callback_handler, pattern="^[a-z_]+$")
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, car_number_callback_handler)
    )
    app.add_handler(
        CallbackQueryHandler(interval_unit_callback_handler, pattern="^interval:unit:")
    )
    app.add_handler(
        CallbackQueryHandler(
            interval_value_callback_handler, pattern="^interval:value:"
        )
    )

    logger.info("Bot listening...")
    app.run_polling()


if __name__ == "__main__":
    main()
