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

    def map_from_csv(
        self, csv_file: str, schema_mapping: Dict[str, Any], output_dir: str = "data"
    ) -> Dict[str, Any]:
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

        csv_files = {"node_files": [], "relationship_files": []}

        # Generate node CSV files
        if "nodes" in schema_mapping:
            node_files = self._generate_node_csvs(
                df, schema_mapping["nodes"], output_dir
            )
            csv_files["node_files"] = node_files

        # Generate relationship CSV files
        if "relationships" in schema_mapping:
            rel_files = self._generate_relationship_csvs(
                df, schema_mapping["relationships"], output_dir
            )
            csv_files["relationship_files"] = rel_files

        self.logger.info("Schema mapping completed:")
        self.logger.info(f"  Node CSV files: {len(csv_files['node_files'])}")
        self.logger.info(
            f"  Relationship CSV files: {len(csv_files['relationship_files'])}"
        )

        return csv_files

    def _generate_node_csvs(
        self, df: pd.DataFrame, node_mappings: Dict[str, Any], output_dir: str
    ) -> List[str]:
        """Generate Neo4j-compatible node CSV files."""
        csv_files = []

        for node_label, mapping in node_mappings.items():
            self.logger.info(f"Generating CSV for {node_label} nodes")

            # Create node DataFrame with Neo4j format
            node_data = []
            id_field_config = mapping.get("id_field", {})
            properties = mapping.get("properties", {})
            seen_ids = set()  # Track unique IDs for deduplication

            # Handle synthetic nodes
            synthetic_value = id_field_config.get("synthetic_value", "")
            id_hasura_col = id_field_config.get("hasura_col")

            # Determine if this is a completely static synthetic node or data-driven
            is_static_synthetic = (
                synthetic_value
                and not id_hasura_col
                and not ("{" in synthetic_value and "}" in synthetic_value)
            )

            if is_static_synthetic:
                # Completely static synthetic node - create single node
                node_row = {}

                # Add ID field with Neo4j :ID(NodeType) format
                id_property_name = id_field_config.get("property_name", "id")
                node_row[f"{id_property_name}:ID({node_label})"] = synthetic_value

                # Add synthetic properties
                for prop_name, prop_config in properties.items():
                    if isinstance(prop_config, dict):
                        prop_type = prop_config.get("type", "string")
                        synthetic_prop_value = prop_config.get("synthetic_value")
                        hasura_col = prop_config.get("hasura_col")

                        if (
                            synthetic_prop_value is not None
                            and synthetic_prop_value != ""
                        ):
                            # Use synthetic value
                            node_row[f"{prop_name}:{prop_type}"] = self._clean_value(
                                synthetic_prop_value, prop_type
                            )
                        elif hasura_col == "current_timestamp":
                            # Special handling for current_timestamp
                            from datetime import datetime

                            node_row[f"{prop_name}:{prop_type}"] = (
                                datetime.now().isoformat()
                            )

                node_data.append(node_row)
            else:
                # Data-driven nodes (including templated synthetic nodes)
                # For templated synthetic nodes, use the generated column from DataCleaner
                if synthetic_value and not id_hasura_col and "{" in synthetic_value:
                    # Use the property name as the column name (same as DataCleaner)
                    property_name = id_field_config.get("property_name", "id")
                    id_hasura_col = property_name

                for _, row in df.iterrows():
                    # Get ID from Hasura column (real and synthetic)
                    if not id_hasura_col:
                        # For synthetic nodes, use generated synthetic column name
                        id_hasura_col = f"synthetic_{node_label.lower()}_id"

                    if id_hasura_col not in row:
                        continue  # Skip if ID field is missing

                    # Get ID value and handle null/NaN values
                    raw_id_value = row[id_hasura_col]
                    if pd.isna(raw_id_value):
                        continue  # Skip rows with null/NaN ID values

                    id_value = str(raw_id_value)

                    # Skip if value is empty or represents null values
                    if not id_value or id_value.strip() == "" or id_value.lower() in ["nan", "null", "none"]:
                        continue

                    # Skip if we've already processed this ID (deduplication)
                    if id_value in seen_ids:
                        continue

                    seen_ids.add(id_value)

                    node_row = {}

                    # Add ID field with Neo4j :ID(NodeType) format
                    id_property_name = id_field_config.get("property_name", "id")
                    id_type = id_field_config.get("type", "string")
                    node_row[f"{id_property_name}:ID({node_label})"] = self._clean_value(id_value, id_type)

                    # Add other properties using config type information
                    for prop_name, prop_config in properties.items():
                        if isinstance(prop_config, dict):
                            hasura_col = prop_config.get("hasura_col")
                            prop_type = prop_config.get("type", "string")
                            synthetic_prop_value = prop_config.get("synthetic_value")

                            if (
                                synthetic_prop_value is not None
                                and synthetic_prop_value != ""
                            ):
                                # Use synthetic value
                                node_row[f"{prop_name}:{prop_type}"] = (
                                    self._clean_value(synthetic_prop_value, prop_type)
                                )
                            elif hasura_col and hasura_col in row:
                                # Use Hasura column value
                                node_row[f"{prop_name}:{prop_type}"] = (
                                    self._clean_value(row[hasura_col], prop_type)
                                )
                            elif hasura_col == "current_timestamp":
                                # Special handling for current_timestamp
                                from datetime import datetime

                                node_row[f"{prop_name}:{prop_type}"] = (
                                    datetime.now().isoformat()
                                )

                    node_data.append(node_row)

            # Save to CSV file
            if node_data:
                csv_filename = f"{node_label.lower()}_nodes.csv"
                csv_path = f"{output_dir}/{csv_filename}"

                node_df = pd.DataFrame(node_data)
                node_df.to_csv(csv_path, index=False, quoting=2)  # QUOTE_NONNUMERIC

                csv_files.append(csv_path)
                self.logger.info(f"Generated {csv_path} with {len(node_data)} nodes")

        return csv_files

    def _generate_relationship_csvs(
        self, df: pd.DataFrame, rel_mappings: Dict[str, Any], output_dir: str
    ) -> List[str]:
        """Generate Neo4j-compatible relationship CSV files."""
        csv_files = []

        for config_key, mapping in rel_mappings.items():
            actual_rel_type = mapping.get("relationship_type", config_key)
            start_node_type = mapping.get("start_node_type")
            end_node_type = mapping.get("end_node_type")
            start_field = mapping.get("start_node_field")
            end_field = mapping.get("end_node_field")
            properties = mapping.get("properties", {})

            self.logger.info(
                f"Generating CSV for {config_key} relationships "
                f"(Neo4j type: {actual_rel_type})"
            )

            rel_data = []
            seen_relationships = (
                set()
            )  # Track unique relationships to prevent duplicates

            for _, row in df.iterrows():
                # Get start ID value (works for both real and synthetic columns)
                if start_field not in row:
                    continue  # Skip if start field missing
                start_id = str(row[start_field])

                # Get end ID value (works for both real and synthetic columns)
                if end_field not in row:
                    continue  # Skip if end field missing
                end_id = str(row[end_field])

                # Skip if either ID is empty
                if (
                    not start_id
                    or not end_id
                    or start_id.strip() == ""
                    or end_id.strip() == ""
                ):
                    continue

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
                            rel_row[f"{prop_name}:{prop_type}"] = self._clean_value(
                                row[hasura_col], prop_type
                            )
                    elif isinstance(prop_config, str) and prop_config in row:
                        # Legacy support for simple string mapping
                        rel_row[f"{prop_name}:string"] = self._clean_value(
                            row[prop_config], "string"
                        )

                rel_data.append(rel_row)

            # Save to CSV file
            if rel_data:
                csv_filename = f"{config_key.lower()}_relationships.csv"
                csv_path = f"{output_dir}/{csv_filename}"

                rel_df = pd.DataFrame(rel_data)
                rel_df.to_csv(csv_path, index=False, quoting=2)  # QUOTE_NONNUMERIC

                csv_files.append(csv_path)
                self.logger.info(
                    f"Generated {csv_path} with {len(rel_data)} relationships"
                )

        return csv_files

    def _clean_value(self, value: Any, data_type: str = "string") -> Any:
        """Clean and convert values for CSV export with proper type preservation."""
        if pd.isna(value):
            if data_type == "string":
                return ""
            elif data_type == "int":
                return 0
            elif data_type == "float":
                return 0.0
            elif data_type == "boolean":
                return False
            else:
                return ""

        try:
            if data_type == "int":
                # Handle cases where int is stored as float (e.g., 123.0 -> 123)
                return int(float(value))
            elif data_type == "float":
                return float(value)
            elif data_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            elif data_type == "datetime":
                return str(value).strip()
            else:  # string
                return str(value).strip()
        except (ValueError, TypeError):
            self.logger.warning(
                f"Failed to convert value {value} to {data_type}, using string conversion"
            )
            return str(value).strip()

    def _map_nodes(
        self, df: pd.DataFrame, node_mappings: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
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
                            node[prop_name] = self._transform_value(
                                row[csv_field], source_field
                            )
                    elif isinstance(source_field, str) and source_field in row:
                        # Simple field mapping
                        node[prop_name] = row[source_field]

                nodes.append(node)

            mapped_nodes[node_label] = nodes
            self.logger.info(f"Mapped {len(nodes)} nodes for {node_label}")

        return mapped_nodes

    def _map_relationships(
        self, df: pd.DataFrame, rel_mappings: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Map DataFrame to relationship structures."""
        mapped_relationships = {}

        for config_key, mapping in rel_mappings.items():
            # Support optional relationship_type field, default to config key
            actual_rel_type = mapping.get("relationship_type", config_key)
            self.logger.info(
                f"Mapping relationships for config: {config_key} "
                f"(Neo4j type: {actual_rel_type})"
            )

            relationships = []
            start_field = mapping.get("start_node_field")
            end_field = mapping.get("end_node_field")
            properties = mapping.get("properties", {})

            for _, row in df.iterrows():
                # Skip if required fields are missing
                if not (
                    start_field
                    and end_field
                    and start_field in row
                    and end_field in row
                ):
                    continue

                relationship = {
                    "type": actual_rel_type,
                    "start_node_id": str(row[start_field]),
                    "end_node_id": str(row[end_field]),
                }

                # Map relationship properties
                for prop_name, source_field in properties.items():
                    if isinstance(source_field, dict):
                        csv_field = source_field.get("csv_field")
                        if csv_field and csv_field in row:
                            relationship[prop_name] = self._transform_value(
                                row[csv_field], source_field
                            )
                    elif isinstance(source_field, str) and source_field in row:
                        relationship[prop_name] = row[source_field]

                relationships.append(relationship)

            mapped_relationships[config_key] = relationships
            self.logger.info(
                f"Mapped {len(relationships)} relationships for {config_key}"
            )

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
            self.logger.warning(
                f"Failed to convert value {value} to {data_type}, using original"
            )
            return value
