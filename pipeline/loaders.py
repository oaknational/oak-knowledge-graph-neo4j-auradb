import os
import pandas as pd
from typing import Dict, List, Tuple
from models.neo4j import Neo4jImportCommand


class Neo4jLoader:
    def __init__(self, import_dir: str = "data", database_name: str = "neo4j"):
        self.import_dir = import_dir
        self.database_name = database_name

    def generate_import_command(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Neo4jImportCommand:
        if not node_files and not relationship_files:
            raise ValueError("No CSV files provided for import")

        # Validate all files exist and are accessible
        all_files = node_files + relationship_files
        for file_path in all_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Build neo4j-admin import command
        command_parts = ["neo4j-admin", "database", "import", "full"]

        # Add database name
        command_parts.extend(["--database", self.database_name])

        # Add node files
        for node_file in node_files:
            command_parts.extend(["--nodes", node_file])

        # Add relationship files
        for rel_file in relationship_files:
            command_parts.extend(["--relationships", rel_file])

        # Add common import options for performance and reliability
        command_parts.extend(
            [
                "--delimiter",
                ",",
                "--array-delimiter",
                ";",
                "--quote",
                '"',
                "--multiline-fields",
                "true",
            ]
        )

        command = " ".join(command_parts)

        return Neo4jImportCommand(
            database_name=self.database_name,
            node_files=node_files,
            relationship_files=relationship_files,
            command=command,
        )

    def validate_csv_format(self, csv_path: str) -> Tuple[bool, List[str]]:
        if not os.path.exists(csv_path):
            return False, [f"CSV file does not exist: {csv_path}"]

        try:
            df = pd.read_csv(csv_path, nrows=0)  # Read only headers for validation
            errors = []

            # Determine file type based on required columns
            is_node_file = ":ID" in df.columns and ":LABEL" in df.columns
            is_rel_file = all(
                col in df.columns for col in [":START_ID", ":END_ID", ":TYPE"]
            )

            if not is_node_file and not is_rel_file:
                errors.append(
                    "File is neither a valid node file (:ID, :LABEL columns) "
                    "nor relationship file (:START_ID, :END_ID, :TYPE columns)"
                )
                return False, errors

            if is_node_file:
                errors.extend(self._validate_node_file_format(df))
            if is_rel_file:
                errors.extend(self._validate_relationship_file_format(df))

            return len(errors) == 0, errors

        except Exception as e:
            return False, [f"Error reading CSV file: {str(e)}"]

    def _validate_node_file_format(self, df: pd.DataFrame) -> List[str]:
        errors = []

        # Check required columns
        if ":ID" not in df.columns:
            errors.append("Missing required :ID column for node file")
        if ":LABEL" not in df.columns:
            errors.append("Missing required :LABEL column for node file")

        # Validate type annotations for property columns
        for col in df.columns:
            if col not in [":ID", ":LABEL"]:
                if ":" not in col:
                    errors.append(f"Property column '{col}' missing type annotation")
                else:
                    # Validate type annotation format
                    parts = col.split(":")
                    if len(parts) != 2:
                        errors.append(f"Invalid type annotation format in '{col}'")
                    else:
                        prop_name, type_annotation = parts
                        valid_types = [
                            "string",
                            "int",
                            "float",
                            "boolean",
                            "long",
                            "double",
                        ]
                        if type_annotation not in valid_types:
                            errors.append(
                                f"Invalid type '{type_annotation}' in column '{col}'. "
                                f"Valid types: {valid_types}"
                            )

        return errors

    def _validate_relationship_file_format(self, df: pd.DataFrame) -> List[str]:
        errors = []

        # Check required columns
        required_columns = [":START_ID", ":END_ID", ":TYPE"]
        for req_col in required_columns:
            if req_col not in df.columns:
                errors.append(
                    f"Missing required {req_col} column for relationship file"
                )

        # Validate type annotations for property columns
        for col in df.columns:
            if col not in required_columns:
                if ":" not in col:
                    errors.append(f"Property column '{col}' missing type annotation")
                else:
                    # Validate type annotation format
                    parts = col.split(":")
                    if len(parts) != 2:
                        errors.append(f"Invalid type annotation format in '{col}'")
                    else:
                        prop_name, type_annotation = parts
                        valid_types = [
                            "string",
                            "int",
                            "float",
                            "boolean",
                            "long",
                            "double",
                        ]
                        if type_annotation not in valid_types:
                            errors.append(
                                f"Invalid type '{type_annotation}' in column '{col}'. "
                                f"Valid types: {valid_types}"
                            )

        return errors

    def validate_import_files(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        validation_results = {"node_files": {}, "relationship_files": {}}
        all_valid = True

        # Validate node files
        for node_file in node_files:
            is_valid, errors = self.validate_csv_format(node_file)
            validation_results["node_files"][node_file] = errors
            if not is_valid:
                all_valid = False

        # Validate relationship files
        for rel_file in relationship_files:
            is_valid, errors = self.validate_csv_format(rel_file)
            validation_results["relationship_files"][rel_file] = errors
            if not is_valid:
                all_valid = False

        return all_valid, validation_results

    def generate_import_statistics(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Dict[str, any]:
        stats = {
            "total_files": len(node_files) + len(relationship_files),
            "node_files_count": len(node_files),
            "relationship_files_count": len(relationship_files),
            "total_nodes": 0,
            "total_relationships": 0,
            "node_files": [],
            "relationship_files": [],
            "estimated_import_time": 0,
            "database_name": self.database_name,
        }

        # Analyze node files
        for node_file in node_files:
            if os.path.exists(node_file):
                try:
                    df = pd.read_csv(node_file)
                    file_stats = {
                        "file": os.path.basename(node_file),
                        "path": node_file,
                        "records": len(df),
                        "columns": len(df.columns),
                        "size_mb": round(os.path.getsize(node_file) / (1024 * 1024), 2),
                    }

                    # Extract label from :LABEL column if available
                    if ":LABEL" in df.columns and not df.empty:
                        unique_labels = df[":LABEL"].unique()
                        file_stats["labels"] = unique_labels.tolist()

                    stats["node_files"].append(file_stats)
                    stats["total_nodes"] += len(df)
                except Exception as e:
                    stats["node_files"].append(
                        {
                            "file": os.path.basename(node_file),
                            "path": node_file,
                            "error": str(e),
                        }
                    )

        # Analyze relationship files
        for rel_file in relationship_files:
            if os.path.exists(rel_file):
                try:
                    df = pd.read_csv(rel_file)
                    file_stats = {
                        "file": os.path.basename(rel_file),
                        "path": rel_file,
                        "records": len(df),
                        "columns": len(df.columns),
                        "size_mb": round(os.path.getsize(rel_file) / (1024 * 1024), 2),
                    }

                    # Extract relationship type from :TYPE column if available
                    if ":TYPE" in df.columns and not df.empty:
                        unique_types = df[":TYPE"].unique()
                        file_stats["types"] = unique_types.tolist()

                    stats["relationship_files"].append(file_stats)
                    stats["total_relationships"] += len(df)
                except Exception as e:
                    stats["relationship_files"].append(
                        {
                            "file": os.path.basename(rel_file),
                            "path": rel_file,
                            "error": str(e),
                        }
                    )

        # Estimate import time (rough calculation: ~10k records per second)
        total_records = stats["total_nodes"] + stats["total_relationships"]
        stats["estimated_import_time"] = max(1, round(total_records / 10000))

        return stats

    def prepare_import_directory(self, target_dir: str = None) -> str:
        if target_dir is None:
            target_dir = os.path.join(self.import_dir, "import")

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        return target_dir

    def generate_import_summary(
        self, node_files: List[str], relationship_files: List[str]
    ) -> Dict[str, any]:
        # Validate files first
        validation_passed, validation_results = self.validate_import_files(
            node_files, relationship_files
        )

        # Generate statistics
        statistics = self.generate_import_statistics(node_files, relationship_files)

        # Generate import command
        try:
            import_command = self.generate_import_command(
                node_files, relationship_files
            )
            command_generated = True
            command_text = import_command.command
        except Exception as e:
            command_generated = False
            command_text = f"Error generating command: {str(e)}"

        summary = {
            "validation": {"passed": validation_passed, "details": validation_results},
            "statistics": statistics,
            "import_command": {
                "generated": command_generated,
                "command": command_text,
                "database": self.database_name,
            },
            "ready_for_import": validation_passed and command_generated,
        }

        return summary
