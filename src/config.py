from decouple import config

# Настройки для Telegram бота
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')

# API ключи криптобирж
BYBIT_API_KEY = config('BYBIT_API_KEY')
BYBIT_API_SECRET = config('BYBIT_API_SECRET')

# Настройка логирования
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
LOG_FILE_PATH = config('LOG_FILE_PATH')
LOG_ROTATION = config('LOG_ROTATION', default='500 MB')
LOG_RETENTION = config('LOG_RETENTION', default='10 days')

# Дополнительные настройки
CRYPTO_CHECK_INTERVAL = config('CRYPTO_CHECK_INTERVAL', default=60, cast=int)
PRICE_CHANGE_THRESHOLD = config('PRICE_CHANGE_THRESHOLD', default=100, cast=int)