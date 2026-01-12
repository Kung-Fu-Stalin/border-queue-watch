import asyncio
import time
import psutil
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LoadTestMetrics:
    """Метрики нагрузочного теста"""

    total_users: int
    total_notifications_sent: int
    total_notifications_expected: int
    test_duration_seconds: float
    memory_start_mb: float
    memory_end_mb: float
    memory_peak_mb: float
    cpu_avg_percent: float
    notifications_per_second: float
    success_rate: float

    def print_report(self):
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТА")
        print("=" * 70)
        print(f"👥 Пользователей:              {self.total_users:,}")
        print(f"⏱️  Длительность теста:         {self.test_duration_seconds:.2f} сек")
        print(f"📨 Отправлено уведомлений:     {self.total_notifications_sent:,}")
        print(f"🎯 Ожидалось уведомлений:      {self.total_notifications_expected:,}")
        print(f"✅ Успешность:                 {self.success_rate:.2f}%")
        print(f"⚡ Уведомлений/сек:            {self.notifications_per_second:.2f}")
        print(f"\n💾 Память начальная:           {self.memory_start_mb:.2f} MB")
        print(f"💾 Память конечная:            {self.memory_end_mb:.2f} MB")
        print(f"📈 Память пиковая:             {self.memory_peak_mb:.2f} MB")
        print(
            f"📊 Использование памяти:       +{self.memory_end_mb - self.memory_start_mb:.2f} MB"
        )
        print(f"🔥 CPU средняя загрузка:       {self.cpu_avg_percent:.2f}%")
        print("=" * 70 + "\n")


class MockBot:
    """Mock для Telegram бота"""

    def __init__(self):
        self.messages_sent = 0
        self.send_times: List[float] = []
        self.lock = asyncio.Lock()

    async def send_message(self, chat_id: int, text: str):
        """Имитация отправки сообщения с небольшой задержкой"""
        # Имитируем сетевую задержку Telegram API (1-5 мс)
        await asyncio.sleep(0.001 + (hash(chat_id) % 4) / 1000)

        async with self.lock:
            self.messages_sent += 1
            self.send_times.append(time.time())


class MockApplication:
    """Mock для Telegram Application"""

    def __init__(self):
        self.bot = MockBot()


class NotificationScheduler:
    """Копия класса из основного кода"""

    def __init__(self, app):
        self.app = app
        self.tasks: Dict[int, asyncio.Task] = {}

    def add_user(self, user_id: int, interval_seconds: int):
        self.remove_user(user_id)
        task = asyncio.create_task(
            self._user_loop(user_id, interval_seconds),
            name=f"user_scheduler_{user_id}",
        )
        self.tasks[user_id] = task

    def remove_user(self, user_id: int):
        task = self.tasks.pop(user_id, None)
        if task:
            task.cancel()

    async def _user_loop(self, user_id: int, interval_seconds: int):
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                await self.send_notification(user_id)
        except asyncio.CancelledError:
            pass

    async def send_notification(self, user_id: int):
        await self.app.bot.send_message(
            chat_id=user_id,
            text=f"⏰ Напоминание! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

    async def shutdown(self):
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()


class PerformanceMonitor:
    """Мониторинг производительности"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.monitoring = False
        self.monitor_task = None

    def get_memory_mb(self) -> float:
        """Получить использование памяти в MB"""
        return self.process.memory_info().rss / 1024 / 1024

    async def start_monitoring(self, interval: float = 0.5):
        """Запустить мониторинг"""
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))

    async def stop_monitoring(self):
        """Остановить мониторинг"""
        self.monitoring = False
        if self.monitor_task:
            await self.monitor_task

    async def _monitor_loop(self, interval: float):
        """Цикл мониторинга"""
        while self.monitoring:
            try:
                cpu = self.process.cpu_percent()
                mem = self.get_memory_mb()
                self.cpu_samples.append(cpu)
                self.memory_samples.append(mem)
                await asyncio.sleep(interval)
            except Exception:
                break

    def get_stats(self) -> Dict:
        """Получить статистику"""
        return {
            "cpu_avg": (
                sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
            ),
            "memory_peak": max(self.memory_samples) if self.memory_samples else 0,
        }


async def run_load_test(
    num_users: int = 10000,
    test_duration_seconds: int = 30,
    min_interval: int = 5,
    max_interval: int = 60,
):
    """
    Запуск нагрузочного теста

    Args:
        num_users: Количество пользователей
        test_duration_seconds: Длительность теста в секундах
        min_interval: Минимальный интервал уведомлений
        max_interval: Максимальный интервал уведомлений
    """
    print("\n🚀 Запуск нагрузочного теста...")
    print(f"👥 Пользователей: {num_users:,}")
    print(f"⏱️  Длительность: {test_duration_seconds} секунд")
    print(f"📊 Интервалы: {min_interval}-{max_interval} секунд\n")

    # Инициализация
    app = MockApplication()
    scheduler = NotificationScheduler(app)
    monitor = PerformanceMonitor()

    memory_start = monitor.get_memory_mb()
    start_time = time.time()

    print("📝 Фаза 1: Добавление пользователей...")
    add_start = time.time()

    # Добавляем пользователей с разными интервалами
    user_intervals = {}
    for user_id in range(1, num_users + 1):
        # Распределяем интервалы равномерно
        interval = min_interval + (user_id % (max_interval - min_interval + 1))
        scheduler.add_user(user_id, interval)
        user_intervals[user_id] = interval

        # Показываем прогресс каждые 1000 пользователей
        if user_id % 1000 == 0:
            print(f"  ✓ Добавлено {user_id:,} пользователей...")

    add_duration = time.time() - add_start
    print(f"✅ Все пользователи добавлены за {add_duration:.2f} сек")
    print(f"⚡ Скорость: {num_users / add_duration:.0f} пользователей/сек\n")

    # Запускаем мониторинг
    await monitor.start_monitoring()

    print(f"⏳ Фаза 2: Работа под нагрузкой ({test_duration_seconds} сек)...")
    print("   Ожидание отправки уведомлений...\n")

    # Показываем прогресс каждые 5 секунд
    for i in range(test_duration_seconds // 5):
        await asyncio.sleep(5)
        elapsed = (i + 1) * 5
        msgs = app.bot.messages_sent
        print(
            f"   [{elapsed:2d}s] Отправлено: {msgs:,} уведомлений, "
            f"Активных задач: {len(scheduler.tasks):,}"
        )

    # Дожидаемся оставшееся время
    remaining = test_duration_seconds % 5
    if remaining > 0:
        await asyncio.sleep(remaining)

    # Останавливаем мониторинг
    await monitor.stop_monitoring()

    test_duration = time.time() - start_time
    memory_end = monitor.get_memory_mb()

    print("\n🛑 Фаза 3: Остановка планировщика...")
    shutdown_start = time.time()
    await scheduler.shutdown()
    shutdown_duration = time.time() - shutdown_start
    print(f"✅ Планировщик остановлен за {shutdown_duration:.2f} сек")

    # Подсчет ожидаемого количества уведомлений
    total_expected = sum(
        test_duration_seconds // interval for interval in user_intervals.values()
    )

    # Получаем статистику мониторинга
    stats = monitor.get_stats()

    # Формируем метрики
    metrics = LoadTestMetrics(
        total_users=num_users,
        total_notifications_sent=app.bot.messages_sent,
        total_notifications_expected=total_expected,
        test_duration_seconds=test_duration,
        memory_start_mb=memory_start,
        memory_end_mb=memory_end,
        memory_peak_mb=stats["memory_peak"],
        cpu_avg_percent=stats["cpu_avg"],
        notifications_per_second=(
            app.bot.messages_sent / test_duration if test_duration > 0 else 0
        ),
        success_rate=(
            (app.bot.messages_sent / total_expected * 100) if total_expected > 0 else 0
        ),
    )

    # Выводим отчет
    metrics.print_report()

    # Дополнительный анализ
    print("📈 ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"🔧 Активных asyncio задач:     {len(scheduler.tasks)}")
    print(
        f"💾 Память на пользователя:     {(memory_end - memory_start) / num_users * 1024:.2f} KB"
    )
    print(
        f"⚙️  Overhead на пользователя:   ~{(memory_end - memory_start) * 1024 * 1024 / num_users:.0f} байт"
    )
    print(f"🏎️  Скорость добавления:        {num_users / add_duration:.0f} users/sec")
    print(
        f"🛑 Скорость остановки:         {num_users / shutdown_duration:.0f} users/sec"
    )

    # Анализ распределения отправок
    if app.bot.send_times:
        send_times_sorted = sorted(app.bot.send_times)
        time_span = send_times_sorted[-1] - send_times_sorted[0]
        if time_span > 0:
            actual_rate = len(send_times_sorted) / time_span
            print(f"📊 Фактическая скорость:       {actual_rate:.2f} msg/sec")

    print("=" * 70 + "\n")

    return metrics


async def run_comparison_test():
    """Сравнительный тест с разным количеством пользователей"""
    print("\n" + "=" * 70)
    print("🔬 СРАВНИТЕЛЬНЫЙ АНАЛИЗ МАСШТАБИРУЕМОСТИ")
    print("=" * 70 + "\n")

    test_cases = [
        (100, 20),
        (1000, 25),
        (5000, 30),
        (10000, 30),
    ]

    results = []

    for num_users, duration in test_cases:
        print(f"\n{'─' * 70}")
        print(f"Тест: {num_users:,} пользователей")
        print(f"{'─' * 70}")

        metrics = await run_load_test(
            num_users=num_users,
            test_duration_seconds=duration,
            min_interval=5,
            max_interval=60,
        )
        results.append((num_users, metrics))

        # Небольшая пауза между тестами для стабилизации
        await asyncio.sleep(2)

    # Итоговое сравнение
    print("\n" + "=" * 70)
    print("📊 СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    print("=" * 70)
    print(
        f"{'Пользователей':<15} {'Память (MB)':<15} {'KB/user':<12} {'CPU %':<10} {'Msg/sec':<10}"
    )
    print("─" * 70)

    for num_users, m in results:
        mem_used = m.memory_end_mb - m.memory_start_mb
        mem_per_user = mem_used * 1024 / num_users
        print(
            f"{num_users:<15,} {mem_used:<15.2f} {mem_per_user:<12.2f} "
            f"{m.cpu_avg_percent:<10.2f} {m.notifications_per_second:<10.2f}"
        )

    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Один тест на 10000 пользователей
    # asyncio.run(run_load_test(num_users=10000, test_duration_seconds=30))

    # Сравнительный анализ
    asyncio.run(run_comparison_test())
