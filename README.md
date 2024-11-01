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