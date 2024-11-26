import asyncio

from aiogram import Bot
from typing import List

from src.crypto.exchange import Exchange
from src.utils.redis_manager import RedisChatManager, RedisCacheManager

from src.utils.logging_config import logger
from src.config import CRYPTO_CHECK_INTERVAL, PRICE_CHANGE_THRESHOLD


class CryptoPriceMonitor:
    """Основной класс для мониторинга изменений на криптовалютных биржах и отправки уведомлений пользователю."""
    
    def __init__(self, exchanges: List[Exchange], bot: Bot):
        """
        Инициализация класса для мониторинга цен.
        
        :param exchanges: Список криптовалютных бирж для отслеживания.
        :param bot: Экземпляр Telegram бота.
        """
        self.exchanges = exchanges
        self.bot = bot
        self.user_id = None
        self.chat_id = None
        self.username = None
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

    async def monitor_price_changes(self):
        """Асинхронный метод для отслеживания изменений цен с уведомлением пользователя."""
        self.is_monitoring_active = True

        if not self.chat_id:
            logger.warning(f"Не найден chat_id для пользователя {self.user_id}")
            return

        while self.is_monitoring_active:
            for exchange in self.exchanges:
                logger.info(f"Получение данных с биржи {exchange.get_exchange_name()}...")

                cache_key = exchange.get_exchange_name()
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

                exchange_name = exchange.get_exchange_name()
                if significant_changes:
                    for coin in significant_changes:
                        await self.send_notification(
                            symbol=coin['symbol'],
                            price_change=coin['price_change'],
                            last_price=coin['last_price'],
                            exchange_name=exchange_name
                        )
                else:
                    await self.send_notification(exchange_name=exchange_name, has_changes=False)

            await asyncio.sleep(self.check_interval)

    async def send_notification(self, symbol: str = None, price_change: float = None,
                                last_price: float = None, has_changes: bool = True,
                                exchange_name: str = ""):
        """Отправляет уведомление пользователю о значительных изменениях цен или их отсутствии."""
        if not self.chat_id:
            logger.warning("Невозможно отправить уведомление: отсутствует chat_id.")
            return

        if has_changes:
            message = (f"🚨 На бирже <b>{exchange_name}</b> монета <b>{symbol}</b> изменилась на "
                       f"{price_change:.2f}%! Текущая цена: {last_price:.2f}")
        else:
            message = f"На бирже <b>{exchange_name}</b> существенных изменений в ценах криптовалют не обнаружено."

        await self.bot.send_message(chat_id=self.chat_id, text=message)


class CryptoBotController(CryptoPriceMonitor):
    """Класс для управления ботом и его командами, включая контроль мониторинга цен."""
    
    def __init__(self, exchanges: List[Exchange], bot: Bot):
        super().__init__(exchanges, bot)
        self.monitoring_task = None

    async def start_monitoring(self):
        """Запускает мониторинг изменений цен асинхронно."""
        self.update_user_if_needed()

        if self.is_monitoring_active and self.monitoring_task and not self.monitoring_task.done():
            logger.info(f"Попытка повторного запуска мониторинга для пользователя {self.user_id}")
            message = "⚠️ Мониторинг уже запущен. Нет необходимости запускать его повторно."
        else:
            logger.info(f"Запуск мониторинга для пользователя {self.user_id}")
            self.monitoring_task = asyncio.create_task(self.monitor_price_changes())
            self.is_monitoring_active = True
            message = "✅ Мониторинг криптовалют успешно запущен!"

        self.chat_manager.set_monitoring_status(self.user_id, True)
        return message

    async def stop_monitoring(self):
        """Останавливает мониторинг изменений цен асинхронно."""
        self.update_user_if_needed()

        if not self.is_monitoring_active or not self.monitoring_task or self.monitoring_task.done():
            logger.info(f"Попытка повторной остановки мониторинга для пользователя {self.user_id}")
            message = "⚠️ Мониторинг уже остановлен. Нет необходимости останавливать его повторно."
        else:
            logger.info(f"Остановка мониторинга для пользователя {self.user_id}")
            self.monitoring_task.cancel()
            self.is_monitoring_active = False

            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                logger.info("Задача мониторинга успешно отменена.")
            
            message = "🛑 Мониторинг криптовалют успешно остановлен!"
        
        self.chat_manager.set_monitoring_status(self.user_id, False)
        return message

    async def update_config(self, check_interval: int, price_change_threshold: float):
        """Асинхронно обновляет параметры мониторинга."""
        self.update_user_if_needed()
        self.check_interval = check_interval
        self.price_change_threshold = price_change_threshold
        logger.info(f"Обновлены параметры мониторинга: интервал = {self.check_interval} сек, порог изменения цены = {self.price_change_threshold}%")

    async def get_status(self):
        """Отправляет статус мониторинга пользователю."""
        self.update_user_if_needed()
        if not self.chat_id:
            logger.warning(f"Не задан chat_id для пользователя {self.user_id}.")
            return

        status_message = (
            f"📊 <b>Статус мониторинга</b>\n"
            f"Активен: {'Да' if self.is_monitoring_active else 'Нет'}\n"
            f"Интервал проверки: {self.check_interval} сек\n"
            f"Порог изменения цены: {self.price_change_threshold}%"
        )
        await self.bot.send_message(chat_id=self.chat_id, text=status_message)

    async def restart_active_sessions(self):
        """Инициализирует все данные из Redis и перезапускает мониторинг для пользователей с активным статусом мониторинга."""
        all_users = self.chat_manager.get_all_chats()
        
        for user_id, user_data in all_users.items():
            self.user_id = user_id
            self.chat_id = int(user_data['chat_id'])
            self.username = user_data['username']
            self.is_monitoring_active = user_data['is_monitoring_active']

            self.is_monitoring_active = bool(int(user_data.get('is_monitoring_active', '0')))
            
            logger.info(f"Инициализация данных для пользователя: user_id={user_id}, chat_id={self.chat_id}, мониторинг активен={self.is_monitoring_active}")

            if self.is_monitoring_active:
                try:
                    logger.info(f"Перезапуск мониторинга для пользователя: user_id={user_id}, chat_id={self.chat_id}")
                    await self.start_monitoring()
                except Exception as e:
                    logger.error(f"Ошибка при перезапуске мониторинга для пользователя {user_id}: {e}")