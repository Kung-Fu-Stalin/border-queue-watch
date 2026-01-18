from telegram import Update
from telegram.ext import ContextTypes

from src.utils import db_manager, messages_ui, get_logger
from src.utils.registration_state import RegistrationStateManager
from src.bot.settings_menu import SettingsMenuBuilder
from src.bot.control import (
    interval_unit_keyboard,
    interval_unit_keyboard_update,
    interval_value_keyboard,
    interval_value_update_keyboard,
    car_number_confirmation_keyboard,
    checkpoint_update_keyboard,
)

logger = get_logger(__name__)

# Time unit to seconds conversion mapping
UNIT_TO_SECONDS = {"secs": 1, "mins": 60, "hours": 3600}


class UserSettingsFormatter:
    """Helper class to format user settings for display."""

    @staticmethod
    def format_interval(interval_seconds: int) -> str:
        """Format interval in seconds to readable string.

        Args:
            interval_seconds: Interval in seconds

        Returns:
            Formatted string like "5 мин" or "30 сек"
        """
        if interval_seconds >= 60:
            minutes = interval_seconds // 60
            return f"{minutes} мин"
        return f"{interval_seconds} сек"

    @staticmethod
    def get_user_settings_message(user_data: dict, include_status: bool = False) -> str:
        """Build formatted user settings message.

        Args:
            user_data: User data dictionary from db_manager
            include_status: Whether to include active/paused status

        Returns:
            Formatted message string
        """
        interval_str = UserSettingsFormatter.format_interval(
            user_data["interval_seconds"]
        )

        message_lines = [
            f"📍 Переход: {user_data['checkpoint_name'].capitalize()}",
            f"🚗 Номер авто: {user_data['car_number']}",
            f"⏱️ Интервал проверки: {interval_str}",
        ]

        if include_status:
            status = "🟢 Активен" if user_data["is_active"] else "🔴 Приостановлен"
            message_lines.append(f"🔄 Статус: {status}")

        return "\n".join(message_lines)


class NotificationServiceHelper:
    """Helper class for notification service operations."""

    @staticmethod
    def get_notification_service(context):
        """Safely get notification service from context.

        Args:
            context: Telegram context

        Returns:
            NotificationService instance or None
        """
        return context.application.bot_data.get("notification_service")

    @staticmethod
    def re_register_user(notification_service, user_id: int, user_data: dict) -> None:
        """Re-register user in notification service with updated data.

        Args:
            notification_service: NotificationService instance
            user_id: Telegram user ID
            user_data: User data dictionary from db_manager
        """
        if not notification_service:
            return

        # Remove old registration
        notification_service.remove_user(user_id)

        # Add with new data
        notification_service.add_user(
            user_id=user_id,
            interval_seconds=user_data["interval_seconds"],
            checkpoint_name=user_data["checkpoint_name"],
            car_number=user_data["car_number"],
        )


async def checkpoint_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle border checkpoint selection during registration."""
    query = update.callback_query
    await query.answer()

    checkpoint_name = query.data
    user_id = update.effective_user.id

    # Get or create registration state
    state = RegistrationStateManager.get(context.user_data)
    state.checkpoint_name = checkpoint_name
    RegistrationStateManager.save(context.user_data, state)

    logger.info(f"User {user_id} selected checkpoint: {checkpoint_name}")

    # Confirm selection
    await query.edit_message_text(text=f"✅ Переход: {checkpoint_name.capitalize()}")

    # Show progress menu
    menu_msg = SettingsMenuBuilder.get_progress_message(state)
    await update.effective_chat.send_message(menu_msg)

    # Ask for car number
    await update.effective_chat.send_message(messages_ui.enter_car_number)


async def car_number_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle car number input during registration."""
    car_number = update.message.text.strip().upper()
    user_id = update.effective_user.id

    # Validate
    if not car_number:
        await update.message.reply_text(messages_ui.invalid_car_number)
        return

    # Save temporarily for confirmation
    context.user_data["temp_car_number"] = car_number

    logger.info(f"User {user_id} entered car number: {car_number}")

    # Show confirmation
    await update.message.reply_text(
        messages_ui.confirm_car_number.format(car_number=car_number),
        reply_markup=car_number_confirmation_keyboard(),
    )


async def confirm_car_number_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle car number confirmation."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    temp_car_number = context.user_data.get("temp_car_number")

    if not temp_car_number:
        await query.edit_message_text(text=messages_ui.incomplete_data)
        return

    if query.data == "confirm_car:yes":
        # Confirmed - save to state
        state = RegistrationStateManager.get(context.user_data)
        state.car_number = temp_car_number
        RegistrationStateManager.save(context.user_data, state)

        del context.user_data["temp_car_number"]
        logger.info(f"User {user_id} confirmed car number: {temp_car_number}")

        await query.edit_message_text(text=messages_ui.car_number_confirmed)

        # Show progress
        menu_msg = SettingsMenuBuilder.get_progress_message(state)
        await update.effective_chat.send_message(menu_msg)

        # Ask to select interval
        await update.effective_chat.send_message(
            messages_ui.choose_interval_unit,
            reply_markup=interval_unit_keyboard(),
        )

    elif query.data == "confirm_car:no":
        # Rejected - ask for new number
        del context.user_data["temp_car_number"]
        logger.info(f"User {user_id} rejected car number: {temp_car_number}")

        await query.edit_message_text(text=messages_ui.car_number_rejected)
        await update.effective_chat.send_message(messages_ui.enter_car_number)


async def interval_unit_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle time unit selection (seconds/minutes/hours)."""
    query = update.callback_query
    await query.answer()

    interval_unit = query.data.split(":")[-1]
    user_id = update.effective_user.id

    state = RegistrationStateManager.get(context.user_data)
    state.interval_unit = interval_unit
    RegistrationStateManager.save(context.user_data, state)

    logger.info(f"User {user_id} selected interval unit: {interval_unit}")

    await query.edit_message_text(text=messages_ui.choose_interval_unit)

    # Show available values for selected unit
    await update.effective_chat.send_message(
        messages_ui.choose_interval_value.format(unit=interval_unit.capitalize()),
        reply_markup=interval_value_keyboard(interval_unit),
    )


async def interval_value_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle interval value selection during registration.

    After selection, saves the user to database and starts monitoring.
    """
    query = update.callback_query
    await query.answer()

    callback_parts = query.data.split(":")
    interval_unit = callback_parts[2]
    interval_value = int(callback_parts[3])

    user_id = update.effective_user.id
    user_name = update.effective_user.username or "noUsername"

    # Get complete registration state
    state = RegistrationStateManager.get(context.user_data)
    state.interval_unit = interval_unit
    state.interval_value = interval_value
    RegistrationStateManager.save(context.user_data, state)

    if not state.is_complete():
        await query.edit_message_text(text=messages_ui.incomplete_data)
        logger.warning(f"User {user_id} registration incomplete: {state}")
        return

    # Convert interval to seconds
    interval_seconds = interval_value * UNIT_TO_SECONDS.get(interval_unit, 1)

    try:
        # Save to database
        if db_manager.user_exists(user_id):
            logger.warning(f"User {user_id} already exists in database")
            await query.edit_message_text(text=messages_ui.user_exists)
            return

        db_manager.add_user(
            telegram_user_id=user_id,
            telegram_user_name=user_name,
            interval_seconds=interval_seconds,
            car_number=state.car_number,
            checkpoint_name=state.checkpoint_name,
        )
        logger.info(f"User {user_id} registration completed and saved")

        # Register for notifications
        notification_service = NotificationServiceHelper.get_notification_service(
            context
        )
        if notification_service:
            notification_service.add_user(
                user_id=user_id,
                interval_seconds=interval_seconds,
                checkpoint_name=state.checkpoint_name,
                car_number=state.car_number,
            )
            logger.info(f"User {user_id} registered for notifications")

        # Show success message
        final_progress = SettingsMenuBuilder.get_progress_message(state)
        await query.edit_message_text(text=final_progress)

        success_msg = messages_ui.user_created.format(
            car_number=state.car_number,
            checkpoint=state.checkpoint_name.capitalize(),
            value=interval_value,
            unit=interval_unit,
        )
        await update.effective_chat.send_message(success_msg)

        # Clear registration state
        RegistrationStateManager.clear(context.user_data)

        # Show active user menu
        from src.bot.control import settings_keyboard

        await update.effective_chat.send_message(
            "✅ Регистрация завершена! Используйте меню ниже для управления:",
            reply_markup=settings_keyboard(),
        )

    except Exception as e:
        logger.error(f"Error saving user {user_id}: {e}")
        await query.edit_message_text(
            text=messages_ui.registration_error.format(error=str(e))
        )

    # Конвертировать интервал в секунды
    unit_multipliers = {"secs": 1, "mins": 60, "hours": 3600}
    interval_seconds = interval_value * unit_multipliers.get(interval_unit, 1)

    try:
        # Проверить, не существует ли уже пользователь
        if db_manager.user_exists(user_id):
            logger.warning(f"User {user_id} already exists in database")
            await query.edit_message_text(text=messages_ui.user_exists)
            return

        # Сохранить пользователя в БД
        db_manager.add_user(
            telegram_user_id=user_id,
            telegram_user_name=user_name,
            interval_seconds=interval_seconds,
            car_number=state.car_number,
            checkpoint_name=state.checkpoint_name,
        )
        logger.info(f"User {user_id} saved to database")

        # Зарегистрировать для отправки уведомлений
        notification_service = context.application.bot_data.get("notification_service")
        if notification_service:
            notification_service.add_user(
                user_id=user_id,
                interval_seconds=interval_seconds,
                checkpoint_name=state.checkpoint_name,
                car_number=state.car_number,
            )
            logger.info(f"User {user_id} registered for notifications")

        # Показать сообщение об успехе
        success_msg = messages_ui.user_created.format(
            car_number=state.car_number,
            checkpoint=state.checkpoint_name.capitalize(),
            value=interval_value,
            unit=interval_unit,
        )
        await update.effective_chat.send_message(success_msg)

        # Очистить состояние регистрации
        RegistrationStateManager.clear(context.user_data)

        # Показать меню активного пользователя с опциями управления
        from src.bot.control import settings_keyboard

        menu_text = "✅ Регистрация завершена! Используйте меню ниже для управления:"
        await update.effective_chat.send_message(
            menu_text,
            reply_markup=settings_keyboard(),
        )

    except Exception as e:
        logger.error(f"Error saving user {user_id}: {e}")
        await query.edit_message_text(
            text=messages_ui.registration_error.format(error=str(e))
        )


async def resume_menu_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle paused monitoring resume/cancel decision."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    action = query.data.split(":")[-1]

    if action == "continue":
        # Activate user
        db_manager.set_user_active(user_id, True)
        logger.info(f"User {user_id} resumed monitoring")

        # Re-register for notifications
        user_data = db_manager.get_user(user_id)
        notification_service = NotificationServiceHelper.get_notification_service(
            context
        )
        NotificationServiceHelper.re_register_user(
            notification_service, user_id, user_data
        )
        logger.info(f"User {user_id} re-registered for notifications")

        await query.edit_message_text(text=messages_ui.monitoring_resumed)

        # Show control menu
        from src.bot.control import settings_keyboard

        await update.effective_chat.send_message(
            "Используйте меню ниже для управления:",
            reply_markup=settings_keyboard(),
        )

    elif action == "cancel":
        await query.edit_message_text(text="❌ Восстановление отменено.")
        logger.info(f"User {user_id} cancelled resume")


# ============================================================================
# SETTINGS MENU HANDLERS - Изменение параметров активного пользователя
# ============================================================================


async def settings_menu_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle settings menu for active users.

    Allows users to:
    - Change checkpoint
    - Change interval
    - View current settings
    - Stop monitoring
    """
    text = update.message.text
    user_id = update.effective_user.id

    # Check user is registered
    if not db_manager.user_exists(user_id):
        await update.message.reply_text(messages_ui.user_not_found)
        return

    logger.info(f"User {user_id} selected menu option: {text}")

    if "Изменить переход" in text:
        await update.message.reply_text(
            messages_ui.choose_checkpoint,
            reply_markup=checkpoint_update_keyboard(),
        )

    elif "Изменить интервал" in text:
        await update.message.reply_text(
            messages_ui.choose_interval_unit,
            reply_markup=interval_unit_keyboard_update(),
        )

    elif "Мои настройки" in text:
        user_data = db_manager.get_user(user_id)
        settings_info = UserSettingsFormatter.get_user_settings_message(
            user_data, include_status=True
        )
        await update.message.reply_text(settings_info)

    elif "Остановить мониторинг" in text:
        db_manager.set_user_active(user_id, False)
        notification_service = NotificationServiceHelper.get_notification_service(
            context
        )
        if notification_service:
            notification_service.remove_user(user_id)
        logger.info(f"User {user_id} stopped monitoring")
        await update.message.reply_text(messages_ui.monitoring_stopped)

    else:
        await update.message.reply_text("❓ Неизвестная команда")


async def update_checkpoint_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle checkpoint update for active users."""
    query = update.callback_query
    await query.answer()

    checkpoint_name = query.data.split(":")[-1]
    user_id = update.effective_user.id

    try:
        # Update in database
        db_manager.update_user(user_id, checkpoint_name=checkpoint_name)
        logger.info(f"User {user_id} updated checkpoint to: {checkpoint_name}")

        # Re-register in notification service
        user_data = db_manager.get_user(user_id)
        notification_service = NotificationServiceHelper.get_notification_service(
            context
        )
        NotificationServiceHelper.re_register_user(
            notification_service, user_id, user_data
        )

        await query.edit_message_text(
            text=f"✅ Переход обновлен: {checkpoint_name.capitalize()}"
        )

        # Show updated settings
        settings_info = UserSettingsFormatter.get_user_settings_message(user_data)
        await update.effective_chat.send_message(
            f"✅ Текущие настройки:\n\n{settings_info}"
        )

    except Exception as e:
        logger.error(f"Error updating checkpoint for user {user_id}: {e}")
        await query.edit_message_text(
            text=messages_ui.registration_error.format(error=str(e))
        )


async def update_interval_unit_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle interval unit selection for update."""
    query = update.callback_query
    await query.answer()

    interval_unit = query.data.split(":")[-1]
    user_id = update.effective_user.id

    logger.info(f"User {user_id} selected interval unit for update: {interval_unit}")

    await query.edit_message_text(text=messages_ui.choose_interval_unit)

    # Show available values for selected unit
    await update.effective_chat.send_message(
        messages_ui.choose_interval_value.format(unit=interval_unit.capitalize()),
        reply_markup=interval_value_update_keyboard(interval_unit),
    )


async def update_interval_value_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle interval value update for active users."""
    query = update.callback_query
    await query.answer()

    callback_parts = query.data.split(":")
    interval_unit = callback_parts[3]
    interval_value = int(callback_parts[4])

    user_id = update.effective_user.id

    # Convert to seconds
    interval_seconds = interval_value * UNIT_TO_SECONDS.get(interval_unit, 1)

    try:
        # Update in database
        db_manager.update_user(user_id, interval_seconds=interval_seconds)
        logger.info(
            f"User {user_id} updated interval to: {interval_value} {interval_unit}"
        )

        # Re-register in notification service
        user_data = db_manager.get_user(user_id)
        notification_service = NotificationServiceHelper.get_notification_service(
            context
        )
        NotificationServiceHelper.re_register_user(
            notification_service, user_id, user_data
        )

        await query.edit_message_text(
            text=f"✅ Интервал обновлен: {interval_value} {interval_unit}"
        )

        # Show updated settings
        settings_info = UserSettingsFormatter.get_user_settings_message(user_data)
        await update.effective_chat.send_message(
            f"✅ Текущие настройки:\n\n{settings_info}"
        )

    except Exception as e:
        logger.error(f"Error updating interval for user {user_id}: {e}")
        await query.edit_message_text(
            text=messages_ui.registration_error.format(error=str(e))
        )
