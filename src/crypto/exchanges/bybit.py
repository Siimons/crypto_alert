from typing import List, Dict
from pybit.unified_trading import HTTP
from src.crypto.exchange import Exchange

from src.utils.logging_config import logger
from src.config import BYBIT_API_KEY, BYBIT_API_SECRET


class BybitExchange(Exchange):
    """Класс для работы с API Bybit."""

    def __init__(self, api_key: str = BYBIT_API_KEY, secret_key: str = BYBIT_API_SECRET):
        self.api_key = api_key
        self.secret_key = secret_key
        self.session = HTTP(api_key=self.api_key, api_secret=self.secret_key)

    def fetch_market_data(self) -> List[Dict]:
        """Извлекает данные о рынке с биржи Bybit."""
        try:
            response = self.session.get_tickers(category="spot")
            # logger.info(f"Получен ответ от API: {response}")
            
            if 'retCode' not in response:
                raise Exception("Ошибка: отсутствует ключ 'retCode' в ответе API")

            if response['retCode'] != 0:
                raise Exception(f"Ошибка при получении данных: {response.get('retMsg', 'Неизвестная ошибка')}")

            return response["result"]["list"]

        except Exception as e:
            logger.error(f"Ошибка при получении рыночных данных: {e}")
            return []

    def filter_significant_changes(self, data: List[Dict], threshold: float) -> List[Dict]:
        """Фильтрует монеты с изменениями цен, превышающими пороговое значение."""
        significant_changes = []

        for ticker in data:
            if not isinstance(ticker, dict):
                logger.info(f"Пропущен элемент, так как он не является словарём: {ticker}")
                continue

            try:
                symbol = ticker['symbol']
                last_price = float(ticker['lastPrice'])
                prev_price_24h = float(ticker['prevPrice24h'])

                price_change = ((last_price - prev_price_24h) / prev_price_24h) * 100

                if abs(price_change) >= threshold:
                    significant_changes.append({
                        'symbol': symbol,
                        'price_change': price_change,
                        'last_price': last_price,
                        'prev_price_24h': prev_price_24h
                    })
                    # logger.info(f"Монета {symbol} отфильтрована: изменение {price_change:.2f}%")
                    
            except (TypeError, ValueError, KeyError) as e:
                logger.info(f"Ошибка при обработке данных для {ticker.get('symbol', 'неизвестный символ')}: {e}")

        return significant_changes

    def get_exchange_name(self) -> str:
        """Возвращает название биржи."""
        return "Bybit"
