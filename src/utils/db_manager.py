from pathlib import Path

from peewee import (
    SQL,
    Model,
    CharField,
    IntegerField,
    DateTimeField,
    SqliteDatabase,
)

from src.utils.settings import settings
from src.utils.logger import get_logger


logger = get_logger(__name__)

db = SqliteDatabase(settings.DATABASE_PATH)


class Users(Model):
    telegram_user_id = CharField(unique=True)
    telegram_user_name = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    car_number = CharField(null=False)
    interval_seconds = IntegerField(null=False)
    checkpoint_name = CharField(null=False)
    is_active = IntegerField(null=False, default=1)  # 1 = active, 0 = paused

    class Meta:
        database = db
        table_name = "users"


class DBConnectionContext:
    def __init__(self, database: SqliteDatabase):
        self.db = database

    def __enter__(self):
        if self.db.is_closed():
            self.db.connect()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.db.is_closed():
            self.db.close()


class DatabaseManager:
    def __init__(self, db_file: Path | str):
        self.db_file = db_file
        self.db = db
        self._ensure_database()
        self._ensure_tables()
        self._ensure_columns()

    def _ensure_database(self):
        if not Path(self.db_file):
            logger.warning(f"Database: {self.db_file} does not exist, creating")
            self.db.connect()
            self.db.close()

    def _ensure_tables(self):
        with DBConnectionContext(self.db):
            models = [Users]
            self.db.create_tables(models, safe=True)

    def _ensure_columns(self):
        with DBConnectionContext(self.db):
            columns = [c.name for c in self.db.get_columns("users")]

            required_columns = {
                "telegram_user_name": "TEXT",
                "is_active": "INTEGER DEFAULT 1",
            }

            for col, col_type in required_columns.items():
                if col not in columns:
                    self.db.execute_sql(
                        f"ALTER TABLE users ADD COLUMN {col} {col_type};"
                    )

    @staticmethod
    def _get_user(telegram_user_id: int) -> Users | None:
        """Retrieve user from database by ID.

        Args:
            telegram_user_id: Telegram user ID

        Returns:
            Users instance if found, None otherwise
        """
        try:
            logger.debug(f"Fetching user {telegram_user_id}")
            return Users.get(Users.telegram_user_id == telegram_user_id)
        except Users.DoesNotExist:
            logger.debug(f"User {telegram_user_id} does not exist")
            return None

    def transaction(self):
        return self.db.atomic()

    def get_all_users(self) -> list[tuple[int, str | None]]:
        """Get all registered users.

        Returns:
            List of tuples (user_id, username)
        """
        users = Users.select()
        users_list = [(u.telegram_user_id, u.telegram_user_name) for u in users]
        logger.debug(f"Retrieved {len(users_list)} users from database")
        return users_list

    def user_exists(self, telegram_user_id: int) -> bool:
        """Check if user exists in database.

        Args:
            telegram_user_id: Telegram user ID to check

        Returns:
            True if user exists, False otherwise
        """
        user = self._get_user(telegram_user_id)
        if user:
            logger.debug(f"User {telegram_user_id} found")
            return True
        logger.debug(f"User {telegram_user_id} not found")
        return False

    def add_user(
        self,
        telegram_user_id: int,
        interval_seconds: int,
        checkpoint_name: str,
        car_number: str,
        telegram_user_name: str | None = None,
    ) -> Users | None:
        """Create a new user in the database.

        Args:
            telegram_user_id: Unique Telegram user ID
            interval_seconds: Monitoring interval in seconds
            checkpoint_name: Border checkpoint name
            car_number: Vehicle registration number
            telegram_user_name: Optional Telegram username

        Returns:
            Created Users instance or None if user already exists

        Raises:
            TypeError: If parameter types are incorrect
        """
        # Validate parameter types
        self._validate_user_params(interval_seconds, checkpoint_name, car_number)

        with self.transaction():
            if self.user_exists(telegram_user_id):
                logger.warning(f"User {telegram_user_id} already exists")
                return None

            logger.info(
                f"Creating user {telegram_user_id}: "
                f"checkpoint={checkpoint_name}, car={car_number}, interval={interval_seconds}s"
            )
            return Users.create(
                telegram_user_id=telegram_user_id,
                telegram_user_name=telegram_user_name,
                interval_seconds=interval_seconds,
                checkpoint_name=checkpoint_name,
                car_number=car_number,
            )

    def _validate_user_params(
        self, interval_seconds: int, checkpoint_name: str, car_number: str
    ) -> None:
        """Validate user parameters.

        Raises:
            TypeError: If any parameter has incorrect type
        """
        if not isinstance(interval_seconds, int):
            raise TypeError(
                f"interval_seconds must be int, got {type(interval_seconds)}"
            )
        if not isinstance(checkpoint_name, str):
            raise TypeError(f"checkpoint_name must be str, got {type(checkpoint_name)}")
        if not isinstance(car_number, str):
            raise TypeError(f"car_number must be str, got {type(car_number)}")

    def delete_user(self, telegram_user_id: int) -> bool:
        """Delete user and all associated data.

        Args:
            telegram_user_id: Telegram user ID to delete

        Returns:
            True if deletion was successful, False if user not found
        """
        with self.transaction():
            user = self._get_user(telegram_user_id)
            if not user:
                logger.warning(f"Cannot delete: user {telegram_user_id} not found")
                return False
            logger.info(f"Deleting user {telegram_user_id}")
            return user.delete_instance(recursive=True)

    def clear_all(self):
        with self.transaction():
            Users.delete().execute()
        logger.warning("All users were deleted")

    def get_user(self, telegram_user_id: int) -> dict | None:
        """Get user data by Telegram ID.

        Args:
            telegram_user_id: Telegram user ID

        Returns:
            Dictionary with user data or None if not found
        """
        user = self._get_user(telegram_user_id)
        if not user:
            return None

        return {
            "id": user.telegram_user_id,
            "name": user.telegram_user_name,
            "car_number": user.car_number,
            "interval_seconds": user.interval_seconds,
            "checkpoint_name": user.checkpoint_name,
            "is_active": bool(user.is_active),
            "created_at": user.created_at,
        }

    def set_user_active(self, telegram_user_id: int, is_active: bool) -> bool:
        """Activate or deactivate user monitoring.

        Args:
            telegram_user_id: Telegram user ID
            is_active: True to activate, False to pause

        Returns:
            True if successful, False if user not found
        """
        with self.transaction():
            user = self._get_user(telegram_user_id)
            if not user:
                return False

            user.is_active = 1 if is_active else 0
            user.save()
            status = "activated" if is_active else "paused"
            logger.info(f"User {telegram_user_id} {status}")
            return True

    def get_user_status(self, telegram_user_id: int) -> bool | None:
        """Get user monitoring status.

        Args:
            telegram_user_id: Telegram user ID

        Returns:
            True if active, False if paused, None if user not found
        """
        user = self._get_user(telegram_user_id)
        if user:
            return bool(user.is_active)
        return None

    def update_user(
        self,
        telegram_user_id: int,
        checkpoint_name: str | None = None,
        interval_seconds: int | None = None,
        car_number: str | None = None,
    ) -> bool:
        """Update user settings.

        Args:
            telegram_user_id: Telegram user ID
            checkpoint_name: New checkpoint name (optional)
            interval_seconds: New interval in seconds (optional)
            car_number: New car number (optional)

        Returns:
            True if successful, False if user not found
        """
        with self.transaction():
            user = self._get_user(telegram_user_id)
            if not user:
                logger.warning(f"Cannot update: user {telegram_user_id} not found")
                return False

            if checkpoint_name is not None:
                user.checkpoint_name = checkpoint_name
            if interval_seconds is not None:
                user.interval_seconds = interval_seconds
            if car_number is not None:
                user.car_number = car_number

            user.save()
            logger.info(f"User {telegram_user_id} updated successfully")
            return True


db_manager = DatabaseManager(settings.DATABASE_PATH)
