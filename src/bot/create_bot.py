from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from .handlers import router, set_crypto_monitor

from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.crypto.crypto_checker import CryptoBotController
from src.crypto.exchanges.bybit import BybitExchange

from src.config import TELEGRAM_BOT_TOKEN
from src.utils.logging_config import logger

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def set_bot_commands(bot: Bot):
    """Установка списка команд для бота в интерфейсе Telegram."""
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="status", description="Текущий статус мониторинга"),
        BotCommand(command="conf", description="Настройки мониторинга"),
        BotCommand(command="start_monitor", description="Запуск мониторинга"),
        BotCommand(command="stop_monitor", description="Остановка мониторинга"),
    ]
    await bot.set_my_commands(commands)

async def start_bot():
    dp = Dispatcher(storage=MemoryStorage())
    logger.info("Starting the bot...")

    exchanges = [BybitExchange()]
    crypto_monitor = CryptoBotController(exchanges, bot)

    set_crypto_monitor(crypto_monitor)
    dp.include_router(router)
    
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await crypto_monitor.restart_active_sessions()
    await dp.start_polling(bot)