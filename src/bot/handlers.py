from telegram import Update
from telegram.ext import ContextTypes

from src.utils import db_manager, messages_ui, get_logger
from src.bot.replies import select_interval_unit_reply, select_interval_value_reply

logger = get_logger(__name__)


async def checkpoint_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle checkpoint selection - ask for car number next."""
    query = update.callback_query
    await query.answer()

    checkpoint_name = query.data

    # Store checkpoint in user context
    context.user_data["selected_checkpoint"] = checkpoint_name

    logger.info(
        f"User {update.effective_user.id} selected checkpoint: {checkpoint_name}"
    )

    # Show confirmation
    await query.edit_message_text(
        text=messages_ui.checkpoint_selected.format(
            checkpoint=checkpoint_name.capitalize()
        )
    )

    # Ask for car number
    await update.effective_chat.send_message(messages_ui.enter_car_number)


async def car_number_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle car number entry - ask for interval unit next."""
    car_number = update.message.text.strip().upper()

    user_id = update.effective_user.id

    # Basic validation (not empty)
    if not car_number:
        await update.message.reply_text(messages_ui.invalid_car_number)
        return

    # Store car number in user context
    context.user_data["car_number"] = car_number

    logger.info(f"User {user_id} entered car number: {car_number}")

    # Confirm car number
    await update.message.reply_text(f"✅ Номер: {car_number}")

    # Show interval unit keyboard
    await select_interval_unit_reply(update, context)


async def interval_unit_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle interval unit selection - ask for value next."""
    query = update.callback_query
    await query.answer()

    # Extract unit from callback_data (format: "interval:unit:{unit}")
    interval_unit = query.data.split(":")[-1]

    # Store unit in user context
    context.user_data["selected_interval_unit"] = interval_unit

    logger.info(
        f"User {update.effective_user.id} selected interval unit: {interval_unit}"
    )

    await query.edit_message_text(text=messages_ui.choose_interval_unit)

    # Show interval values for this unit
    await select_interval_value_reply(update, context, interval_unit)


async def interval_value_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle interval value selection - save user to DB and start scheduler."""
    query = update.callback_query
    await query.answer()

    # Extract value and unit from callback_data (format: "interval:value:{unit}:{value}")
    callback_parts = query.data.split(":")
    interval_unit = callback_parts[2]
    interval_value = int(callback_parts[3])

    # Get checkpoint and car number from context
    checkpoint_name = context.user_data.get("selected_checkpoint")
    car_number = context.user_data.get("car_number")

    if not checkpoint_name or not car_number:
        await query.edit_message_text(text=messages_ui.incomplete_data)
        return

    user_id = update.effective_user.id
    user_name = update.effective_user.username or "noUsername"

    logger.info(
        f"User {user_id} completed setup: checkpoint={checkpoint_name}, "
        f"car_number={car_number}, interval={interval_value} {interval_unit}"
    )

    # Convert interval to seconds
    unit_multipliers = {
        "secs": 1,
        "mins": 60,
        "hours": 3600,
    }
    interval_seconds = interval_value * unit_multipliers.get(interval_unit, 1)

    try:
        # Check if user exists
        if db_manager.user_exists(user_id):
            logger.warning(f"User {user_id} already exists")
            await query.edit_message_text(text=messages_ui.user_exists)
            return

        # Add user to database
        db_manager.add_user(
            telegram_user_id=user_id,
            telegram_user_name=user_name,
            interval_seconds=interval_seconds,
            car_number=car_number,
            checkpoint_name=checkpoint_name,
        )

        logger.info(f"User {user_id} saved to DB with interval {interval_seconds}s")

        # Register user for notifications
        notification_service = context.application.bot_data.get("notification_service")
        if notification_service:
            notification_service.add_user(
                user_id=user_id,
                interval_seconds=interval_seconds,
                checkpoint_name=checkpoint_name,
                car_number=car_number,
            )
            logger.info(f"User {user_id} registered for notifications")

        # Send success message with car number
        await query.edit_message_text(
            text=messages_ui.user_created.format(
                car_number=car_number,
                checkpoint=checkpoint_name.capitalize(),
                value=interval_value,
                unit=interval_unit,
            )
        )

        # Clear user data
        context.user_data.clear()

    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")
        await query.edit_message_text(
            text=messages_ui.registration_error.format(error=str(e))
        )
