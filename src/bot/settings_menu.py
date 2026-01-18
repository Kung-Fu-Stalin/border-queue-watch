"""
Dynamic Settings Menu Builder

Строит динамическое меню настроек на основе состояния регистрации.
Позволяет пользователю изменять параметры по мере их выбора.
"""

from telegram import ReplyKeyboardMarkup

from src.utils.registration_state import RegistrationState


class SettingsMenuBuilder:
    """
    Построитель динамического меню настроек.

    Меню формируется на основе того, какие параметры уже выбраны:
    - После выбора переходу: кнопка "Изменить переход"
    - После ввода номера: +кнопка "Изменить номер авто"
    - После выбора интервала: +кнопка "Изменить интервал"
    """

    @staticmethod
    def build_registration_menu(state: RegistrationState) -> ReplyKeyboardMarkup:
        """
        Построить меню во время регистрации.

        Динамически добавляет кнопки "Изменить" для каждого заполненного параметра.

        Args:
            state: Текущее состояние регистрации

        Returns:
            ReplyKeyboardMarkup с кнопками
        """
        buttons = []

        # Кнопка изменения переходу (доступна только после выбора)
        if state.is_checkpoint_set():
            buttons.append(["✏️ Изменить переход"])

        # Кнопка изменения номера авто (доступна только после ввода)
        if state.is_car_number_set():
            buttons.append(["🚗 Изменить номер авто"])

        # Кнопка изменения интервала (доступна как только выбрана единица)
        if state.interval_unit is not None:
            buttons.append(["⏱️ Изменить интервал"])

        # Кнопка завершения регистрации (только если всё заполнено)
        if state.is_complete():
            buttons.append(["✅ Завершить регистрацию"])

        return ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=False
        )

    @staticmethod
    def build_active_user_menu() -> ReplyKeyboardMarkup:
        """
        Построить полное меню для активного пользователя.

        Returns:
            ReplyKeyboardMarkup с полным набором опций
        """
        buttons = [
            ["✏️ Изменить переход", "🚗 Изменить номер авто"],
            ["⏱️ Изменить интервал"],
            ["⏸️ Остановить мониторинг", "ℹ️ Мои настройки"],
        ]
        return ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=False
        )

    @staticmethod
    def get_menu_message(state: RegistrationState) -> str:
        """
        Получить сообщение для меню с текущим состоянием.

        Args:
            state: Текущее состояние регистрации

        Returns:
            Форматированное сообщение
        """
        return f"Текущие настройки:\n\n{state.get_summary()}\n\nИспользуйте кнопки ниже для управления."

    @staticmethod
    def get_progress_message(state: RegistrationState) -> str:
        """
        Получить сообщение с прогрессом регистрации.

        Args:
            state: Текущее состояние регистрации

        Returns:
            Сообщение с информацией о прогрессе
        """
        progress_items = []

        if state.is_checkpoint_set():
            progress_items.append(f"✅ Переход: {state.checkpoint_name.capitalize()}")
        else:
            progress_items.append("⬜ Переход: не выбран")

        if state.is_car_number_set():
            progress_items.append(f"✅ Автомобиль: {state.car_number}")
        else:
            progress_items.append("⬜ Автомобиль: не введено")

        if state.is_interval_set():
            progress_items.append(
                f"✅ Интервал: {state.interval_value} {state.interval_unit}"
            )
        elif state.interval_unit is not None:
            # Единица выбрана, но значение еще нет
            progress_items.append(
                f"⏳ Интервал: {state.interval_unit} (выбираю значение...)"
            )
        else:
            progress_items.append("⬜ Интервал: не выбран")

        progress_text = "\n".join(progress_items)

        # Считаем только полностью завершенные шаги
        completed = sum(1 for item in progress_items if item.startswith("✅"))
        total = 3

        return (
            f"📝 Прогресс регистрации:\n\n{progress_text}\n\n"
            f"Готово: {completed}/{total}"
        )
