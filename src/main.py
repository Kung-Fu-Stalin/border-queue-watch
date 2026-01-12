from telegram.ext import (
    Application,
    CommandHandler,
)

from utils import settings
from bot.replies import start_cmd


def main():
    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
