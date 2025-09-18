import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import ValidationError

from models.config import PipelineConfig


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

    def load_config(self, config_file: str) -> PipelineConfig:
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

        config_data = self._substitute_env_vars(config_data)

        try:
            return PipelineConfig(**config_data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                error_details.append(f"  {field}: {message}")

            raise ConfigurationError(
                f"Configuration validation failed in {config_path}:\n"
                + "\n".join(error_details)
            )

    def save_config(self, config: PipelineConfig, config_file: str) -> None:
        config_path = self.config_dir / config_file

        try:
            config_dict = config.dict()
            with open(config_path, "w") as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {config_path}: {e}"
            )

    def list_configs(self) -> list[str]:
        try:
            return [f.name for f in self.config_dir.iterdir() if f.suffix == ".json"]
        except Exception as e:
            raise ConfigurationError(f"Failed to list configurations: {e}")

    def validate_config_file(self, config_file: str) -> tuple[bool, Optional[str]]:
        try:
            self.load_config(config_file)
            return True, None
        except ConfigurationError as e:
            return False, str(e)

    def _substitute_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
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
