from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class RegistrationState:
    """
    Состояние регистрации пользователя.

    Attributes:
        checkpoint_name: Выбранный пограничный переход
        car_number: Номер автомобиля
        interval_unit: Единица интервала (secs, mins, hours)
        interval_value: Значение интервала
    """

    checkpoint_name: Optional[str] = None
    car_number: Optional[str] = None
    interval_unit: Optional[str] = None
    interval_value: Optional[int] = None

    def is_checkpoint_set(self) -> bool:
        """Проверка наличия выбранного переходу."""
        return self.checkpoint_name is not None

    def is_car_number_set(self) -> bool:
        """Проверка наличия номера автомобиля."""
        return self.car_number is not None

    def is_interval_set(self) -> bool:
        """Проверка наличия установленного интервала."""
        return self.interval_unit is not None and self.interval_value is not None

    def is_complete(self) -> bool:
        """Проверка полноты регистрации."""
        return (
            self.is_checkpoint_set()
            and self.is_car_number_set()
            and self.is_interval_set()
        )

    def get_summary(self) -> str:
        """
        Получить краткое резюме текущего состояния.

        Returns:
            Форматированная строка с текущими параметрами
        """
        lines = []

        if self.is_checkpoint_set():
            lines.append(f"🔔 Переход: {self.checkpoint_name.capitalize()}")

        if self.is_car_number_set():
            lines.append(f"🚗 Автомобиль: {self.car_number}")

        if self.is_interval_set():
            lines.append(f"⏱️ Интервал: {self.interval_value} {self.interval_unit}")

        return "\n".join(lines) if lines else "Начнём регистрацию..."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistrationState":
        """Восстановить состояние из словаря."""
        return cls(**data)


class RegistrationStateManager:
    CONTEXT_KEY = "registration_state"

    @staticmethod
    def get(context_user_data: Dict) -> RegistrationState:
        if RegistrationStateManager.CONTEXT_KEY not in context_user_data:
            context_user_data[RegistrationStateManager.CONTEXT_KEY] = (
                RegistrationState()
            )

        return context_user_data[RegistrationStateManager.CONTEXT_KEY]

    @staticmethod
    def save(context_user_data: Dict, state: RegistrationState) -> None:
        context_user_data[RegistrationStateManager.CONTEXT_KEY] = state

    @staticmethod
    def clear(context_user_data: Dict) -> None:
        context_user_data.pop(RegistrationStateManager.CONTEXT_KEY, None)
