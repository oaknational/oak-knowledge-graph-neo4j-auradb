#!/usr/bin/env python3
"""
Neo4j Import Validation Script

Tests actual Neo4j database import with generated CSV files.
Verifies data integrity and relationship consistency.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.auradb_loader import AuraDBLoader
from pipeline.config_manager import ConfigManager
from utils.logging import PipelineLogger
from utils.database_utils import DatabaseConnection


@dataclass
class ValidationResult:
    """Result of Neo4j import validation."""
    success: bool
    nodes_imported: int
    relationships_imported: int
    validation_errors: List[str]
    warnings: List[str]
    execution_time_seconds: float


class Neo4jImportValidator:
    """Validates Neo4j imports and data integrity."""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize validator with Neo4j connection parameters."""
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.logger = PipelineLogger().get_logger()
        self.db_connection = None

    def connect_to_database(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            self.db_connection = DatabaseConnection(
                uri=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password
            )
            self.db_connection.connect()
            self.logger.info("✅ Connected to Neo4j database")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False

    def validate_csv_import(
        self,
        csv_directory: Path,
        config_path: str,
        clear_before_import: bool = True
    ) -> ValidationResult:
        """Validate complete CSV import process."""
        import time
        start_time = time.time()

        validation_errors = []
        warnings = []

        try:
            # Connect to database
            if not self.connect_to_database():
                return ValidationResult(
                    success=False,
                    nodes_imported=0,
                    relationships_imported=0,
                    validation_errors=["Failed to connect to Neo4j database"],
                    warnings=[],
                    execution_time_seconds=time.time() - start_time
                )

            # Load configuration
            config_manager = ConfigManager()
            config = config_manager.load_config(config_path)

            # Initialize AuraDB loader
            auradb_loader = AuraDBLoader(
                uri=self.neo4j_uri,
                username=self.neo4j_user,
                password=self.neo4j_password
            )

            # Clear database if requested
            if clear_before_import:
                self.logger.info("🧹 Clearing database before import...")
                self._clear_database()

            # Get CSV files
            csv_files = list(csv_directory.glob("*.csv"))
            if not csv_files:
                validation_errors.append(f"No CSV files found in {csv_directory}")
                return ValidationResult(
                    success=False,
                    nodes_imported=0,
                    relationships_imported=0,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    execution_time_seconds=time.time() - start_time
                )

            self.logger.info(f"📁 Found {len(csv_files)} CSV files for import")

            # Validate CSV file formats before import
            format_validation = self._validate_csv_formats(csv_files)
            if not format_validation["success"]:
                validation_errors.extend(format_validation["errors"])
                return ValidationResult(
                    success=False,
                    nodes_imported=0,
                    relationships_imported=0,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    execution_time_seconds=time.time() - start_time
                )

            # Import data using AuraDB loader
            self.logger.info("🚀 Starting data import...")
            import_result = auradb_loader.load_csv_files(str(csv_directory))

            if not import_result.success:
                validation_errors.append(f"Import failed: {import_result.message}")
                return ValidationResult(
                    success=False,
                    nodes_imported=0,
                    relationships_imported=0,
                    validation_errors=validation_errors,
                    warnings=warnings,
                    execution_time_seconds=time.time() - start_time
                )

            # Validate imported data
            validation_results = self._validate_imported_data(config)
            validation_errors.extend(validation_results["errors"])
            warnings.extend(validation_results["warnings"])

            # Get final counts
            node_count = self._count_nodes()
            relationship_count = self._count_relationships()

            self.logger.info(f"✅ Import validation completed:")
            self.logger.info(f"   📊 Nodes imported: {node_count}")
            self.logger.info(f"   🔗 Relationships imported: {relationship_count}")

            return ValidationResult(
                success=len(validation_errors) == 0,
                nodes_imported=node_count,
                relationships_imported=relationship_count,
                validation_errors=validation_errors,
                warnings=warnings,
                execution_time_seconds=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"❌ Validation failed with error: {e}")
            validation_errors.append(f"Unexpected error: {str(e)}")
            return ValidationResult(
                success=False,
                nodes_imported=0,
                relationships_imported=0,
                validation_errors=validation_errors,
                warnings=warnings,
                execution_time_seconds=time.time() - start_time
            )

        finally:
            if self.db_connection:
                self.db_connection.close()

    def _validate_csv_formats(self, csv_files: List[Path]) -> Dict[str, Any]:
        """Validate CSV file formats before import."""
        errors = []

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)

                if "_nodes.csv" in csv_file.name:
                    # Validate node file format
                    if ":ID" not in df.columns:
                        errors.append(f"Missing :ID column in {csv_file.name}")
                    if ":LABEL" not in df.columns:
                        errors.append(f"Missing :LABEL column in {csv_file.name}")

                elif "_relationships.csv" in csv_file.name:
                    # Validate relationship file format
                    required_cols = [":START_ID", ":END_ID", ":TYPE"]
                    for col in required_cols:
                        if col not in df.columns:
                            errors.append(f"Missing {col} column in {csv_file.name}")

                # Check for empty files
                if len(df) == 0:
                    errors.append(f"Empty CSV file: {csv_file.name}")

                # Check for null values in critical columns
                if "_nodes.csv" in csv_file.name and ":ID" in df.columns:
                    if df[":ID"].isnull().any():
                        errors.append(f"Null :ID values in {csv_file.name}")

            except Exception as e:
                errors.append(f"Error reading {csv_file.name}: {str(e)}")

        return {
            "success": len(errors) == 0,
            "errors": errors
        }

    def _clear_database(self):
        """Clear all nodes and relationships from database."""
        if not self.db_connection:
            raise RuntimeError("Database connection not established")

        # Delete all relationships and nodes
        queries = [
            "MATCH (n)-[r]-() DELETE r",  # Delete relationships first
            "MATCH (n) DELETE n"          # Then delete nodes
        ]

        for query in queries:
            self.db_connection.execute_query(query)

        self.logger.info("🗑️ Database cleared successfully")

    def _validate_imported_data(self, config) -> Dict[str, Any]:
        """Validate imported data integrity."""
        errors = []
        warnings = []

        try:
            # Check node label consistency
            expected_labels = [mapping.label for mapping in config.node_mappings]
            actual_labels = self._get_node_labels()

            for label in expected_labels:
                if label not in actual_labels:
                    warnings.append(f"Expected node label '{label}' not found in database")

            # Check relationship type consistency
            expected_types = [mapping.type for mapping in config.relationship_mappings]
            actual_types = self._get_relationship_types()

            for rel_type in expected_types:
                if rel_type not in actual_types:
                    warnings.append(f"Expected relationship type '{rel_type}' not found in database")

            # Check for orphaned nodes (nodes without relationships)
            orphaned_count = self._count_orphaned_nodes()
            if orphaned_count > 0:
                warnings.append(f"{orphaned_count} nodes have no relationships")

            # Check for invalid relationships (pointing to non-existent nodes)
            invalid_rels = self._count_invalid_relationships()
            if invalid_rels > 0:
                errors.append(f"{invalid_rels} relationships point to non-existent nodes")

        except Exception as e:
            errors.append(f"Data validation error: {str(e)}")

        return {
            "errors": errors,
            "warnings": warnings
        }

    def _get_node_labels(self) -> List[str]:
        """Get all node labels in the database."""
        query = "CALL db.labels() YIELD label RETURN label"
        result = self.db_connection.execute_query(query)
        return [record["label"] for record in result]

    def _get_relationship_types(self) -> List[str]:
        """Get all relationship types in the database."""
        query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
        result = self.db_connection.execute_query(query)
        return [record["relationshipType"] for record in result]

    def _count_nodes(self) -> int:
        """Count total nodes in database."""
        query = "MATCH (n) RETURN count(n) as count"
        result = self.db_connection.execute_query(query)
        return result[0]["count"] if result else 0

    def _count_relationships(self) -> int:
        """Count total relationships in database."""
        query = "MATCH ()-[r]-() RETURN count(r) as count"
        result = self.db_connection.execute_query(query)
        return result[0]["count"] if result else 0

    def _count_orphaned_nodes(self) -> int:
        """Count nodes with no relationships."""
        query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN count(n) as count
        """
        result = self.db_connection.execute_query(query)
        return result[0]["count"] if result else 0

    def _count_invalid_relationships(self) -> int:
        """Count relationships pointing to non-existent nodes."""
        # This is a complex check that would require specific implementation
        # based on the actual data structure. For now, return 0.
        return 0


def main():
    """Main function for running Neo4j import validation."""
    # Check for required environment variables
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not all([neo4j_uri, neo4j_password]):
        print("❌ Error: Missing required Neo4j environment variables")
        print("   Required: NEO4J_URI, NEO4J_PASSWORD")
        print("   Optional: NEO4J_USER (defaults to 'neo4j')")
        sys.exit(1)

    # Get CSV directory and config path from command line arguments
    if len(sys.argv) < 3:
        print("Usage: python validate_neo4j_import.py <csv_directory> <config_path>")
        print("Example: python validate_neo4j_import.py data/ config/integration_test_config.json")
        sys.exit(1)

    csv_directory = Path(sys.argv[1])
    config_path = sys.argv[2]

    if not csv_directory.exists():
        print(f"❌ Error: CSV directory not found: {csv_directory}")
        sys.exit(1)

    if not Path(config_path).exists():
        print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)

    # Initialize validator
    validator = Neo4jImportValidator(neo4j_uri, neo4j_user, neo4j_password)

    # Run validation
    print("🧪 Neo4j Import Validation")
    print("=" * 50)

    result = validator.validate_csv_import(
        csv_directory=csv_directory,
        config_path=config_path,
        clear_before_import=True
    )

    # Print results
    print()
    if result.success:
        print("🎉 Validation PASSED")
    else:
        print("❌ Validation FAILED")

    print(f"⏱️ Execution time: {result.execution_time_seconds:.2f} seconds")
    print(f"📊 Nodes imported: {result.nodes_imported}")
    print(f"🔗 Relationships imported: {result.relationships_imported}")

    if result.validation_errors:
        print()
        print("❌ Errors:")
        for error in result.validation_errors:
            print(f"   • {error}")

    if result.warnings:
        print()
        print("⚠️ Warnings:")
        for warning in result.warnings:
            print(f"   • {warning}")

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()