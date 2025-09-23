import pandas as pd
import logging
from typing import Dict, List, Any
from uuid import uuid4


class SchemaMapper:
    """
    Simple schema mapper that transforms CSV data to knowledge graph format
    based on configuration mapping.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def map_from_csv(self, csv_file: str, schema_mapping: Dict[str, Any], output_dir: str = "data") -> Dict[str, Any]:
        """
        Map CSV data to knowledge graph schema and generate Neo4j CSV files.

        Args:
            csv_file: Path to the CSV file to process
            schema_mapping: Dictionary containing node and relationship mappings
            output_dir: Directory to save Neo4j CSV files

        Returns:
            Dictionary with CSV file paths for Neo4j loading
        """
        self.logger.info(f"Mapping CSV data from {csv_file}")

        # Load CSV data
        try:
            df = pd.read_csv(csv_file)
            self.logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        except Exception as e:
            raise ValueError(f"Failed to load CSV file: {e}")

        # Create output directory
        import os
        os.makedirs(output_dir, exist_ok=True)

        csv_files = {
            "node_files": [],
            "relationship_files": []
        }

        # Generate node CSV files
        if "nodes" in schema_mapping:
            node_files = self._generate_node_csvs(df, schema_mapping["nodes"], output_dir)
            csv_files["node_files"] = node_files

        # Generate relationship CSV files
        if "relationships" in schema_mapping:
            rel_files = self._generate_relationship_csvs(df, schema_mapping["relationships"], output_dir)
            csv_files["relationship_files"] = rel_files

        self.logger.info(f"Schema mapping completed:")
        self.logger.info(f"  Node CSV files: {len(csv_files['node_files'])}")
        self.logger.info(f"  Relationship CSV files: {len(csv_files['relationship_files'])}")

        return csv_files

    def _generate_node_csvs(self, df: pd.DataFrame, node_mappings: Dict[str, Any], output_dir: str) -> List[str]:
        """Generate Neo4j-compatible node CSV files."""
        csv_files = []

        for node_label, mapping in node_mappings.items():
            self.logger.info(f"Generating CSV for {node_label} nodes")

            # Create node DataFrame with Neo4j format
            node_data = []
            id_field_config = mapping.get("id_field", {})
            properties = mapping.get("properties", {})
            seen_ids = set()  # Track unique IDs for deduplication

            for _, row in df.iterrows():
                # Get the ID field value for deduplication
                id_hasura_col = id_field_config.get("hasura_col")
                if not id_hasura_col or id_hasura_col not in row:
                    continue  # Skip if ID field is missing

                id_value = str(row[id_hasura_col])

                # Skip if we've already processed this ID
                if id_value in seen_ids:
                    continue

                seen_ids.add(id_value)

                node_row = {}

                # Add ID field with Neo4j :ID(NodeType) format
                id_property_name = id_field_config.get("property_name", "id")
                node_row[f"{id_property_name}:ID({node_label})"] = self._clean_value(row[id_hasura_col])

                # Add other properties using config type information
                for prop_name, prop_config in properties.items():
                    if isinstance(prop_config, dict):
                        hasura_col = prop_config.get("hasura_col")
                        prop_type = prop_config.get("type", "string")
                        if hasura_col and hasura_col in row:
                            node_row[f"{prop_name}:{prop_type}"] = self._clean_value(row[hasura_col])

                node_data.append(node_row)

            # Save to CSV file
            if node_data:
                csv_filename = f"{node_label.lower()}_nodes.csv"
                csv_path = f"{output_dir}/{csv_filename}"

                node_df = pd.DataFrame(node_data)
                node_df.to_csv(csv_path, index=False, quoting=1)  # QUOTE_ALL

                csv_files.append(csv_path)
                self.logger.info(f"Generated {csv_path} with {len(node_data)} nodes")

        return csv_files

    def _generate_relationship_csvs(self, df: pd.DataFrame, rel_mappings: Dict[str, Any], output_dir: str) -> List[str]:
        """Generate Neo4j-compatible relationship CSV files."""
        csv_files = []

        for config_key, mapping in rel_mappings.items():
            actual_rel_type = mapping.get("relationship_type", config_key)
            start_node_type = mapping.get("start_node_type")
            end_node_type = mapping.get("end_node_type")
            start_field = mapping.get("start_node_field")
            end_field = mapping.get("end_node_field")
            properties = mapping.get("properties", {})

            self.logger.info(f"Generating CSV for {config_key} relationships (Neo4j type: {actual_rel_type})")

            rel_data = []
            seen_relationships = set()  # Track unique relationships to prevent duplicates

            for _, row in df.iterrows():
                # Skip if required fields are missing
                if not (start_field and end_field and
                       start_field in row and end_field in row):
                    continue

                # Get the values from Hasura CSV
                start_id = str(row[start_field])
                end_id = str(row[end_field])

                # Create relationship identifier for deduplication
                rel_key = (start_id, end_id, actual_rel_type)

                # Skip if we've already processed this relationship
                if rel_key in seen_relationships:
                    continue

                seen_relationships.add(rel_key)

                rel_row = {}

                # Add Neo4j relationship headers with node types
                rel_row[f":START_ID({start_node_type})"] = start_id
                rel_row[f":END_ID({end_node_type})"] = end_id
                rel_row[":TYPE"] = actual_rel_type

                # Map relationship properties
                for prop_name, prop_config in properties.items():
                    if isinstance(prop_config, dict):
                        hasura_col = prop_config.get("hasura_col")
                        prop_type = prop_config.get("type", "string")
                        if hasura_col and hasura_col in row:
                            rel_row[f"{prop_name}:{prop_type}"] = self._clean_value(row[hasura_col])
                    elif isinstance(prop_config, str) and prop_config in row:
                        # Legacy support for simple string mapping
                        rel_row[f"{prop_name}:string"] = self._clean_value(row[prop_config])

                rel_data.append(rel_row)

            # Save to CSV file
            if rel_data:
                csv_filename = f"{config_key.lower()}_relationships.csv"
                csv_path = f"{output_dir}/{csv_filename}"

                rel_df = pd.DataFrame(rel_data)
                rel_df.to_csv(csv_path, index=False, quoting=1)  # QUOTE_ALL

                csv_files.append(csv_path)
                self.logger.info(f"Generated {csv_path} with {len(rel_data)} relationships")

        return csv_files

    def _clean_value(self, value: Any) -> str:
        """Clean and convert values for CSV export."""
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _map_nodes(self, df: pd.DataFrame, node_mappings: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Map DataFrame to node structures."""
        mapped_nodes = {}

        for node_label, mapping in node_mappings.items():
            self.logger.info(f"Mapping nodes for label: {node_label}")

            nodes = []
            id_field = mapping.get("id_field")
            properties = mapping.get("properties", {})

            for _, row in df.iterrows():
                node = {}

                # Generate or extract node ID
                if id_field and id_field in row:
                    node["id"] = str(row[id_field])
                else:
                    node["id"] = str(uuid4())  # Generate UUID if no ID field

                # Add label
                node["label"] = node_label

                # Map properties
                for prop_name, source_field in properties.items():
                    if isinstance(source_field, dict):
                        # Handle complex field mapping
                        csv_field = source_field.get("csv_field")
                        if csv_field and csv_field in row:
                            node[prop_name] = self._transform_value(row[csv_field], source_field)
                    elif isinstance(source_field, str) and source_field in row:
                        # Simple field mapping
                        node[prop_name] = row[source_field]

                nodes.append(node)

            mapped_nodes[node_label] = nodes
            self.logger.info(f"Mapped {len(nodes)} nodes for {node_label}")

        return mapped_nodes

    def _map_relationships(self, df: pd.DataFrame, rel_mappings: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Map DataFrame to relationship structures."""
        mapped_relationships = {}

        for config_key, mapping in rel_mappings.items():
            # Support optional relationship_type field, default to config key
            actual_rel_type = mapping.get("relationship_type", config_key)
            self.logger.info(f"Mapping relationships for config: {config_key} (Neo4j type: {actual_rel_type})")

            relationships = []
            start_field = mapping.get("start_node_field")
            end_field = mapping.get("end_node_field")
            properties = mapping.get("properties", {})

            for _, row in df.iterrows():
                # Skip if required fields are missing
                if not (start_field and end_field and
                       start_field in row and end_field in row):
                    continue

                relationship = {
                    "type": actual_rel_type,
                    "start_node_id": str(row[start_field]),
                    "end_node_id": str(row[end_field])
                }

                # Map relationship properties
                for prop_name, source_field in properties.items():
                    if isinstance(source_field, dict):
                        csv_field = source_field.get("csv_field")
                        if csv_field and csv_field in row:
                            relationship[prop_name] = self._transform_value(row[csv_field], source_field)
                    elif isinstance(source_field, str) and source_field in row:
                        relationship[prop_name] = row[source_field]

                relationships.append(relationship)

            mapped_relationships[config_key] = relationships
            self.logger.info(f"Mapped {len(relationships)} relationships for {config_key}")

        return mapped_relationships

    def _transform_value(self, value: Any, field_config: Dict[str, Any]) -> Any:
        """Apply transformations to field values."""
        if pd.isna(value):
            return None

        # Handle data type conversion
        data_type = field_config.get("data_type", "string")

        try:
            if data_type == "int":
                return int(float(value))  # Handle cases where int is stored as float
            elif data_type == "float":
                return float(value)
            elif data_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            else:
                return str(value).strip()
        except (ValueError, TypeError):
            self.logger.warning(f"Failed to convert value {value} to {data_type}, using original")
            return value