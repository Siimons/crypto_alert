import redis
import json

from decouple import config
from typing import Optional

from src.utils.logging_config import logger


class RedisConfig:
    """Базовый класс для подключения к Redis и управления клиентом."""
    def __init__(self):
        self.host = config('REDIS_HOST', default='localhost')
        self.port = int(config('REDIS_PORT', default=6379))
        self.db = int(config('REDIS_DB', default=0))
        self.password = config('REDIS_PASSWORD', default=None)
        self.client = self.connect()

    def connect(self):
        """Устанавливает соединение с Redis и возвращает клиента."""
        connection_params = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "decode_responses": True
        }
        
        if self.password:
            connection_params["password"] = self.password
        
        return redis.StrictRedis(**connection_params)

    def reconnect_if_needed(self):
        """Проверяет соединение и переподключается при необходимости."""
        try:
            self.client.ping()
        except redis.ConnectionError:
            self.client = self.connect()


class RedisChatManager(RedisConfig):
    """Класс для управления активными чатами в формате hash-таблицы Redis."""

    def __init__(self):
        super().__init__()
        self.hash_name = "active_chats"

    def add_chat(self, username: str, chat_id: int):
        """Добавляет чат в hash-таблицу с именем пользователя как ключом и ID чата как значением."""
        self.reconnect_if_needed()
        self.client.hset(self.hash_name, username, chat_id)
        logger.info(f"Чат добавлен для пользователя '{username}' с ID чата '{chat_id}'")

    def get_chat_id(self, username: str):
        """Получает ID чата по имени пользователя."""
        self.reconnect_if_needed()
        chat_id = self.client.hget(self.hash_name, username)
        logger.info(f"Получен ID чата для пользователя '{username}': {chat_id}")
        return chat_id

    def remove_chat(self, username: str):
        """Удаляет чат из hash-таблицы по имени пользователя."""
        self.reconnect_if_needed()
        self.client.hdel(self.hash_name, username)
        logger.info(f"Чат удален для пользователя '{username}'")

    def get_all_chats(self):
        """Возвращает все активные чаты в формате словаря."""
        self.reconnect_if_needed()
        chats = self.client.hgetall(self.hash_name)
        logger.info("Получены все активные чаты")
        return chats


class RedisCacheManager(RedisConfig):
    """Класс для кэширования данных с бирж в Redis с поддержкой времени жизни кэша."""

    def __init__(self):
        super().__init__()
        self.cache_prefix = "exchange_data:"

    def save_data(self, exchange_name: str, data: dict, ttl: Optional[int] = None):
        """
        Сохраняет данные биржи с временным хранением.
        :param exchange_name: Название биржи для формирования ключа.
        :param data: Данные, которые нужно сохранить.
        :param ttl: Время жизни данных в секундах (если указано).
        """
        self.reconnect_if_needed()
        key = f"{self.cache_prefix}{exchange_name}"
        self.client.set(key, json.dumps(data))
        logger.info(f"Данные для '{exchange_name}' сохранены с TTL: {ttl if ttl else 'Без TTL'}")
        
        if ttl is not None:
            self.client.expire(key, ttl)

    def get_data(self, exchange_name: str):
        """
        Получает данные биржи по её имени.
        :param exchange_name: Название биржи для формирования ключа.
        :return: Декодированные данные или None, если ключ не существует.
        """
        self.reconnect_if_needed()
        key = f"{self.cache_prefix}{exchange_name}"
        data = self.client.get(key)
        logger.info(f"Получены данные для '{exchange_name}': {data}")
        return json.loads(data) if data else None

    def clear_cache(self, exchange_name: str):
        """
        Очищает кэшированные данные по имени биржи.
        :param exchange_name: Название биржи для формирования ключа.
        """
        self.reconnect_if_needed()
        key = f"{self.cache_prefix}{exchange_name}"
        self.client.delete(key)
        logger.info(f"Кэш очищен для '{exchange_name}'")
        
        
# if __name__ == "__main__":
#     chat_manager = RedisChatManager()
#     cache_manager = RedisCacheManager()
    
#     logger.info("=== Тестирование RedisChatManager ===")
#     chat_manager.add_chat("Simon", 67890)
#     chat_id = chat_manager.get_chat_id("Simon")
#     logger.info(f"Чат добавлен для Simon с ID: {chat_id}")
#     chat_manager.remove_chat("Simon")
    
#     logger.info("=== Тестирование RedisCacheManager ===")
#     test_data = {"price": 50000, "currency": "BTC"}
#     cache_manager.save_data("binance", test_data, ttl=3600)
#     data = cache_manager.get_data("binance")
#     logger.info(f"Получены данные из кэша для 'binance': {data}")
