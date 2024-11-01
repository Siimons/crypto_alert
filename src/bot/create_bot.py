from aiogram import Bot, Dispatcher
from .handlers import router, set_crypto_monitor

from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.crypto.crypto_checker import CryptoBotController
from src.crypto.exchanges.bybit import BybitExchange

from src.config import TELEGRAM_BOT_TOKEN
from src.utils.logging_config import logger

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def send_notification(chat_id: int, symbol: str = None, price_change: float = None, last_price: float = None, has_changes: bool = True, status_message: str = None):
    if status_message:
        message = status_message
    elif has_changes:
        message = (f"🚨 <b>{symbol}</b> изменился на {price_change:.2f}%! "
                   f"Текущая цена: {last_price:.2f}")
    else:
        message = "В последнее время существенных изменений в ценах криптовалют не обнаружено."

    await bot.send_message(chat_id=chat_id, text=message)

async def start_bot():
    dp = Dispatcher(storage=MemoryStorage())
    logger.info("Starting the bot...")

    exchanges = [BybitExchange()]
    crypto_monitor = CryptoBotController(exchanges, None, send_notification)

    # Передаем контроллер мониторинга в handlers через setter
    set_crypto_monitor(crypto_monitor)
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
