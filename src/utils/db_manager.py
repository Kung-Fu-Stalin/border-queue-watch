from peewee import (
    SQL,
    Model,
    CharField,
    IntegerField,
    DateTimeField,
    SqliteDatabase,
)
from pathlib import Path

from src.utils.settings import settings


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
            self.db.connect()
            self.db.close()

    def _ensure_tables(self):
        with DBConnectionContext(self.db):
            self.db.create_tables([Users], safe=True)

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
            return Users.get(Users.telegram_user_id == telegram_user_id)
        except Users.DoesNotExist:
            return None

    def transaction(self):
        return self.db.atomic()

    def get_all_users(self):
        users = Users.select()
        users_list = [(u.telegram_user_id, u.telegram_user_name) for u in users]
        return users_list

    def user_exists(self, telegram_user_id):
        # Add type check after investigation from TelegramAPI side
        return self._get_user(telegram_user_id) is not None

    def add_user(
        self,
        telegram_user_id,
        update_time: int,
        checkpoint_name: str,
        telegram_user_name=None,
    ):
        if not isinstance(update_time, int):
            raise TypeError("update_time must be an integer")
        if not isinstance(checkpoint_name, str):
            raise TypeError("checkpoint_name must be a string")

        with self.transaction():
            if self.user_exists(telegram_user_id):
                return None
            # Need to change
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
                return False
            return user.delete_instance(recursive=True)

    def clear_all(self):
        with self.transaction():
            Users.delete().execute()


db_manager = DatabaseManager(settings.DATABASE_PATH)
