import redis
import json

from decouple import config
from typing import Optional, Dict

from src.utils.logging_config import logger


class RedisConfig:
    """Базовый класс для подключения к Redis и управления клиентом Redis."""
    
    def __init__(self):
        self.host = config('REDIS_HOST', default='localhost')
        self.port = int(config('REDIS_PORT', default=6379))
        self.db = int(config('REDIS_DB', default=0))
        self.password = config('REDIS_PASSWORD', default=None)
        self.client = self.connect()

    def connect(self):
        """Устанавливает соединение с Redis и возвращает Redis клиента."""
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
        """Проверяет соединение и при необходимости переподключается к Redis."""
        try:
            self.client.ping()
        except redis.ConnectionError:
            self.client = self.connect()


class RedisChatManager(RedisConfig):
    """Класс для управления активными чатами и данными пользователей в Redis, включая статус мониторинга."""
    
    def __init__(self):
        super().__init__()
        self.hash_name = "active_chats"

    def add_user(self, user_id: int, chat_id: int, username: str, is_monitoring_active: bool = False):
        """
        Добавляет или обновляет данные пользователя в хеш-таблице Redis.
        
        :param user_id: Идентификатор пользователя.
        :param chat_id: Идентификатор чата, связанного с пользователем.
        :param username: Имя пользователя.
        :param is_monitoring_active: Статус активности мониторинга (по умолчанию False).
        """
        self.reconnect_if_needed()
        self.client.hset(
            f"{self.hash_name}:{user_id}", 
            mapping={
                "chat_id": chat_id, 
                "username": username, 
                "is_monitoring_active": int(is_monitoring_active)
            }
        )
        logger.info(f"Пользователь добавлен/обновлен: user_id='{user_id}', chat_id='{chat_id}', username='{username}', мониторинг активен={is_monitoring_active}")

    def get_user_data(self, user_id: int) -> Optional[Dict[str, str]]:
        """
        Получает данные пользователя по user_id.
        
        :param user_id: Идентификатор пользователя.
        :return: Словарь с данными пользователя или None, если данные отсутствуют.
        """
        self.reconnect_if_needed()
        user_data = self.client.hgetall(f"{self.hash_name}:{user_id}")
        if user_data:
            logger.info(f"Получены данные для user_id='{user_id}': {user_data}")
            return user_data
        else:
            logger.info(f"Данные для user_id='{user_id}' не найдены")
            return None

    def get_chat_id(self, user_id: int) -> Optional[int]:
        """
        Получает ID чата для указанного пользователя.
        
        :param user_id: Идентификатор пользователя.
        :return: Идентификатор чата или None, если данные отсутствуют.
        """
        self.reconnect_if_needed()
        chat_id = self.client.hget(f"{self.hash_name}:{user_id}", "chat_id")
        logger.info(f"Получен ID чата для user_id='{user_id}': {chat_id}")
        return int(chat_id) if chat_id else None

    def set_monitoring_status(self, user_id: int, is_active: bool):
        """
        Устанавливает статус активности мониторинга для пользователя.
        
        :param user_id: Идентификатор пользователя.
        :param is_active: Статус активности мониторинга (True или False).
        """
        self.reconnect_if_needed()
        self.client.hset(f"{self.hash_name}:{user_id}", "is_monitoring_active", int(is_active))
        logger.info(f"Статус мониторинга для user_id='{user_id}' установлен на {is_active}")

    def get_monitoring_status(self, user_id: int) -> bool:
        """
        Получает статус активности мониторинга для пользователя.
        
        :param user_id: Идентификатор пользователя.
        :return: True, если мониторинг активен, иначе False.
        """
        self.reconnect_if_needed()
        status = self.client.hget(f"{self.hash_name}:{user_id}", "is_monitoring_active")
        return bool(int(status)) if status else False

    def remove_user(self, user_id: int):
        """
        Удаляет данные пользователя по user_id из Redis.
        
        :param user_id: Идентификатор пользователя.
        """
        self.reconnect_if_needed()
        self.client.delete(f"{self.hash_name}:{user_id}")
        logger.info(f"Удалён пользователь с user_id='{user_id}'")

    def get_all_chats(self) -> Dict[int, Dict[str, str]]:
        """
        Возвращает данные всех активных чатов.
        
        :return: Словарь с данными всех пользователей, формата {user_id: {chat_id, username, is_monitoring_active}}.
        """
        self.reconnect_if_needed()
        active_chats = {}
        for key in self.client.keys(f"{self.hash_name}:*"):
            user_id = int(key.replace(f"{self.hash_name}:", ""))
            user_data = self.client.hgetall(key)
            if user_data:
                user_data["is_monitoring_active"] = bool(int(user_data.get("is_monitoring_active", 0)))
                active_chats[user_id] = user_data
        logger.info("Получены данные всех активных чатов")
        return active_chats


class RedisCacheManager(RedisConfig):
    """Класс для кэширования данных с бирж в Redis с поддержкой временного хранения."""

    def __init__(self):
        super().__init__()
        self.cache_prefix = "exchange_data:"

    def save_data(self, exchange_name: str, data: dict, ttl: Optional[int] = None):
        """
        Сохраняет данные биржи в кэше с возможностью временного хранения.
        
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