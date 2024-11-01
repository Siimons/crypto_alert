import asyncio
from typing import List, Callable, Optional

from src.crypto.exchange import Exchange
from src.utils.redis_manager import RedisChatManager, RedisCacheManager

from src.utils.logging_config import logger
from src.config import CRYPTO_CHECK_INTERVAL, PRICE_CHANGE_THRESHOLD


class CryptoPriceMonitor:
    """Основной класс для мониторинга изменений на криптовалютных биржах и отправки уведомлений."""

    def __init__(self, exchanges: List[Exchange], username: str, send_notification: Callable):
        """
        Инициализация класса CryptoPriceMonitor.
        
        :param exchanges: Список криптовалютных бирж для мониторинга.
        :param username: Имя пользователя, активирующего мониторинг.
        :param send_notification: Функция для отправки уведомлений через роутеры.
        """
        self.exchanges = exchanges
        self.username = username
        self.send_notification = send_notification
        self.is_monitoring_active = False
        
        self.check_interval = CRYPTO_CHECK_INTERVAL
        self.price_change_threshold = PRICE_CHANGE_THRESHOLD

        self.chat_manager = RedisChatManager()
        self.cache_manager = RedisCacheManager()

    async def monitor_price_changes(self):
        """Асинхронный метод мониторинга изменений цен для активного пользователя."""
        self.is_monitoring_active = True
        
        chat_id = self.chat_manager.get_chat_id(self.username)
        if not chat_id:
            logger.warning(f"Чат не найден для пользователя {self.username}")
            return

        while self.is_monitoring_active:
            for exchange in self.exchanges:
                logger.info(f"Проверка данных на бирже {exchange.__class__.__name__}...")

                # Получаем кэшированные данные
                cache_key = exchange.__class__.__name__
                cached_data = self.cache_manager.get_data(cache_key)

                # Получаем свежие данные с биржи, если кэша нет или устарел
                if not cached_data:
                    data = await asyncio.get_running_loop().run_in_executor(None, exchange.fetch_market_data)
                    self.cache_manager.save_data(cache_key, data, ttl=300)  # Сохраняем данные с TTL 5 минут
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
                        logger.info(f"Отправка уведомления по монете {coin['symbol']} с изменением {coin['price_change']:.2f}%")
                        await self.notify_user(chat_id, coin['symbol'], coin['price_change'], coin['last_price'])
                else:
                    logger.info("Существенных изменений не обнаружено.")
                    await self.notify_user(chat_id, has_changes=False)

            await asyncio.sleep(self.check_interval)

    async def notify_user(self, chat_id: int, symbol: Optional[str] = None, price_change: Optional[float] = None,
                          last_price: Optional[float] = None, has_changes: bool = True):
        """Уведомляет конкретного пользователя о значительном изменении цен или об отсутствии изменений."""
        if not chat_id:
            logger.warning("Невозможно отправить уведомление: chat_id отсутствует.")
            return

        await self.send_notification(chat_id, symbol, price_change, last_price, has_changes)


class CryptoBotController(CryptoPriceMonitor):
    """Класс для управления мониторингом и выполнения команд бота."""

    def __init__(self, exchanges: List[Exchange], username: str, send_notification: Callable):
        super().__init__(exchanges, username, send_notification)
        self.monitoring_task = None

    def update_user(self, username: str):
        """Метод для обновления текущего username."""
        self.username = username
    
    async def start_monitoring(self):
        """Асинхронно запускает мониторинг изменений цен."""
        if not self.monitoring_task or self.monitoring_task.done():
            logger.info(f"Запуск мониторинга для пользователя {self.username}.")
            self.monitoring_task = asyncio.create_task(self.monitor_price_changes())
        else:
            logger.info("Мониторинг уже запущен.")

    async def stop_monitoring(self):
        """Асинхронно останавливает мониторинг изменений цен."""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.info(f"Остановка мониторинга для пользователя {self.username}.")
            self.monitoring_task.cancel()
            self.is_monitoring_active = False
            await self.monitoring_task
        else:
            logger.info("Мониторинг уже остановлен.")

    async def update_config(self, check_interval: int, price_change_threshold: float):
        """Асинхронно обновляет настройки мониторинга."""
        self.check_interval = check_interval
        self.price_change_threshold = price_change_threshold
        logger.info(f"Настройки мониторинга обновлены: интервал проверки = {self.check_interval} сек, "
                    f"порог изменения цены = {self.price_change_threshold}%")
        
    async def get_status(self, chat_id: int):
        """Отправляет пользователю статус мониторинга."""
        status_message = (
            f"📊 <b>Статус мониторинга</b>\n"
            f"Активен: {'Да' if self.is_monitoring_active else 'Нет'}\n"
            f"Интервал проверки: {self.check_interval} сек\n"
            f"Порог изменения цены: {self.price_change_threshold}%"
        )
        await self.send_notification(chat_id, status_message=status_message)

    async def get_coin_info(self, chat_id: int, coin_name: str):
        """Отправляет пользователю информацию о конкретной криптовалюте, если она доступна на бирже."""
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