import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigurationError(Exception):
    pass


class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        if not self.config_dir.exists():
            raise ConfigurationError(
                f"Configuration directory {self.config_dir} does not exist"
            )

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load and validate configuration from JSON file."""
        config_path = self.config_dir / config_file

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file {config_path} does not exist")

        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to read {config_path}: {e}")

        # Substitute environment variables
        config_data = self._substitute_env_vars(config_data)

        # Simple validation
        self._validate_config(config_data)

        return config_data

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Simple validation of required configuration keys."""
        required_keys = ["hasura_endpoint", "materialized_views", "join_strategy"]

        for key in required_keys:
            if key not in config:
                raise ConfigurationError(f"Missing required configuration key: {key}")

        # Validate materialized_views is a dict (view_name -> field_list)
        if not isinstance(config["materialized_views"], dict):
            raise ConfigurationError(
                "materialized_views must be a dict mapping view names to field lists"
            )

        # Validate join_strategy (now required)
        self._validate_join_strategy(
            config["join_strategy"], config["materialized_views"]
        )

        # Handle legacy config format and convert to new format
        if "schema_mapping" not in config:
            if "node_mappings" in config or "relationship_mappings" in config:
                # Convert old format to new format
                config["schema_mapping"] = self._convert_legacy_config(config)
            else:
                raise ConfigurationError(
                    "Configuration must contain 'schema_mapping' or legacy 'node_mappings'/'relationship_mappings'"
                )

        # Validate schema_mapping has required structure
        schema_mapping = config["schema_mapping"]
        if not isinstance(schema_mapping, dict):
            raise ConfigurationError("schema_mapping must be a dictionary")

    def _convert_legacy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy config format to new simplified format."""
        schema_mapping = {"nodes": {}, "relationships": {}}

        # Convert node_mappings
        if "node_mappings" in config:
            for node_mapping in config["node_mappings"]:
                label = node_mapping.get("label")
                if label:
                    schema_mapping["nodes"][label] = {
                        "id_field": node_mapping.get("id_field"),
                        "properties": {},
                    }

                    # Convert properties
                    properties = node_mapping.get("properties", {})
                    for prop_name, prop_config in properties.items():
                        if isinstance(prop_config, dict):
                            source_field = prop_config.get("source_field")
                            if source_field:
                                schema_mapping["nodes"][label]["properties"][
                                    prop_name
                                ] = source_field
                        else:
                            schema_mapping["nodes"][label]["properties"][
                                prop_name
                            ] = prop_config

        # Convert relationship_mappings
        if "relationship_mappings" in config:
            for rel_mapping in config["relationship_mappings"]:
                rel_type = rel_mapping.get("type")
                if rel_type:
                    schema_mapping["relationships"][rel_type] = {
                        "start_node_field": rel_mapping.get("start_node_id_field"),
                        "end_node_field": rel_mapping.get("end_node_id_field"),
                        "properties": {},
                    }

                    # Convert properties
                    properties = rel_mapping.get("properties", {})
                    for prop_name, prop_config in properties.items():
                        if isinstance(prop_config, dict):
                            source_field = prop_config.get("source_field")
                            if source_field:
                                schema_mapping["relationships"][rel_type]["properties"][
                                    prop_name
                                ] = source_field
                        else:
                            schema_mapping["relationships"][rel_type]["properties"][
                                prop_name
                            ] = prop_config

        return schema_mapping

    def save_config(self, config: Dict[str, Any], config_file: str) -> None:
        """Save configuration to JSON file."""
        config_path = self.config_dir / config_file

        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {config_path}: {e}"
            )

    def list_configs(self) -> list[str]:
        """List all JSON configuration files."""
        try:
            return [f.name for f in self.config_dir.iterdir() if f.suffix == ".json"]
        except Exception as e:
            raise ConfigurationError(f"Failed to list configurations: {e}")

    def validate_config_file(self, config_file: str) -> tuple[bool, Optional[str]]:
        """Validate a configuration file."""
        try:
            self.load_config(config_file)
            return True, None
        except ConfigurationError as e:
            return False, str(e)

    def _substitute_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration."""

        def substitute_value(value):
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                env_var = value[2:-1]
                env_value = os.getenv(env_var)
                if env_value is None:
                    raise ConfigurationError(
                        f"Environment variable {env_var} is not set"
                    )
                return env_value
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            return value

        return substitute_value(config_data)

    def _validate_join_strategy(
        self, join_strategy: Dict[str, Any], materialized_views: Dict[str, Any]
    ) -> None:
        """Validate join strategy configuration."""
        # Validate join strategy type
        strategy_type = join_strategy.get("type")
        if strategy_type not in ["single_source", "multi_source_join"]:
            raise ConfigurationError(
                "join_strategy.type must be 'single_source' or 'multi_source_join'"
            )

        # Validate primary_mv exists in materialized_views
        primary_mv = join_strategy.get("primary_mv")
        if primary_mv and primary_mv not in materialized_views:
            raise ConfigurationError(
                f"join_strategy.primary_mv '{primary_mv}' not found in materialized_views"
            )

        # Validate joins if present
        joins = join_strategy.get("joins", [])
        if strategy_type == "multi_source_join" and not joins:
            raise ConfigurationError(
                "multi_source_join strategy requires at least one join configuration"
            )

        for i, join_config in enumerate(joins):
            # Validate mv exists
            join_mv = join_config.get("mv")
            if join_mv not in materialized_views:
                raise ConfigurationError(
                    f"Join {i}: mv '{join_mv}' not found in materialized_views"
                )

            # Validate join_type
            join_type = join_config.get("join_type", "inner")
            if join_type not in ["inner", "left", "right", "outer"]:
                raise ConfigurationError(
                    f"Join {i}: join_type must be 'inner', 'left', 'right', or 'outer'"
                )

            # Validate on clause
            on_clause = join_config.get("on")
            if not on_clause or not isinstance(on_clause, dict):
                raise ConfigurationError(
                    f"Join {i}: 'on' clause is required and must be a dict"
                )

            if "left_key" not in on_clause or "right_key" not in on_clause:
                raise ConfigurationError(
                    f"Join {i}: 'on' clause must contain 'left_key' and 'right_key'"
                )
