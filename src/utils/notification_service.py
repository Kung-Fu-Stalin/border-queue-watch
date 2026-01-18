import asyncio
from dataclasses import dataclass
from datetime import datetime

from telegram.ext import Application

from src.utils.logger import get_logger
from src.utils.puller import DataPuller
from src.utils.settings import settings
from src.utils.ui import messages_ui


logger = get_logger(__name__)


@dataclass
class UserScheduleData:
    """Data needed to send notifications to a user."""

    user_id: int
    checkpoint_name: str
    car_number: str


class NotificationScheduler:
    """Internal scheduler for managing periodic notifications."""

    def __init__(self, app: Application):
        self.app = app
        self.tasks: dict[int, asyncio.Task] = {}
        self.user_data: dict[int, UserScheduleData] = {}

    def add_user(
        self, user_id: int, interval_seconds: int, checkpoint_name: str, car_number: str
    ):
        """Add a user to the scheduler with specified interval."""
        self.remove_user(user_id)

        # Store user data for notifications
        self.user_data[user_id] = UserScheduleData(
            user_id=user_id, checkpoint_name=checkpoint_name, car_number=car_number
        )

        task = asyncio.create_task(
            self._user_loop(user_id, interval_seconds),
            name=f"user_scheduler_{user_id}",
        )
        self.tasks[user_id] = task

        logger.info(
            f"User {user_id} scheduled with interval {interval_seconds}s for {checkpoint_name}"
        )

    def remove_user(self, user_id: int):
        task = self.tasks.pop(user_id, None)
        self.user_data.pop(user_id, None)
        if task:
            task.cancel()
            logger.info(f"User {user_id} scheduler stopped")

    async def _user_loop(self, user_id: int, interval_seconds: int):
        """Main loop that sends periodic notifications to a user."""
        try:
            while True:
                await asyncio.sleep(interval_seconds)

                # Get user data
                user_data = self.user_data.get(user_id)
                if not user_data:
                    logger.warning(f"User {user_id} data not found, stopping scheduler")
                    break

                # Send notification
                try:
                    await self._send_notification(user_data)
                except Exception as e:
                    logger.error(f"Error sending notification to user {user_id}: {e}")

        except asyncio.CancelledError:
            logger.info(f"Scheduler task cancelled for user {user_id}")

    async def _send_notification(self, user_data: UserScheduleData):
        """Send notification for a user."""
        try:
            queue_data = await self._fetch_queue_data(user_data.checkpoint_name)
            message = self._build_message(user_data, queue_data)

            await self.app.bot.send_message(chat_id=user_data.user_id, text=message)
            logger.info(f"Notification sent to user {user_data.user_id}")
        except Exception as e:
            logger.error(f"Error in _send_notification: {e}")

    async def shutdown(self):
        """Stop all scheduled tasks."""
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        self.user_data.clear()
        logger.info("All scheduler tasks stopped")

    async def _fetch_queue_data(self, checkpoint_name: str) -> dict:
        """Fetch queue data from the border API."""
        try:
            checkpoint_id = settings.CHECKPOINTS.get(checkpoint_name)
            if not checkpoint_id:
                logger.warning(f"Unknown checkpoint: {checkpoint_name}")
                return {}

            puller = DataPuller(checkpoint_id)
            monitoring_data = puller.fetch_monitoring()
            return monitoring_data or {}
        except Exception as e:
            logger.error(
                f"Error fetching queue data for checkpoint {checkpoint_name}: {e}"
            )
            return {}

    def _build_message(self, user_data: UserScheduleData, queue_data: dict) -> str:
        """Build the notification message with all available information."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        queue_info = self._extract_queue_info(queue_data)

        return (
            f"{messages_ui.notification_title.format(checkpoint=user_data.checkpoint_name.capitalize())}\n"
            f"{messages_ui.notification_car_number.format(car_number=user_data.car_number)}\n"
            f"{messages_ui.notification_timestamp.format(timestamp=timestamp)}\n"
            f"{queue_info}"
        )

    def _extract_queue_info(self, data: dict) -> str:
        """Extract and format queue information from API response."""
        if not data:
            return messages_ui.notification_queue_unavailable

        try:
            queue_info = data.get("queue_info", {})
            if queue_info:
                length = queue_info.get("length", "N/A")
                wait_time = queue_info.get("wait_time", "N/A")
                return messages_ui.notification_queue_info.format(
                    length=length, wait_time=wait_time
                )

            return messages_ui.notification_queue_available
        except Exception as e:
            logger.warning(f"Error parsing queue data: {e}")
            return messages_ui.notification_queue_error


class NotificationService:
    """Service responsible for managing user notifications and scheduling."""

    def __init__(self, app: Application):
        self.app = app
        self.scheduler = NotificationScheduler(app)

    def add_user(
        self, user_id: int, interval_seconds: int, checkpoint_name: str, car_number: str
    ):
        """Register a user for notifications."""
        self.scheduler.add_user(user_id, interval_seconds, checkpoint_name, car_number)
        logger.info(f"User {user_id} registered for notifications")

    def remove_user(self, user_id: int):
        """Unregister a user from notifications."""
        self.scheduler.remove_user(user_id)
        logger.info(f"User {user_id} unregistered from notifications")

    async def shutdown(self):
        """Shutdown the notification service."""
        await self.scheduler.shutdown()
