from abc import ABC, abstractmethod
from typing import List, Dict


class Exchange(ABC):
    """Абстрактный базовый класс для всех бирж."""

    @abstractmethod
    def fetch_market_data(self) -> List[Dict]:
        """Метод для извлечения данных с биржи. Должен быть реализован в каждом наследующем классе."""
        pass

    @abstractmethod
    def filter_significant_changes(self, data: List[Dict], threshold: float) -> List[Dict]:
        """Фильтрует монеты с изменениями цен, превышающими пороговое значение."""
        pass
