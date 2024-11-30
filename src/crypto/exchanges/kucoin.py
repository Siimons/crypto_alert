from kucoin.client import Market

from typing import List, Dict
from src.crypto.exchange import Exchange

from src.utils.logging_config import logger
from src.config import KUCOIN_API_KEY, KUCOIN_API_SECRET, KUCOIN_API_PASSPHRASE


class KuCoin(Exchange):
    """Класс для работы с API KuCoin."""
    
    def __init__(self, api_key: str = KUCOIN_API_KEY, secret_key: str = KUCOIN_API_SECRET, passphrase: str = KUCOIN_API_PASSPHRASE):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.client = Market('https://api.kucoin.com')
        
    def fetch_market_data(self) -> List[Dict]:
        """Извлекает данные о рынке с биржи KuCoin."""
        try:
            response = self.client.get_all_tickers()
            # logger.info(f"Получен ответ от API: {response}")
            
            if 'ticker' not in response:
                raise Exception("Ошибка: отсутствует ключ 'ticker' в ответе API")
            
            return response['ticker']
        
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
            
            # logger.info(f"Ключи в текущем элементе: {list(ticker.keys())}")
            
            try:
                symbol = ticker.get('symbol')
                last_price = ticker.get('last')
                prev_price_24h = ticker.get('averagePrice')
                change_rate = ticker.get('changeRate')
                change_price = ticker.get('changePrice')

                last_price = float(last_price) if last_price is not None else 0.0

                if change_rate is not None:
                    price_change = float(change_rate) * 100
                    
                elif change_price is not None:
                    price_change = (float(change_price) / last_price) * 100 if last_price != 0 else None
                    
                elif prev_price_24h is not None:
                    prev_price_24h = float(prev_price_24h)
                    
                    if prev_price_24h > 0:
                        price_change = ((last_price - prev_price_24h) / prev_price_24h) * 100
                    else:
                        logger.warning(f"Пропущен тикер {symbol}, так как prev_price_24h равен 0.")
                        continue
                    
                else:
                    logger.warning(f"Пропущен тикер {symbol}: отсутствуют данные для расчёта изменения цены.")
                    continue

                if price_change is not None and abs(price_change) >= threshold:
                    significant_changes.append({
                        'symbol': symbol,
                        'price_change': price_change,
                        'last_price': last_price,
                        'prev_price_24h': prev_price_24h
                    })
                    logger.info(f"Монета {symbol} отфильтрована: изменение {price_change:.2f}%")

            except (TypeError, ValueError) as e:
                logger.error(f"Ошибка при обработке данных для {symbol}: {e}")

        return significant_changes
    
    def get_exchange_name(self) -> str:
        """Возвращает название биржи."""
        return "KuCoin"
