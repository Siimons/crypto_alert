from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.utils.logging_config import logger

router = Router()

def set_crypto_monitor(monitor):
    """Функция для установки глобального экземпляра контроллера мониторинга."""
    global crypto_monitor
    crypto_monitor = monitor

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start для инициализации пользователя и начала работы с ботом."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or "Unknown"

    crypto_monitor.initialize_user(user_id, chat_id, username)
    logger.info(f"Пользователь с ID {user_id} начал взаимодействие с ботом.")
    await message.answer(
        "Привет! Я бот, который следит за резкими изменениями цен криптовалют. "
        "Используй /help, чтобы узнать доступные команды."
    )

@router.message(Command(commands=["help"]))
async def cmd_help(message: Message):
    """Команда /help для вывода доступных команд бота."""
    help_message = (
        "<b>Список команд:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Вывести список команд\n"
        "/status - Показать текущий статус мониторинга\n"
        "/coin <b>{coin_name}</b> - Получить информацию о криптовалюте\n"
        "Например, /coin BTC покажет последние данные о биткоине.\n"
        "/conf <b>{interval}</b> <b>{threshold}</b> - Установить параметры мониторинга:\n"
        "    - <b>{interval}</b> - Интервал проверки цен (в секундах)\n"
        "    - <b>{threshold}</b> - Порог изменения цены (в %)\n"
        "/start_monitor - Запустить мониторинг криптовалют\n"
        "/stop_monitor - Остановить мониторинг криптовалют\n"
    )
    await message.answer(help_message)

@router.message(Command(commands=["start_monitor"]))
async def cmd_start_monitor(message: Message):
    """Команда /start_monitor для запуска мониторинга."""
    await crypto_monitor.start_monitoring()
    await message.answer("Мониторинг криптовалют запущен.")

@router.message(Command(commands=["stop_monitor"]))
async def cmd_stop_monitor(message: Message):
    """Команда /stop_monitor для остановки мониторинга."""
    await crypto_monitor.stop_monitoring()
    await message.answer("Мониторинг криптовалют остановлен.")

@router.message(Command(commands=["conf"]))
async def cmd_conf(message: Message):
    """Команда /conf для изменения параметров мониторинга."""
    try:
        _, interval, threshold = message.text.split()
        interval = int(interval)
        threshold = float(threshold)
        
        await crypto_monitor.update_config(interval, threshold)
        await message.answer(
            f"Настройки обновлены: интервал проверки = {interval} сек, порог изменения = {threshold}%."
        )
    except ValueError:
        await message.answer("Ошибка: укажите интервал и порог изменения корректно.\nПример: /conf 60 5")

@router.message(Command(commands=["status"]))
async def cmd_status(message: Message):
    """Команда /status для показа текущего статуса мониторинга."""
    await crypto_monitor.get_status(message.chat.id)

@router.message(Command(commands=["coin"]))
async def cmd_coin_info(message: Message):
    """Команда /coin для получения информации о криптовалюте."""
    try:
        _, coin_name = message.text.split()
        await crypto_monitor.get_coin_info(message.chat.id, coin_name)
    except ValueError:
        await message.answer("Ошибка: укажите символ криптовалюты корректно.\nПример: /coin BTC")
