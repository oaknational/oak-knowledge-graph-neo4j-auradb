import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, List
from models.config import PipelineConfig
from models.hasura import HasuraResponse


class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self, config: PipelineConfig) -> List[Dict]:
        pass


class HasuraExtractor(ExtractionStrategy):
    def __init__(self, api_key: str = None, auth_type: str = None):
        self.api_key = api_key or os.getenv("HASURA_API_KEY")
        self.auth_type = auth_type or os.getenv("OAK_AUTH_TYPE")
        if not self.api_key:
            raise ValueError("Hasura API key required")
        if not self.auth_type:
            raise ValueError("Oak auth type required")

    def extract(self, config: PipelineConfig) -> List[Dict]:
        all_data = []

        for view_name, fields in config.materialized_views.items():
            try:
                view_data = self._query_materialized_view(
                    config.hasura_endpoint, view_name, fields, config.test_limit
                )
                all_data.extend(view_data)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to extract from view '{view_name}': {str(e)}"
                )

        return all_data

    def _query_materialized_view(
        self, endpoint: str, view_name: str, fields: List[str], limit: int = None
    ) -> List[Dict]:
        query = self._build_graphql_query(view_name, fields, limit)

        headers = {
            "Content-Type": "application/json",
            "x-oak-auth-key": self.api_key,
            "x-oak-auth-type": self.auth_type,
        }

        payload = {"query": query}

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()

            hasura_response = HasuraResponse.model_validate(response.json())

            if hasura_response.errors:
                errors = hasura_response.errors
                error_messages = [error.message for error in errors]
                raise RuntimeError(f"GraphQL errors: {error_messages}")

            data = hasura_response.data
            if not data or view_name not in data:
                raise RuntimeError(f"No data returned for view: {view_name}")

            return hasura_response.data[view_name]

        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")

    def _build_graphql_query(self, view_name: str, fields: List[str], limit: int = None) -> str:
        words = view_name.split("_")
        query_name = "Get" + "".join(word.capitalize() for word in words)

        # Add limit parameter to query if specified
        limit_clause = f"(limit: {limit})" if limit else ""

        # Build field selection from config
        field_selection = "\n            ".join(fields)

        return f"""
        query {query_name} {{
          {view_name}{limit_clause} {{
            {field_selection}
          }}
        }}
        """


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


# Register the HasuraExtractor strategy
ExtractorFactory.register_strategy("hasura", HasuraExtractor)
