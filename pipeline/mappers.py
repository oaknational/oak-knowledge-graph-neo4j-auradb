from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
import pandas as pd

from models.config import NodeMapping, RelationshipMapping, FieldMapping


class DataLineage:
    def __init__(self):
        self.transformations: List[Dict[str, Any]] = []
        self.id_mappings: Dict[str, str] = {}

    def record_field_transformation(
        self,
        source_field: str,
        target_field: str,
        transformation: Optional[str] = None,
    ):
        self.transformations.append(
            {
                "type": "field_mapping",
                "source_field": source_field,
                "target_field": target_field,
                "transformation": transformation,
            }
        )

    def record_id_generation(
        self, original_id: str, generated_id: str, node_label: str
    ):
        self.id_mappings[f"{node_label}:{original_id}"] = generated_id
        self.transformations.append(
            {
                "type": "id_generation",
                "original_id": original_id,
                "generated_id": generated_id,
                "node_label": node_label,
            }
        )


class SchemaMapper:
    def __init__(self):
        self.lineage = DataLineage()
        self._generated_ids: Dict[str, str] = {}
        self._deduplication_cache: Dict[str, str] = {}  # For synthetic nodes

    def map_node_data(
        self, data: List[Dict[str, Any]], mapping: NodeMapping
    ) -> Tuple[pd.DataFrame, DataLineage]:
        if not data:
            return pd.DataFrame(), self.lineage

        mapped_records = []

        for record in data:
            mapped_record = self._apply_node_mapping(record, mapping)
            if mapped_record:
                mapped_records.append(mapped_record)

        df = pd.DataFrame(mapped_records)
        return df, self.lineage

    def map_relationship_data(
        self, data: List[Dict[str, Any]], mapping: RelationshipMapping
    ) -> Tuple[pd.DataFrame, DataLineage]:
        if not data:
            return pd.DataFrame(), self.lineage

        mapped_records = []

        for record in data:
            mapped_record = self._apply_relationship_mapping(record, mapping)
            if mapped_record:
                mapped_records.append(mapped_record)

        df = pd.DataFrame(mapped_records)
        return df, self.lineage

    def _apply_node_mapping(
        self, record: Dict[str, Any], mapping: NodeMapping
    ) -> Optional[Dict[str, Any]]:
        try:
            mapped_record = {}

            # Handle deduplication for synthetic nodes
            if mapping.deduplication_key:
                dedup_key = self._build_deduplication_key(
                    record, mapping.deduplication_key
                )
                cache_key = f"{mapping.label}:{dedup_key}"

                if cache_key in self._deduplication_cache:
                    # Skip - already processed this synthetic node
                    return None
                else:
                    self._deduplication_cache[cache_key] = dedup_key

            # Generate or get unique ID for this node
            node_id = self._generate_node_id(record, mapping)
            if node_id is None:
                return None

            node_key = f"{mapping.label}:{node_id}"
            if node_key not in self._generated_ids:
                if (
                    mapping.id_generation == "uuid"
                    or mapping.id_field == "_generated_uuid"
                ):
                    generated_id = str(uuid4())
                else:
                    generated_id = str(node_id)

                self._generated_ids[node_key] = generated_id
                self.lineage.record_id_generation(
                    str(node_id), generated_id, mapping.label
                )

            mapped_record[":ID"] = self._generated_ids[node_key]
            mapped_record[":LABEL"] = mapping.label

            # Apply property mappings
            for target_field, field_mapping in mapping.properties.items():
                transformed_value = self._get_field_value(
                    record, field_mapping, mapping
                )
                mapped_record[target_field] = transformed_value

                self.lineage.record_field_transformation(
                    field_mapping.source_field,
                    target_field,
                    field_mapping.transformation,
                )

            return mapped_record

        except Exception as e:
            raise ValueError(f"Failed to map node record for {mapping.label}: {e}")

    def _apply_relationship_mapping(
        self, record: Dict[str, Any], mapping: RelationshipMapping
    ) -> Optional[Dict[str, Any]]:
        try:
            mapped_record = {}

            # Get start and end node IDs
            start_id = record.get(mapping.start_node_id_field)
            end_id = record.get(mapping.end_node_id_field)

            if start_id is None or end_id is None:
                return None

            # Find generated IDs for start and end nodes
            start_generated_id = self._find_generated_id(str(start_id))
            end_generated_id = self._find_generated_id(str(end_id))

            if not start_generated_id or not end_generated_id:
                return None

            mapped_record[":START_ID"] = start_generated_id
            mapped_record[":END_ID"] = end_generated_id
            mapped_record[":TYPE"] = mapping.type

            # Apply property mappings
            for target_field, field_mapping in mapping.properties.items():
                source_value = record.get(field_mapping.source_field)
                transformed_value = self._transform_field_value(
                    source_value, field_mapping
                )
                mapped_record[target_field] = transformed_value

                self.lineage.record_field_transformation(
                    field_mapping.source_field,
                    target_field,
                    field_mapping.transformation,
                )

            return mapped_record

        except Exception as e:
            raise ValueError(
                f"Failed to map relationship record for {mapping.type}: {e}"
            )

    def _find_generated_id(self, original_id: str) -> Optional[str]:
        for key, generated_id in self._generated_ids.items():
            if key.endswith(f":{original_id}"):
                return generated_id
        return None

    def _transform_field_value(self, value: Any, field_mapping: FieldMapping) -> Any:
        if value is None:
            return None

        # Apply transformation if specified
        if field_mapping.transformation:
            value = self._apply_transformation(value, field_mapping.transformation)

        # Apply type conversion
        return self._convert_type(value, field_mapping.target_type)

    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        if transformation == "uppercase":
            return str(value).upper()
        elif transformation == "lowercase":
            return str(value).lower()
        elif transformation == "strip":
            return str(value).strip()
        elif transformation.startswith("prefix:"):
            prefix = transformation.replace("prefix:", "")
            return f"{prefix}{value}"
        elif transformation.startswith("suffix:"):
            suffix = transformation.replace("suffix:", "")
            return f"{value}{suffix}"
        else:
            return value

    def _convert_type(self, value: Any, target_type: str) -> Any:
        if value is None:
            return None

        try:
            if target_type == "string":
                return str(value)
            elif target_type == "int":
                return int(float(value)) if value != "" else None
            elif target_type == "float":
                return float(value) if value != "" else None
            elif target_type == "boolean":
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes", "on")
            else:
                return value
        except (ValueError, TypeError):
            return None

    def get_node_id_mapping(self, node_label: str, original_id: str) -> Optional[str]:
        node_key = f"{node_label}:{original_id}"
        return self._generated_ids.get(node_key)

    def clear_lineage(self):
        self.lineage = DataLineage()
        self._generated_ids.clear()
        self._deduplication_cache.clear()

    def _build_deduplication_key(self, record: Dict[str, Any], dedup_key: str) -> str:
        """Build deduplication key from comma-separated field names"""
        fields = [field.strip() for field in dedup_key.split(",")]
        values = []
        for field in fields:
            value = record.get(field, "")
            values.append(str(value))
        return "|".join(values)

    def _generate_node_id(
        self, record: Dict[str, Any], mapping: NodeMapping
    ) -> Optional[str]:
        """Generate node ID based on the mapping configuration"""
        if mapping.id_field == "_generated_uuid":
            # Use deduplication key for synthetic nodes
            if mapping.deduplication_key:
                return self._build_deduplication_key(record, mapping.deduplication_key)
            else:
                return str(uuid4())

        elif mapping.id_generation == "computed" and mapping.id_computation:
            return self._compute_value(record, mapping.id_computation)

        else:
            # Use source field
            return record.get(mapping.id_field)

    def _get_field_value(
        self,
        record: Dict[str, Any],
        field_mapping: FieldMapping,
        node_mapping: NodeMapping,
    ) -> Any:
        """Get field value with support for computed fields and special values"""
        if field_mapping.source_field == "_generated_uuid":
            # Return the UUID for this node
            node_id = self._generate_node_id(record, node_mapping)
            node_key = f"{node_mapping.label}:{node_id}"
            return self._generated_ids.get(node_key)

        elif (
            field_mapping.source_field.startswith("_computed_")
            and field_mapping.computation
        ):
            # Computed field
            return self._compute_value(record, field_mapping.computation)

        else:
            # Regular field
            source_value = record.get(field_mapping.source_field)
            return self._transform_field_value(source_value, field_mapping)

    def _compute_value(self, record: Dict[str, Any], computation: str) -> str:
        """Compute values using computation expressions like 'concat:field1,-,field2'"""
        if computation.startswith("concat:"):
            # Parse concat expression: concat:field1,separator,field2
            parts = computation[7:].split(",")
            result_parts = []

            for part in parts:
                part = part.strip()
                if part in record:
                    # It's a field name
                    result_parts.append(str(record[part]))
                else:
                    # It's a literal separator or text
                    result_parts.append(part)

            return "".join(result_parts)

        else:
            # Future: Add more computation types here
            return computation
