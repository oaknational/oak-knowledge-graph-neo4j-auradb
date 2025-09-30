import pandas as pd
import logging
import json
import ast
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
            df = pd.read_csv(csv_file, low_memory=False)
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
                df, schema_mapping["relationships"], schema_mapping.get("nodes", {}), output_dir
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

            # Check if this is an array expansion node
            expand_list = id_field_config.get("expand_list", False)
            if expand_list:
                # Handle array expansion
                node_data = self._expand_array_to_nodes(
                    df, node_label, id_field_config, properties, seen_ids
                )
            else:
                # Handle normal nodes (existing logic)
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
                        if (
                            not id_value
                            or id_value.strip() == ""
                            or id_value.lower() in ["nan", "null", "none"]
                        ):
                            continue

                        # Skip if we've already processed this ID (deduplication)
                        if id_value in seen_ids:
                            continue

                        seen_ids.add(id_value)

                        node_row = {}

                        # Add ID field with Neo4j :ID(NodeType) format
                        id_property_name = id_field_config.get("property_name", "id")
                        id_type = id_field_config.get("type", "string")
                        node_row[f"{id_property_name}:ID({node_label})"] = (
                            self._clean_value(id_value, id_type)
                        )

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
                                    cleaned_synthetic = self._clean_value(synthetic_prop_value, prop_type)
                                    if cleaned_synthetic is not None:
                                        node_row[f"{prop_name}:{prop_type}"] = cleaned_synthetic
                                elif hasura_col and hasura_col in row:
                                    # Use Hasura column value
                                    cleaned_value = self._clean_value(
                                        row[hasura_col], prop_type
                                    )
                                    # Skip properties with None values (empty values)
                                    if cleaned_value is not None:
                                        # Convert lists to JSON string for CSV storage
                                        if prop_type == "list" and isinstance(
                                            cleaned_value, list
                                        ):
                                            node_row[f"{prop_name}:{prop_type}"] = json.dumps(
                                                cleaned_value
                                            )
                                        else:
                                            node_row[f"{prop_name}:{prop_type}"] = cleaned_value
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
        self, df: pd.DataFrame, rel_mappings: Dict[str, Any], node_mappings: Dict[str, Any], output_dir: str
    ) -> List[str]:
        """Generate Neo4j-compatible relationship CSV files with array expansion support."""
        csv_files = []

        # Build a lookup of which fields are expandable arrays
        expandable_fields = {}
        for node_label, node_config in node_mappings.items():
            id_field_config = node_config.get("id_field", {})
            if id_field_config.get("expand_list"):
                hasura_col = id_field_config.get("hasura_col")
                property_name = id_field_config.get("property_name", "id")
                expandable_fields[hasura_col] = {
                    "node_type": node_label,
                    "property_name": property_name,
                    "id_key": id_field_config.get("id_key", property_name)
                }

        for config_key, mapping in rel_mappings.items():
            actual_rel_type = mapping.get("relationship_type", config_key)
            start_node_type = mapping.get("start_node_type")
            end_node_type = mapping.get("end_node_type")
            start_field = mapping.get("start_csv_field")
            end_field = mapping.get("end_csv_field")
            properties = mapping.get("properties", {})

            self.logger.info(
                f"Generating CSV for {config_key} relationships "
                f"(Neo4j type: {actual_rel_type})"
            )

            # Check if either start or end field is an expandable array
            start_is_array = start_field in expandable_fields
            end_is_array = end_field in expandable_fields

            if start_is_array or end_is_array:
                # Use array expansion for relationships
                rel_data = self._expand_array_relationships(
                    df, start_field, end_field, start_node_type, end_node_type,
                    actual_rel_type, properties, expandable_fields,
                    start_is_array, end_is_array
                )
            else:
                # Use normal relationship generation
                rel_data = []
                seen_relationships = set()

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

    def _expand_array_relationships(
        self,
        df: pd.DataFrame,
        start_field: str,
        end_field: str,
        start_node_type: str,
        end_node_type: str,
        rel_type: str,
        properties: Dict[str, Any],
        expandable_fields: Dict[str, Any],
        start_is_array: bool,
        end_is_array: bool,
    ) -> List[Dict[str, Any]]:
        """
        Generate relationships with array expansion support.

        Handles cases where start or end node comes from an expanded array.
        """
        rel_data = []
        seen_relationships = set()

        for _, row in df.iterrows():
            # Determine start IDs (single or multiple from array)
            if start_is_array:
                start_ids = self._extract_ids_from_array(
                    row, start_field, expandable_fields[start_field]
                )
            else:
                if start_field not in row:
                    continue
                start_id_value = str(row[start_field])
                if start_id_value and start_id_value.strip():
                    start_ids = [start_id_value]
                else:
                    start_ids = []

            # Determine end IDs (single or multiple from array)
            if end_is_array:
                end_ids = self._extract_ids_from_array(
                    row, end_field, expandable_fields[end_field]
                )
            else:
                if end_field not in row:
                    continue
                end_id_value = str(row[end_field])
                if end_id_value and end_id_value.strip():
                    end_ids = [end_id_value]
                else:
                    end_ids = []

            # Create relationships for all combinations
            for start_id in start_ids:
                for end_id in end_ids:
                    # Skip empty IDs
                    if not start_id or not end_id:
                        continue

                    # Deduplicate
                    rel_key = (start_id, end_id, rel_type)
                    if rel_key in seen_relationships:
                        continue
                    seen_relationships.add(rel_key)

                    # Create relationship row
                    rel_row = {
                        f":START_ID({start_node_type})": start_id,
                        f":END_ID({end_node_type})": end_id,
                        ":TYPE": rel_type,
                    }

                    # Add properties
                    for prop_name, prop_config in properties.items():
                        if isinstance(prop_config, dict):
                            hasura_col = prop_config.get("hasura_col")
                            prop_type = prop_config.get("type", "string")
                            if hasura_col and hasura_col in row:
                                cleaned = self._clean_value(row[hasura_col], prop_type)
                                if cleaned is not None:
                                    rel_row[f"{prop_name}:{prop_type}"] = cleaned
                            elif hasura_col == "current_timestamp":
                                from datetime import datetime
                                rel_row[f"{prop_name}:{prop_type}"] = (
                                    datetime.now().isoformat()
                                )

                    rel_data.append(rel_row)

        self.logger.info(f"Expanded {len(rel_data)} relationships with array support")
        return rel_data

    def _extract_ids_from_array(
        self, row: pd.Series, field_name: str, field_config: Dict[str, Any]
    ) -> List[str]:
        """
        Extract ID values from an array field in a row.

        Args:
            row: DataFrame row
            field_name: Name of the field containing the array
            field_config: Configuration for the expandable field

        Returns:
            List of ID values extracted from the array
        """
        if field_name not in row:
            return []

        array_value = row[field_name]
        if pd.isna(array_value):
            return []

        id_key = field_config["id_key"]
        ids = []

        try:
            # Parse the array
            if isinstance(array_value, str):
                try:
                    parsed_array = json.loads(array_value)
                except json.JSONDecodeError:
                    parsed_array = ast.literal_eval(array_value)
            elif isinstance(array_value, list):
                parsed_array = array_value
            else:
                return []

            if not isinstance(parsed_array, list):
                return []

            # Extract IDs from each item
            for item in parsed_array:
                if isinstance(item, dict) and id_key in item:
                    id_value = str(item[id_key])
                    if id_value and id_value.strip():
                        ids.append(id_value)

        except (json.JSONDecodeError, ValueError, SyntaxError) as e:
            self.logger.warning(f"Failed to parse array in {field_name}: {e}")
            return []

        return ids

    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is effectively empty and should be treated as null."""
        if isinstance(value, str):
            # Check for empty string, empty list string, or empty object string
            stripped = value.strip()
            if stripped == "" or stripped == "[]" or stripped == "{}":
                return True
            # Try to parse as JSON to check for empty structures
            try:
                import json
                parsed = json.loads(stripped)
                if isinstance(parsed, (list, dict)) and not parsed:
                    return True
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(value, (list, dict)) and not value:
            # Direct empty list or dict
            return True
        return False

    def _decode_unicode(self, text: str) -> str:
        """Decode Unicode escape sequences to proper characters."""
        try:
            import re
            # Find and replace Unicode escape sequences
            def replace_unicode(match):
                hex_code = match.group(1)
                return chr(int(hex_code, 16))

            # Handle different levels of escaping - try most common patterns
            # Pattern for \uXXXX (single backslash)
            text = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
            # Pattern for \\uXXXX (double backslash)
            text = re.sub(r'\\\\u([0-9a-fA-F]{4})', replace_unicode, text)

            return text
        except (ValueError, OverflowError):
            # If decoding fails, return original string
            return text

    def _expand_array_to_nodes(
        self,
        df: pd.DataFrame,
        node_label: str,
        id_field_config: Dict[str, Any],
        properties: Dict[str, Any],
        seen_ids: set,
    ) -> List[Dict[str, Any]]:
        """
        Expand array column into separate nodes.

        Args:
            df: DataFrame with source data
            node_label: Label for the nodes being created
            id_field_config: ID field configuration with expand_list: true
            properties: Property mappings for the node
            seen_ids: Set to track unique IDs for deduplication

        Returns:
            List of node dictionaries ready for CSV export
        """
        node_data = []
        hasura_col = id_field_config.get("hasura_col")
        id_property_name = id_field_config.get("property_name", "id")
        # Use property_name as the key to look up in each object (since that's what the ID is called)
        id_key = id_field_config.get("id_key", id_property_name)
        id_type = id_field_config.get("type", "string")

        self.logger.info(
            f"Expanding array column '{hasura_col}' to create {node_label} nodes"
        )

        if not hasura_col:
            self.logger.warning(f"No hasura_col specified for {node_label}, skipping")
            return node_data

        for _, row in df.iterrows():
            if hasura_col not in row:
                continue

            array_value = row[hasura_col]

            # Skip if null/NaN
            if pd.isna(array_value):
                continue

            # Parse the array
            try:
                if isinstance(array_value, str):
                    # Try JSON parsing
                    try:
                        parsed_array = json.loads(array_value)
                    except json.JSONDecodeError:
                        # Try ast.literal_eval for single-quote format
                        parsed_array = ast.literal_eval(array_value)
                elif isinstance(array_value, list):
                    parsed_array = array_value
                else:
                    continue

                # Ensure it's a list
                if not isinstance(parsed_array, list):
                    continue

                # Process each item in the array
                for item in parsed_array:
                    if not isinstance(item, dict):
                        self.logger.warning(
                            f"Array item is not a dict in {hasura_col}, skipping: {item}"
                        )
                        continue

                    # Extract ID from the item
                    if id_key not in item:
                        self.logger.warning(
                            f"ID key '{id_key}' not found in item: {item}"
                        )
                        continue

                    id_value = str(item[id_key])

                    # Skip empty IDs
                    if not id_value or id_value.strip() == "":
                        continue

                    # Skip duplicates
                    if id_value in seen_ids:
                        continue

                    seen_ids.add(id_value)

                    # Create node row
                    node_row = {}

                    # Add ID field with Neo4j :ID(NodeType) format
                    node_row[f"{id_property_name}:ID({node_label})"] = (
                        self._clean_value(id_value, id_type)
                    )

                    # Add other properties from the item
                    for prop_name, prop_config in properties.items():
                        if isinstance(prop_config, dict):
                            hasura_col_prop = prop_config.get("hasura_col")
                            prop_type = prop_config.get("type", "string")
                            synthetic_prop_value = prop_config.get("synthetic_value")

                            if (
                                synthetic_prop_value is not None
                                and synthetic_prop_value != ""
                            ):
                                # Use synthetic value
                                cleaned_synthetic = self._clean_value(
                                    synthetic_prop_value, prop_type
                                )
                                if cleaned_synthetic is not None:
                                    node_row[f"{prop_name}:{prop_type}"] = (
                                        cleaned_synthetic
                                    )
                            elif hasura_col_prop == "current_timestamp":
                                # Special handling for current_timestamp
                                from datetime import datetime

                                node_row[f"{prop_name}:{prop_type}"] = (
                                    datetime.now().isoformat()
                                )
                            elif hasura_col_prop and hasura_col_prop in item:
                                # Extract property from the expanded item
                                cleaned_value = self._clean_value(
                                    item[hasura_col_prop], prop_type
                                )
                                if cleaned_value is not None:
                                    if prop_type == "list" and isinstance(
                                        cleaned_value, list
                                    ):
                                        node_row[f"{prop_name}:{prop_type}"] = (
                                            json.dumps(cleaned_value)
                                        )
                                    else:
                                        node_row[f"{prop_name}:{prop_type}"] = (
                                            cleaned_value
                                        )

                    node_data.append(node_row)

            except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                self.logger.warning(
                    f"Failed to parse array in row: {e}, value: {array_value}"
                )
                continue

        self.logger.info(
            f"Expanded {len(node_data)} {node_label} nodes from array column"
        )
        return node_data

    def _clean_value(self, value: Any, data_type: str = "string") -> Any:
        """Clean and convert values for CSV export with proper type preservation."""
        # Check for empty values that should be treated as null
        if pd.isna(value) or self._is_empty_value(value):
            # Return None for empty values so they get skipped during CSV generation
            return None

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
            elif data_type == "list":
                # Parse JSON array into Python list for Neo4j
                if isinstance(value, str) and value.strip():
                    try:
                        parsed_array = json.loads(value)
                        if isinstance(parsed_array, list):
                            result = []
                            for item in parsed_array:
                                if isinstance(item, dict):
                                    # Always preserve dictionary objects as JSON strings
                                    json_str = json.dumps(item)
                                    # Decode Unicode escapes in the JSON string
                                    result.append(self._decode_unicode(json_str))
                                else:
                                    # If array contains primitives, use directly
                                    result.append(str(item).strip())
                            return [r for r in result if r]  # Filter out empty strings
                        else:
                            return [str(parsed_array)]
                    except json.JSONDecodeError:
                        try:
                            # Try ast.literal_eval for single-quote format
                            parsed_array = ast.literal_eval(value)
                            if isinstance(parsed_array, list):
                                result = []
                                for item in parsed_array:
                                    if isinstance(item, dict):
                                        # Always preserve dictionary objects as JSON strings
                                        json_str = json.dumps(item)
                                        # Decode Unicode escapes in the JSON string
                                        result.append(self._decode_unicode(json_str))
                                    else:
                                        result.append(str(item).strip())
                                return [r for r in result if r]
                            else:
                                return [str(parsed_array)]
                        except (ValueError, SyntaxError):
                            # Fallback: return as single-item list
                            return [str(value).strip()]
                elif isinstance(value, list):
                    # Already a list
                    return value
                else:
                    return [str(value).strip()]
            else:  # string
                # Handle case where we have dict/list data but want string type (like JSON)
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return self._decode_unicode(str(value).strip())
        except (ValueError, TypeError):
            self.logger.warning(
                f"Failed to convert value {value} to {data_type}, using string conversion"
            )
            return self._decode_unicode(str(value).strip())

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
            start_field = mapping.get("start_csv_field")
            end_field = mapping.get("end_csv_field")
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
