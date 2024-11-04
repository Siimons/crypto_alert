import asyncio
from typing import List, Callable, Optional

from src.crypto.exchange import Exchange
from src.utils.redis_manager import RedisChatManager, RedisCacheManager

from src.utils.logging_config import logger
from src.config import CRYPTO_CHECK_INTERVAL, PRICE_CHANGE_THRESHOLD


class CryptoPriceMonitor:
    """Основной класс для мониторинга изменений на криптовалютных биржах и отправки уведомлений пользователю."""
    
    def __init__(self, exchanges: List[Exchange], send_notification: Callable):
        """
        Инициализация класса для мониторинга цен.
        
        :param exchanges: Список криптовалютных бирж для отслеживания.
        :param send_notification: Функция для отправки уведомлений.
        """
        self.exchanges = exchanges
        self.user_id = None
        self.chat_id = None
        self.username = None
        self.send_notification = send_notification
        self.is_monitoring_active = False
        
        self.check_interval = CRYPTO_CHECK_INTERVAL
        self.price_change_threshold = PRICE_CHANGE_THRESHOLD

        self.chat_manager = RedisChatManager()
        self.cache_manager = RedisCacheManager()

    def initialize_user(self, user_id: int, chat_id: int, username: str):
        """Инициализация данных пользователя при запуске бота и сохранение данных в Redis."""
        self.user_id = user_id
        self.chat_id = chat_id
        self.username = username
        self.chat_manager.add_user(user_id, chat_id, username)
        logger.info(f"Пользователь инициализирован: user_id={user_id}, chat_id={chat_id}, username={username}")

    def update_user_if_needed(self):
        """Обновляет данные пользователя в Redis при их изменении."""
        stored_data = self.chat_manager.get_user_data(self.user_id)
        if stored_data:
            if stored_data.get('chat_id') != self.chat_id or stored_data.get('username') != self.username:
                self.chat_manager.add_user(self.user_id, self.chat_id, self.username)
                logger.info(f"Данные пользователя обновлены: user_id={self.user_id}")
        else:
            logger.warning(f"Нет данных для user_id={self.user_id}, требуется инициализация через /start")

    def reset_user_data(self):
        """Сбрасывает информацию о пользователе для корректного мониторинга и повторной инициализации."""
        self.user_id = None
        self.chat_id = None
        self.username = None
        logger.info("Данные пользователя сброшены. Требуется повторная инициализация.")

    async def monitor_price_changes(self):
        """Асинхронный метод для отслеживания изменений цен с уведомлением пользователя."""
        self.is_monitoring_active = True

        if not self.chat_id:
            logger.warning(f"Не найден chat_id для пользователя {self.user_id}")
            return

        while self.is_monitoring_active:
            for exchange in self.exchanges:
                logger.info(f"Получение данных с биржи {exchange.__class__.__name__}...")

                cache_key = exchange.__class__.__name__
                cached_data = self.cache_manager.get_data(cache_key)

                if not cached_data:
                    data = await asyncio.get_running_loop().run_in_executor(None, exchange.fetch_market_data)
                    self.cache_manager.save_data(cache_key, data, ttl=300)
                else:
                    data = cached_data

                significant_changes = await asyncio.get_running_loop().run_in_executor(
                    None,
                    exchange.filter_significant_changes,
                    data,
                    self.price_change_threshold
                )

                if significant_changes:
                    for coin in significant_changes:
                        await self.notify_user(self.chat_id, symbol=coin['symbol'], price_change=coin['price_change'], last_price=coin['last_price'])
                else:
                    await self.notify_user(self.chat_id, has_changes=False)

            await asyncio.sleep(self.check_interval)

    async def notify_user(self, chat_id: int, symbol: Optional[str] = None, price_change: Optional[float] = None,
                          last_price: Optional[float] = None, has_changes: bool = True):
        """Отправляет уведомление пользователю о значительных изменениях цен или их отсутствии."""
        if not chat_id:
            logger.warning("Невозможно отправить уведомление: отсутствует chat_id.")
            return

        await self.send_notification(chat_id, symbol=symbol, price_change=price_change, last_price=last_price, has_changes=has_changes)


class CryptoBotController(CryptoPriceMonitor):
    """Класс для управления ботом и его командами, включая контроль мониторинга цен."""
    
    def __init__(self, exchanges: List[Exchange], send_notification: Callable):
        super().__init__(exchanges, send_notification)
        self.monitoring_task = None

    async def start_monitoring(self):
        """Запускает мониторинг изменений цен асинхронно."""
        self.update_user_if_needed()
        if not self.monitoring_task or self.monitoring_task.done():
            logger.info(f"Запуск мониторинга для пользователя {self.user_id}")
            self.monitoring_task = asyncio.create_task(self.monitor_price_changes())
        else:
            logger.info("Мониторинг уже запущен.")

    async def stop_monitoring(self):
        """Останавливает мониторинг изменений цен асинхронно."""
        self.update_user_if_needed()
        if self.monitoring_task and not self.monitoring_task.done():
            logger.info(f"Остановка мониторинга для пользователя {self.user_id}")
            self.monitoring_task.cancel()
            self.is_monitoring_active = False
            await self.monitoring_task
        else:
            logger.info("Мониторинг уже остановлен.")

    async def update_config(self, check_interval: int, price_change_threshold: float):
        """Асинхронно обновляет параметры мониторинга."""
        self.update_user_if_needed()
        self.check_interval = check_interval
        self.price_change_threshold = price_change_threshold
        logger.info(f"Обновлены параметры мониторинга: интервал = {self.check_interval} сек, порог изменения цены = {self.price_change_threshold}%")

    async def get_status(self, chat_id: int):
        """Отправляет статус мониторинга и проверяет актуальность данных пользователя."""
        self.update_user_if_needed()
        status_message = (
            f"📊 <b>Статус мониторинга</b>\n"
            f"Активен: {'Да' if self.is_monitoring_active else 'Нет'}\n"
            f"Интервал проверки: {self.check_interval} сек\n"
            f"Порог изменения цены: {self.price_change_threshold}%"
        )
        await self.send_notification(chat_id, status_message=status_message)

    async def get_coin_info(self, chat_id: int, coin_name: str):
        """Отправляет пользователю информацию о выбранной криптовалюте и актуализирует данные пользователя."""
        self.update_user_if_needed()
        for exchange in self.exchanges:
            data = await asyncio.get_running_loop().run_in_executor(None, exchange.fetch_market_data)
            coin_info = next((coin for coin in data if coin['symbol'].lower() == coin_name.lower()), None)

            if coin_info:
                info_message = (
                    f"💰 <b>{coin_info['symbol']}</b>\n"
                    f"Текущая цена: {coin_info['last_price']}\n"
                    f"Изменение за 24ч: {coin_info['price_change']}%"
                )
                await self.send_notification(chat_id, status_message=info_message)
                return

        await self.send_notification(chat_id, status_message=f"❗ Монета {coin_name} не найдена.")