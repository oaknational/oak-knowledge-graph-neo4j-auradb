from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import os
import pandas as pd
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


class CSVTransformer:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def transform_nodes_to_csv(
        self, node_data: pd.DataFrame, node_mapping: NodeMapping
    ) -> str:
        if node_data.empty:
            raise ValueError(
                f"No data to transform for node {node_mapping.label}"
            )

        # Validate required columns
        required_columns = [":ID", ":LABEL"]
        missing_columns = [
            col for col in required_columns if col not in node_data.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing required columns for node {node_mapping.label}: "
                f"{missing_columns}"
            )

        # Generate CSV with proper headers
        csv_data = node_data.copy()
        csv_filename = f"{node_mapping.label.lower()}_nodes.csv"
        csv_path = os.path.join(self.output_dir, csv_filename)

        # Apply Neo4j type annotations to headers
        typed_headers = self._generate_typed_headers(csv_data, node_mapping)
        csv_data.columns = typed_headers

        # Write CSV with optimizations for Neo4j bulk import
        csv_data.to_csv(
            csv_path,
            index=False,
            na_rep="",
            quoting=1,  # QUOTE_ALL for Neo4j compatibility
            encoding="utf-8",
        )

        return csv_path

    def transform_relationships_to_csv(
        self,
        relationship_data: pd.DataFrame,
        relationship_mapping: RelationshipMapping,
    ) -> str:
        if relationship_data.empty:
            raise ValueError(
                f"No data to transform for relationship "
                f"{relationship_mapping.type}"
            )

        # Validate required columns
        required_columns = [":START_ID", ":END_ID", ":TYPE"]
        missing_columns = [
            col for col in required_columns if col not in relationship_data.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing required columns for relationship "
                f"{relationship_mapping.type}: {missing_columns}"
            )

        # Generate CSV with proper headers
        csv_data = relationship_data.copy()
        csv_filename = f"{relationship_mapping.type.lower()}_relationships.csv"
        csv_path = os.path.join(self.output_dir, csv_filename)

        # Apply Neo4j type annotations to headers
        typed_headers = self._generate_typed_relationship_headers(
            csv_data, relationship_mapping
        )
        csv_data.columns = typed_headers

        # Write CSV with optimizations for Neo4j bulk import
        csv_data.to_csv(
            csv_path,
            index=False,
            na_rep="",
            quoting=1,  # QUOTE_ALL for Neo4j compatibility
            encoding="utf-8",
        )

        return csv_path

    def _generate_typed_headers(
        self, data: pd.DataFrame, node_mapping: NodeMapping
    ) -> List[str]:
        typed_headers = []

        for column in data.columns:
            if column == ":ID":
                typed_headers.append(":ID")
            elif column == ":LABEL":
                typed_headers.append(":LABEL")
            else:
                # Find the field mapping to get the target type
                field_type = self._get_field_type_from_mapping(
                    column, node_mapping
                )
                typed_headers.append(f"{column}:{field_type}")

        return typed_headers

    def _generate_typed_relationship_headers(
        self, data: pd.DataFrame, relationship_mapping: RelationshipMapping
    ) -> List[str]:
        typed_headers = []

        for column in data.columns:
            if column in [":START_ID", ":END_ID", ":TYPE"]:
                typed_headers.append(column)
            else:
                # Find the field mapping to get the target type
                field_type = self._get_relationship_field_type_from_mapping(
                    column, relationship_mapping
                )
                typed_headers.append(f"{column}:{field_type}")

        return typed_headers

    def _get_field_type_from_mapping(
        self, field_name: str, node_mapping: NodeMapping
    ) -> str:
        # Look up the field type from the node mapping configuration
        if field_name in node_mapping.properties:
            return node_mapping.properties[field_name].target_type

        # Default to string if not found in mapping
        return "string"

    def _get_relationship_field_type_from_mapping(
        self, field_name: str, relationship_mapping: RelationshipMapping
    ) -> str:
        # Look up the field type from the relationship mapping configuration
        if field_name in relationship_mapping.properties:
            return relationship_mapping.properties[field_name].target_type

        # Default to string if not found in mapping
        return "string"

    def generate_import_summary(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Dict[str, any]:
        summary = {
            "total_files": len(node_files) + len(relationship_files),
            "node_files": len(node_files),
            "relationship_files": len(relationship_files),
            "files": {"nodes": [], "relationships": []},
            "total_records": 0,
        }

        # Count records in node files
        for node_file in node_files:
            if os.path.exists(node_file):
                df = pd.read_csv(node_file)
                file_info = {
                    "file": os.path.basename(node_file),
                    "path": node_file,
                    "records": len(df),
                    "columns": len(df.columns),
                }
                summary["files"]["nodes"].append(file_info)
                summary["total_records"] += len(df)

        # Count records in relationship files
        for rel_file in relationship_files:
            if os.path.exists(rel_file):
                df = pd.read_csv(rel_file)
                file_info = {
                    "file": os.path.basename(rel_file),
                    "path": rel_file,
                    "records": len(df),
                    "columns": len(df.columns),
                }
                summary["files"]["relationships"].append(file_info)
                summary["total_records"] += len(df)

        return summary

    def validate_csv_format(
        self, csv_path: str, file_type: str
    ) -> Tuple[bool, List[str]]:
        if not os.path.exists(csv_path):
            return False, [f"CSV file does not exist: {csv_path}"]

        try:
            df = pd.read_csv(csv_path)
            errors = []

            if file_type == "node":
                # Validate node CSV format
                if ":ID" not in df.columns:
                    errors.append("Missing required :ID column for node file")
                if ":LABEL" not in df.columns:
                    errors.append("Missing required :LABEL column for node file")

                # Check for proper type annotations
                for col in df.columns:
                    if col not in [":ID", ":LABEL"] and ":" not in col:
                        errors.append(f"Column '{col}' missing type annotation")

            elif file_type == "relationship":
                # Validate relationship CSV format
                required_rel_columns = [":START_ID", ":END_ID", ":TYPE"]
                for req_col in required_rel_columns:
                    if req_col not in df.columns:
                        errors.append(
                            f"Missing required {req_col} column for relationship file"
                        )

                # Check for proper type annotations
                for col in df.columns:
                    if col not in required_rel_columns and ":" not in col:
                        errors.append(f"Column '{col}' missing type annotation")

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Error reading CSV file: {str(e)}"]


# Register CSVTransformer with the factory as the default strategy
class CSVNodeTransformationStrategy(TransformationStrategy):
    def __init__(self, output_dir: str = "data"):
        self.csv_transformer = CSVTransformer(output_dir)

    def transform(self, data: List[Dict], mapping: NodeMapping) -> pd.DataFrame:
        # This method should not be used directly for CSV transformation
        # CSVTransformer.transform_nodes_to_csv should be used instead
        raise NotImplementedError(
            "Use CSVTransformer.transform_nodes_to_csv for CSV generation"
        )


class CSVRelationshipTransformationStrategy(RelationshipTransformationStrategy):
    def __init__(self, output_dir: str = "data"):
        self.csv_transformer = CSVTransformer(output_dir)

    def transform_relationships(
        self, data: List[Dict], mapping: RelationshipMapping
    ) -> pd.DataFrame:
        # This method should not be used directly for CSV transformation
        # CSVTransformer.transform_relationships_to_csv should be used instead
        raise NotImplementedError(
            "Use CSVTransformer.transform_relationships_to_csv for CSV generation"
        )


# Auto-register strategies
TransformerFactory.register_node_strategy("csv", CSVNodeTransformationStrategy)
TransformerFactory.register_relationship_strategy(
    "csv", CSVRelationshipTransformationStrategy
)
