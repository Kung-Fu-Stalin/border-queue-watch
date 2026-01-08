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
    update_time = IntegerField(null=False)
    checkpoint_name = CharField(null=False)

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
            logger.warning(f"database: {self.db_file} does not exist, creating")
            self.db.connect()
            self.db.close()

    def _ensure_tables(self):
        with DBConnectionContext(self.db):
            self.db.create_tables([Users], safe=True)
            logger.info(f"tables: {str(Users).split(" ")[-1][:-1]} created")

    def _ensure_columns(self):
        with DBConnectionContext(self.db):
            columns = [c.name for c in self.db.get_columns("users")]

            required_columns = {"telegram_user_name": "TEXT"}

            for col, col_type in required_columns.items():
                if col not in columns:
                    self.db.execute_sql(
                        f"ALTER TABLE users ADD COLUMN {col} {col_type};"
                    )

    def _get_user(self, telegram_user_id):
        try:
            logger.info(f"getting user: {telegram_user_id}")
            return Users.get(Users.telegram_user_id == telegram_user_id)
        except Users.DoesNotExist:
            logger.warning(
                f"user with telegram_user_id {telegram_user_id} does not exist"
            )
            return None

    def transaction(self):
        return self.db.atomic()

    def get_all_users(self):
        users = Users.select()
        users_list = [(u.telegram_user_id, u.telegram_user_name) for u in users]
        logger.info("a list of all users was received")
        return users_list

    def user_exists(self, telegram_user_id):
        # Add type check after investigation from TelegramAPI side
        if self._get_user(telegram_user_id):
            logger.info(f"user {telegram_user_id} exist")
            return True
        logger.info(f"user {telegram_user_id} does not exist")
        return False

    def add_user(
        self,
        telegram_user_id,
        update_time: int,
        checkpoint_name: str,
        telegram_user_name=None,
    ):
        if not isinstance(update_time, int):
            logger.error(f"incorrect incoming update_time: {update_time}")
            raise TypeError("update_time must be an integer")
        if not isinstance(checkpoint_name, str):
            logger.error(f"incorrect incoming checkpoint_name: {checkpoint_name}")
            raise TypeError("checkpoint_name must be a string")

        with self.transaction():
            if self.user_exists(telegram_user_id):
                return None
            logger.info(
                f"Creating user: "
                f"id:{telegram_user_id}, "
                f"name: {telegram_user_name}, "
                f"update_time:{update_time}, "
                f"checkpoint_name:{checkpoint_name}"
            )
            return Users.create(
                telegram_user_id=telegram_user_id,
                telegram_user_name=telegram_user_name,
                update_time=update_time,
                checkpoint_name=checkpoint_name,
            )

    def delete_user(self, telegram_user_id):
        with self.transaction():
            user = self._get_user(telegram_user_id)
            if not user:
                logger.warning(f"user {telegram_user_id} does not exist")
                return False
            logger.info(f"deleting user: {telegram_user_id}")
            return user.delete_instance(recursive=True)

    def clear_all(self):
        with self.transaction():
            Users.delete().execute()
        logger.warning("all users were deleted")


db_manager = DatabaseManager(settings.DATABASE_PATH)
