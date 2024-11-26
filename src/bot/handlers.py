from aiogram import Router, F
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
        "<b>Список команд:</b>\n"
        "/start - Запустить бота\n"
        "/help - Показать доступные команды\n"
        "/status - Показать текущий статус мониторинга\n"
        "/conf - Настроить параметры мониторинга\n"
        "/start_monitor - Запустить мониторинг\n"
        "/stop_monitor - Остановить мониторинг\n"
    )
    await message.answer(help_message)

@router.message(Command(commands=["start_monitor"]))
async def cmd_start_monitor(message: Message):
    """Команда /start_monitor для запуска мониторинга."""
    response_message = await crypto_monitor.start_monitoring()
    await message.answer(response_message)

@router.message(Command(commands=["stop_monitor"]))
async def cmd_stop_monitor(message: Message):
    """Команда /stop_monitor для остановки мониторинга."""
    response_message = await crypto_monitor.stop_monitoring()
    await message.answer(response_message)

@router.message(Command(commands=["conf"]))
async def cmd_conf(message: Message):
    """Команда /conf запрашивает у пользователя интервал и порог."""
    await message.answer(
        "Укажите параметры мониторинга через пробел:\n"
        "- Интервал (в секундах): частота проверки цен\n"
        "- Порог изменения (в %): процентное изменение для уведомлений\n\n"
        "Пример: <code>60 5</code> — проверка каждую минуту, уведомление при изменении на 5%."
    )

@router.message(F.text.regexp(r"^\d+\s+\d+(\.\d+)?$"))
async def process_conf_data(message: Message):
    """Обработка интервала и порога изменения цены для команды /conf."""
    try:
        interval, threshold = map(float, message.text.split())
        interval = int(interval)
        
        await crypto_monitor.update_config(interval, threshold)
        await message.answer(
            f"Настройки обновлены: интервал проверки = {interval} сек, порог изменения = {threshold}%."
        )
    except ValueError:
        await message.answer(
            "Ошибка: укажите интервал и порог изменения корректно.\nПример: <code>60 5</code>"
        )

@router.message(Command(commands=["status"]))
async def cmd_status(message: Message):
    """Команда /status для показа текущего статуса мониторинга."""
    await crypto_monitor.get_status()