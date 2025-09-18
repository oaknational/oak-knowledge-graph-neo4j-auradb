from abc import ABC, abstractmethod
from typing import Dict, List
from pandas import DataFrame
from models.config import NodeMapping, RelationshipMapping


class TransformationStrategy(ABC):
    @abstractmethod
    def transform(self, data: List[Dict], mapping: NodeMapping) -> DataFrame:
        pass


class RelationshipTransformationStrategy(ABC):
    @abstractmethod
    def transform_relationships(
        self, data: List[Dict], mapping: RelationshipMapping
    ) -> DataFrame:
        pass


class TransformerFactory:
    _node_strategies = {}
    _relationship_strategies = {}

    @classmethod
    def register_node_strategy(cls, name: str, strategy_class: type):
        cls._node_strategies[name] = strategy_class

    @classmethod
    def register_relationship_strategy(cls, name: str, strategy_class: type):
        cls._relationship_strategies[name] = strategy_class

    @classmethod
    def create_node_transformer(
        cls, strategy_name: str
    ) -> TransformationStrategy:
        if strategy_name not in cls._node_strategies:
            raise ValueError(
                f"Unknown node transformation strategy: {strategy_name}"
            )
        return cls._node_strategies[strategy_name]()

    @classmethod
    def create_relationship_transformer(
        cls, strategy_name: str
    ) -> RelationshipTransformationStrategy:
        if strategy_name not in cls._relationship_strategies:
            raise ValueError(
                f"Unknown relationship transformation strategy: "
                f"{strategy_name}"
            )
        return cls._relationship_strategies[strategy_name]()

    @classmethod
    def get_available_node_strategies(cls) -> List[str]:
        return list(cls._node_strategies.keys())

    @classmethod
    def get_available_relationship_strategies(cls) -> List[str]:
        return list(cls._relationship_strategies.keys())
