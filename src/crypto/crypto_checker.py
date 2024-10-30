import asyncio
from typing import List, Set, Callable
from src.crypto.exchange import Exchange

from src.utils.logging_config import logger
from src.config import CRYPTO_CHECK_INTERVAL, PRICE_CHANGE_THRESHOLD

class CryptoPriceMonitor:
    """Основной класс для мониторинга изменений на криптовалютных биржах и отправки уведомлений."""

    def __init__(self, exchanges: List[Exchange], active_chats: Set[int], send_notification: Callable):
        """
        Инициализация класса CryptoPriceMonitor.

        :param exchanges: Список криптовалютных бирж для мониторинга.
        :param active_chats: Набор активных чатов, куда отправляются уведомления.
        :param send_notification: Функция для отправки уведомлений через роутеры.
        """
        self.exchanges = exchanges
        self.active_chats = active_chats
        self.check_interval = CRYPTO_CHECK_INTERVAL
        self.price_change_threshold = PRICE_CHANGE_THRESHOLD
        self.is_monitoring_active = False
        self.send_notification = send_notification

    async def monitor_price_changes(self):
        """Асинхронный метод мониторинга изменений цен."""
        self.is_monitoring_active = True
        while self.is_monitoring_active:
            for exchange in self.exchanges:
                logger.info(f"Проверка данных на бирже {exchange.__class__.__name__}...")
                
                # Получаем данные с биржи
                data = await asyncio.get_running_loop().run_in_executor(None, exchange.fetch_market_data)
                
                # Фильтруем для значительных изменений
                significant_changes = await asyncio.get_running_loop().run_in_executor(
                    None,
                    exchange.filter_significant_changes,
                    data,
                    self.price_change_threshold
                )

                if significant_changes:
                    for coin in significant_changes:
                        logger.info(f"Отправка уведомления по монете {coin['symbol']} с изменением {coin['price_change']:.2f}%")
                        await self.notify_users(coin['symbol'], coin['price_change'], coin['last_price'])
                else:
                    logger.info("Существенных изменений не обнаружено.")
                    await self.notify_users(has_changes=False)
                    
            await asyncio.sleep(self.check_interval)

    async def notify_users(self, symbol: str = None, price_change: float = None, last_price: float = None, has_changes: bool = True):
        """Уведомляет все активные чаты о значительном изменении цен или об отсутствии изменений."""
        if not self.active_chats:
            logger.warning("Нет активных чатов для отправки уведомлений.")
            return

        for chat_id in self.active_chats:
            await self.send_notification(chat_id, symbol, price_change, last_price, has_changes)

class CryptoBotController(CryptoPriceMonitor):
    """Класс для управления мониторингом и выполнения команд бота."""

    def __init__(self, exchanges: List[Exchange], active_chats: Set[int], send_notification: Callable):
        super().__init__(exchanges, active_chats, send_notification)
        self.monitoring_task = None

    async def start_monitoring(self):
        """Асинхронно запускает мониторинг изменений цен."""
        if not self.monitoring_task or self.monitoring_task.done():
            logger.info("Запуск мониторинга криптовалют.")
            self.monitoring_task = asyncio.create_task(self.monitor_price_changes())
        else:
            logger.info("Мониторинг уже запущен.")

    async def stop_monitoring(self):
        """Асинхронно останавливает мониторинг изменений цен."""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.info("Остановка мониторинга криптовалют.")
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