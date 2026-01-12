import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

from utils import settings, get_logger

logger = get_logger(__name__, silence=False)


class NotificationScheduler:

    def __init__(self, app: Application):
        self.app = app
        self.tasks: dict[int, asyncio.Task] = {}

    def add_user(self, user_id: int, interval_seconds: int):
        self.remove_user(user_id)

        task = asyncio.create_task(
            self._user_loop(user_id, interval_seconds),
            name=f"user_scheduler_{user_id}",
        )
        self.tasks[user_id] = task

        logger.info(f"User {user_id} scheduled with interval {interval_seconds}s")

        self.show_tasks()

    def remove_user(self, user_id: int):
        task = self.tasks.pop(user_id, None)
        if task:
            task.cancel()
            logger.info(f"User {user_id} scheduler stopped")

    async def _user_loop(self, user_id: int, interval_seconds: int):
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                await self.send_notification(user_id)
        except asyncio.CancelledError:
            logger.info(f"Scheduler task cancelled for user {user_id}")

    async def send_notification(self, user_id: int):
        await self.app.bot.send_message(
            chat_id=user_id,
            text=f"⏰ Ваше напоминание! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )
        logger.info(f"Notification sent to user {user_id}")

    async def shutdown(self):
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        logger.info("All scheduler tasks stopped")

    def show_tasks(self):
        print(self.tasks)


scheduler: NotificationScheduler | None = None


async def handle_seconds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scheduler

    user = update.effective_user
    user_id = user.id
    user_name = user.username or "unknown"
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text(
            "❌ Пожалуйста, введите число секунд (например: 60)"
        )
        return

    seconds = int(text)

    if seconds < 1:
        await update.message.reply_text("❌ Интервал должен быть больше 0 секунд")
        return

    scheduler.add_user(user_id, seconds)

    await update.message.reply_text(
        f"✅ Принято! Вы будете получать уведомления каждые {seconds} секунд.\n\n"
        f"Чтобы изменить интервал, отправьте новое число."
    )

    logger.info(f"User @{user_name} (ID: {user_id}) set interval to {seconds}s")


async def post_init(application: Application):
    logger.info("Bot post_init completed")


async def post_shutdown(application: Application):
    global scheduler
    if scheduler:
        await scheduler.shutdown()


def main():
    global scheduler

    app = Application.builder().token(settings.TELEGRAM_TOKEN).build()

    scheduler = NotificationScheduler(app)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_seconds))

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    logger.info("Starting bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
