# Crypto Alert Bot

**Crypto Alert Bot** — это Telegram-бот для мониторинга криптовалют, который отслеживает изменения цен на различных биржах и уведомляет пользователей о резких колебаниях. Этот бот поддерживает ряд популярных бирж, таких как Bybit, Binance, BitMart, KuCoin, OKX, и другие.

## Основной функционал

- Отслеживание цен криптовалют в режиме реального времени.
- Настраиваемые параметры мониторинга (интервал проверки и порог изменения).
- Уведомления о достижении установленного порога изменений цены.
- Поддержка нескольких бирж и криптовалют.

## Требования

- Python 3.8 или новее
- Redis для хранения данных
- Docker (опционально, для контейнерного развертывания)

## Установка

### 1. Клонирование репозитория

Сначала клонируйте репозиторий на локальную машину:

```bash
git clone https://github.com/siimons/crypto_alert
cd crypto_alert
```

### 2. Настройка окружения

Создайте файл `.env` в корневой директории проекта и добавьте ваши API-ключи и конфигурации:

```
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

BINANCE_API_KEY=<your_binance_api_key>
KUCOIN_API_KEY=<your_kucoin_api_key>
```

### 3. Создание и активация виртуального окружения:

```bash
python3 -m venv venv

source venv/bin/activate    # Для Linux/MacOS
venv\Scripts\activate       # Для Windows
```

### 4. Установка зависимостей

Установите необходимые зависимости Python:

```bash
pip install -r requirements.txt
```

## Запуск Redis-сервера

Установите и запустите Redis:

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

## Запуск приложения

Для запуска бота выполните следующую команду:

```bash
python main.py
```

Бот должен начать работу и ожидать взаимодействия в Telegram.

## Docker (опционально)

Для запуска проекта в Docker:

### 1. Соберите Docker-образ:

```bash
docker build -t crypto_alert .
```

### 2. Запустите контейнер:

```bash
docker run -d --env-file .env -p 8000:8000 crypto_alert
```

## Команды бота

- `/start` — Запустить бота и инициализировать пользователя.
- `/help` — Показать доступные команды.
- `/status` — Показать текущий статус мониторинга.
- `/conf` — Настроить параметры мониторинга.
- `/start_monitor` — Запустить мониторинг.
- `/stop_monitor` — Остановить мониторинг.

## Файловая структура 

```
crypto_alert/
│
├── src/                        # Исходный код проекта
│   ├── bot/                    # Логика Telegram бота и обработка сообщений
│   │   ├── create_bot.py       # Основная логика Telegram бота
│   │   ├── handlers.py         # Обработчики команд и сообщений
│   │   └── __init__.py         # Инициализация пакета bot
│   │
│   ├── crypto/                 # Пакет для работы с криптовалютами и мониторинга
│   │   ├── crypto_checker.py   # Основная логика мониторинга криптовалют
│   │   ├── exchange.py         # Реализация абстрактного базового класса для всех бирж
│   │   ├── exchanges/          # Пакет для работы с API криптобирж
│   │   │   ├── gate.py         # API для биржи Gate.io
│   │   │   ├── mexc.py         # API для биржи MEXC
│   │   │   ├── bitmart.py      # API для биржи BitMart
│   │   │   ├── xt.py           # API для биржи XT.com
│   │   │   ├── coinex.py       # API для биржи CoinEx
│   │   │   ├── okex.py         # API для биржи OKX
│   │   │   ├── huobi.py        # API для биржи Huobi
│   │   │   ├── bingx.py        # API для биржи BingX
│   │   │   ├── binance.py      # API для биржи Binance
│   │   │   ├── bybit.py        # API для биржи Bybit
│   │   │   ├── kucoin.py       # API для биржи Kucoin
│   │   │   └── __init__.py     # Инициализация пакета exchanges
│   │   └── __init__.py         # Инициализация пакета crypto
│   │
│   ├── utils/                  # Вспомогательные функции и настройки
│   │   ├── logging_config.py   # Настройка и инициализация логирования
│   │   ├── redis_manager.py    # Менеджер данных Redis
│   │   └── __init__.py         # Инициализация пакета utils
│   │
│   ├── config.py               # Основной конфигурационный файл проекта (API-ключи, параметры)
│   └── __init__.py             # Инициализация пакета src
│
├── logs/                       # Каталог для логов
│   └── app.log                 # Файл логов
│
├── main.py                     # Главный файл для запуска программы
├── requirements.txt            # Зависимости проекта (aiogram, requests, etc.)
├── Dockerfile                  # Docker конфигурация для развертывания
├── README.md                   # Описание проекта и инструкции по запуску
├── .env                        # Конфигурации для API-ключей
└── .gitignore                  # Файлы и папки, игнорируемые Git
```