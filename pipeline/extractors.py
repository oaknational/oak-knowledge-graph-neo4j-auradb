from abc import ABC, abstractmethod
from typing import Dict, List
from models.config import PipelineConfig


class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, config: PipelineConfig) -> List[Dict]:
        pass


class ExtractorFactory:
    _strategies = {}

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        cls._strategies[name] = strategy_class

    @classmethod
    def create_extractor(cls, strategy_name: str) -> ExtractionStrategy:
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown extraction strategy: {strategy_name}")
        return cls._strategies[strategy_name]()

    @classmethod
    def get_available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())
