from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.utils.redis_manager import RedisChatManager
from src.utils.logging_config import logger

router = Router()

redis_chat_manager = RedisChatManager()
# username_str = None

def set_crypto_monitor(monitor):
    """Функция для установки глобального экземпляра контроллера мониторинга."""
    global crypto_monitor
    crypto_monitor = monitor

@router.message(CommandStart())
async def cmd_start(message: Message):
    global username_str
    username_str = message.from_user.username or str(message.from_user.id)
    redis_chat_manager.add_chat(username=username_str, chat_id=message.chat.id)
    
    crypto_monitor.update_user(username_str)
    logger.info(f"Пользователь {username_str} с ID {message.chat.id} начал взаимодействие с ботом.")
    await message.answer(
        "Привет! Я бот, который следит за резкими изменениями цен криптовалют. "
        "Используй /help, чтобы узнать доступные команды."
    )

@router.message(Command(commands=["help"]))
async def cmd_help(message: Message):
    logger.info(f"Пользователь {message.chat.id} запросил команду /help.")
    help_message = (
        "<b>Список команд:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Вывести список команд\n"
        "/status - Показать текущий статус мониторинга\n"
        "/coin <b>{coin_name}</b> - Получить информацию о криптовалюте\n"
        "Например, /coin BTC покажет последние данные о биткоине.\n"
        "/conf <b>{interval}</b> <b>{threshold}</b> - Установить новые параметры мониторинга:\n"
        "    - <b>{interval}</b> - Интервал проверки цен в секундах\n"
        "    - <b>{threshold}</b> - Порог изменения цены в процентах\n"
        "/start_monitor - Запустить мониторинг криптовалют\n"
        "/stop_monitor - Остановить мониторинг криптовалют\n"
    )
    await message.answer(help_message)

@router.message(Command(commands=["start_monitor"]))
async def cmd_start_monitor(message: Message):
    global username_str
    username_str = message.from_user.username or str(message.from_user.id)
    
    if crypto_monitor:
        crypto_monitor.update_user(username_str)
        await crypto_monitor.start_monitoring()
        await message.answer("Мониторинг криптовалют запущен.")
    else:
        await message.answer("Ошибка: контроллер мониторинга не инициализирован.")

@router.message(Command(commands=["stop_monitor"]))
async def cmd_stop_monitor(message: Message):
    if crypto_monitor:
        await crypto_monitor.stop_monitoring()
        await message.answer("Мониторинг криптовалют остановлен.")
    else:
        await message.answer("Ошибка: контроллер мониторинга не инициализирован.")

@router.message(Command(commands=["conf"]))
async def cmd_conf(message: Message):
    try:
        _, interval, threshold = message.text.split()
        interval = int(interval)
        threshold = float(threshold)
        
        if crypto_monitor:
            await crypto_monitor.update_config(interval, threshold)
            await message.answer(
                f"Настройки обновлены: интервал = {interval} сек, порог изменения = {threshold}%."
            )
        else:
            await message.answer("Ошибка: контроллер мониторинга не инициализирован.")
    except ValueError:
        await message.answer("Ошибка: укажите интервал и порог изменения корректно.\nПример: /conf 60 5")
