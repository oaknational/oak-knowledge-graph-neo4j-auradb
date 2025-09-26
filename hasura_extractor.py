import os
import requests
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional


class HasuraExtractor:
    """
    Simplified Hasura data extractor that queries materialized views
    and joins the data into a single consolidated CSV file.
    """

    def __init__(self, endpoint: str = None, output_dir: str = "data"):
        self.endpoint = endpoint or os.getenv("HASURA_ENDPOINT")
        self.api_key = os.getenv("HASURA_API_KEY")
        self.auth_type = os.getenv("OAK_AUTH_TYPE")
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)

        if not self.endpoint:
            raise ValueError(
                "HASURA_ENDPOINT environment variable or endpoint parameter required"
            )
        if not self.api_key:
            raise ValueError("HASURA_API_KEY environment variable required")
        if not self.auth_type:
            raise ValueError("OAK_AUTH_TYPE environment variable required")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_and_join(
        self,
        materialized_views: Dict[str, List[str]],
        join_strategy: Dict[str, Any],
        test_limit: Optional[int] = None,
    ) -> str:
        """
        Extract data from specified materialized views and join according to strategy.

        Args:
            materialized_views: Dict mapping view names to field lists
            join_strategy: JOIN strategy configuration
            test_limit: Optional limit on records per view for testing

        Returns:
            Path to the consolidated CSV file
        """
        strategy_type = join_strategy.get("type")

        if strategy_type == "single_source":
            return self._extract_single_source(
                materialized_views, join_strategy, test_limit
            )
        elif strategy_type == "multi_source_join":
            return self._extract_with_joins(
                materialized_views, join_strategy, test_limit
            )
        else:
            raise ValueError(f"Unsupported join strategy type: {strategy_type}")

    def _extract_single_source(
        self,
        materialized_views: Dict[str, List[str]],
        join_strategy: Dict[str, Any],
        test_limit: Optional[int] = None,
    ) -> str:
        """Extract data from a single primary materialized view."""
        primary_mv = join_strategy.get("primary_mv")

        if primary_mv not in materialized_views:
            raise ValueError(
                f"Primary MV '{primary_mv}' not found in materialized_views"
            )

        self.logger.info(f"Extracting data from single source: {primary_mv}")

        fields = materialized_views[primary_mv]
        data = self._query_materialized_view(primary_mv, fields, test_limit)

        if not data:
            raise ValueError(f"No data retrieved from {primary_mv}")

        consolidated_df = pd.DataFrame(data)
        consolidated_df["_source_view"] = primary_mv

        # Save to CSV
        csv_filename = "consolidated_data.csv"
        csv_path = self.output_dir / csv_filename
        consolidated_df.to_csv(csv_path, index=False)

        self.logger.info(f"Consolidated CSV saved: {csv_path}")
        self.logger.info(f"Total records: {len(consolidated_df)}")
        self.logger.info(f"Total columns: {len(consolidated_df.columns)}")

        return str(csv_path)

    def _extract_with_joins(
        self,
        materialized_views: Dict[str, List[str]],
        join_strategy: Dict[str, Any],
        test_limit: Optional[int] = None,
    ) -> str:
        """Extract data from multiple materialized views and join them."""
        primary_mv = join_strategy.get("primary_mv")
        joins = join_strategy.get("joins", [])

        if primary_mv not in materialized_views:
            raise ValueError(
                f"Primary MV '{primary_mv}' not found in materialized_views"
            )

        self.logger.info(
            f"Extracting data with {len(joins)} joins, primary MV: {primary_mv}"
        )

        # Extract primary dataset
        primary_fields = materialized_views[primary_mv]
        primary_data = self._query_materialized_view(
            primary_mv, primary_fields, test_limit
        )

        if not primary_data:
            raise ValueError(f"No data retrieved from primary MV {primary_mv}")

        result_df = pd.DataFrame(primary_data)
        result_df["_primary_source"] = primary_mv
        self.logger.info(f"Primary dataset: {len(result_df)} records from {primary_mv}")

        # Perform joins
        for i, join_config in enumerate(joins):
            join_mv = join_config["mv"]
            join_type = join_config.get("join_type", "inner")
            on_clause = join_config["on"]
            left_key = on_clause["left_key"]
            right_key = on_clause["right_key"]

            self.logger.info(
                f"Join {i+1}: {join_type} join with {join_mv} on {left_key}={right_key}"
            )

            # Extract join dataset
            join_fields = materialized_views[join_mv]
            join_data = self._query_materialized_view(join_mv, join_fields, test_limit)

            if not join_data:
                self.logger.warning(f"No data from {join_mv}, skipping join")
                continue

            join_df = pd.DataFrame(join_data)
            join_df[f"_source_{join_mv}"] = join_mv

            # Perform pandas merge
            how_mapping = {
                "inner": "inner",
                "left": "left",
                "right": "right",
                "outer": "outer",
            }
            result_df = result_df.merge(
                join_df,
                left_on=left_key,
                right_on=right_key,
                how=how_mapping[join_type],
                suffixes=("", f"_from_{join_mv}"),
            )

            self.logger.info(f"After join {i+1}: {len(result_df)} records")

        # Save to CSV
        csv_filename = "consolidated_data.csv"
        csv_path = self.output_dir / csv_filename
        result_df.to_csv(csv_path, index=False)

        self.logger.info(f"Consolidated CSV saved: {csv_path}")
        self.logger.info(f"Total records: {len(result_df)}")
        self.logger.info(f"Total columns: {len(result_df.columns)}")

        return str(csv_path)

    def _introspect_schema_fields(self, view_name: str) -> List[str]:
        """Use GraphQL introspection to discover available fields for the materialized view."""
        self.logger.info(
            f"Discovering fields for {view_name} via schema introspection..."
        )

        # Introspection query to get the specific field and its return type structure
        introspection_query = """
        query {
            __schema {
                queryType {
                    fields {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                                fields {
                                    name
                                    type {
                                        name
                                        kind
                                    }
                                }
                            }
                            fields {
                                name
                                type {
                                    name
                                    kind
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        headers = {
            "Content-Type": "application/json",
            "x-oak-auth-key": self.api_key,
            "x-oak-auth-type": self.auth_type,
        }

        payload = {"query": introspection_query}

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if "errors" in result:
                self.logger.warning(f"Introspection errors: {result['errors']}")
                return []

            # Find our specific view field in the query type
            query_fields = (
                result.get("data", {})
                .get("__schema", {})
                .get("queryType", {})
                .get("fields", [])
            )

            for field in query_fields:
                if field["name"] == view_name:
                    # Handle different GraphQL type structures
                    field_type = field.get("type", {})

                    # Check if it's a LIST type wrapping another type
                    if field_type.get("kind") == "LIST" and field_type.get("ofType"):
                        actual_type = field_type["ofType"]
                    else:
                        actual_type = field_type

                    # Extract fields from the actual type
                    type_fields = actual_type.get("fields", [])

                    if type_fields:
                        available_fields = []
                        for view_field in type_fields:
                            field_type_info = view_field.get("type", {})
                            field_kind = field_type_info.get("kind", "")
                            type_name = field_type_info.get("name", "")

                            # Include scalar types and simple types
                            if (
                                field_kind in ["SCALAR", "ENUM"]
                                or type_name
                                in ["String", "Int", "Float", "Boolean", "ID"]
                                or field_kind == "NON_NULL"
                            ):  # NON_NULL can wrap scalars
                                available_fields.append(view_field["name"])

                        self.logger.info(
                            f"Discovered {len(available_fields)} fields for {view_name}"
                        )
                        return available_fields

            self.logger.warning(f"Could not find {view_name} in schema")
            return []

        except Exception as e:
            self.logger.warning(f"Schema introspection failed: {e}")
            return []

    def _query_materialized_view(
        self, view_name: str, fields: List[str], limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query a single materialized view with specified fields."""
        self.logger.info(f"Querying {view_name} with {len(fields)} configured fields")

        # Build query with the provided fields
        query = self._build_graphql_query(view_name, fields, limit)

        headers = {
            "Content-Type": "application/json",
            "x-oak-auth-key": self.api_key,
            "x-oak-auth-type": self.auth_type,
        }

        payload = {"query": query}

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()

            response_data = response.json()

            if "errors" in response_data:
                error_messages = [error["message"] for error in response_data["errors"]]
                raise RuntimeError(f"GraphQL errors: {'; '.join(error_messages)}")

            if "data" not in response_data:
                raise RuntimeError("No data field in response")

            # Extract the actual data from the response
            view_data = response_data["data"].get(view_name, [])
            return view_data

        except requests.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")

    def _query_with_field_discovery(
        self, view_name: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query MV with field discovery by examining the first record to get all fields."""
        self.logger.info(
            f"Discovering fields by querying {view_name} with minimal fields first"
        )

        # Make a test query with just a few records to discover the structure
        test_limit = min(limit or 1000, 5)  # Use small number for discovery

        # Start with basic query - Hasura should return an error showing available fields
        test_query = f"""
        query {{
            {view_name}(limit: {test_limit})
        }}
        """

        headers = {
            "Content-Type": "application/json",
            "x-oak-auth-key": self.api_key,
            "x-oak-auth-type": self.auth_type,
        }

        try:
            response = requests.post(
                self.endpoint, json={"query": test_query}, headers=headers
            )
            response.raise_for_status()
            response_data = response.json()

            # If the query succeeds without field specification, we got all fields
            if "data" in response_data and view_name in response_data["data"]:
                data = response_data["data"][view_name]
                if data and len(data) > 0:
                    # Get all fields from the first record
                    available_fields = list(data[0].keys())
                    self.logger.info(
                        f"Discovered {len(available_fields)} fields from query response"
                    )

                    # Now make the full query with the discovered fields and proper limit
                    if limit and limit > test_limit:
                        full_query = self._build_graphql_query(
                            view_name, available_fields, limit
                        )
                        full_response = requests.post(
                            self.endpoint, json={"query": full_query}, headers=headers
                        )
                        full_response.raise_for_status()
                        full_data = full_response.json()
                        return full_data["data"].get(view_name, [])
                    else:
                        return data

        except Exception as e:
            self.logger.error(f"Field discovery query failed: {e}")
            raise RuntimeError(f"Unable to query {view_name}: {e}")

        return []

    def _build_graphql_query(
        self, view_name: str, fields: List[str], limit: Optional[int] = None
    ) -> str:
        """Build GraphQL query for a materialized view with specified fields."""
        limit_clause = f"(limit: {limit})" if limit else ""

        # Build the fields selection
        fields_selection = "\n                ".join(fields)

        query = f"""
        query {{
            {view_name}{limit_clause} {{
                {fields_selection}
            }}
        }}
        """

        return query
