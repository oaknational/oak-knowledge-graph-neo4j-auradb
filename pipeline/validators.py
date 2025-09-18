from typing import Any, Dict, List, Type
from pydantic import BaseModel, ValidationError
from models.hasura import HasuraResponse, MaterializedViewRecord
from models.neo4j import Neo4jNode, Neo4jRelationship
from models.config import NodeMapping, RelationshipMapping


class ValidationResult:
    """Container for validation results with detailed error reporting."""

    def __init__(self):
        self.valid_records: List[Dict[str, Any]] = []
        self.invalid_records: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.validation_summary: Dict[str, int] = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "error_count": 0,
        }

    def add_valid_record(self, record: Dict[str, Any]) -> None:
        """Add a valid record to results."""
        self.valid_records.append(record)
        self.validation_summary["valid_records"] += 1

    def add_invalid_record(self, record: Dict[str, Any], error: str) -> None:
        """Add an invalid record with its error to results."""
        self.invalid_records.append(record)
        self.errors.append(error)
        self.validation_summary["invalid_records"] += 1
        self.validation_summary["error_count"] += 1

    def finalize(self) -> None:
        """Finalize validation summary statistics."""
        self.validation_summary["total_records"] = (
            self.validation_summary["valid_records"]
            + self.validation_summary["invalid_records"]
        )

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no invalid records)."""
        return self.validation_summary["invalid_records"] == 0

    def get_error_report(self) -> str:
        """Generate detailed error report for debugging."""
        if self.is_valid:
            valid_count = self.validation_summary["valid_records"]
            return f"Validation successful: {valid_count} records validated"

        invalid_count = self.validation_summary["invalid_records"]
        total_count = self.validation_summary["total_records"]
        valid_count = self.validation_summary["valid_records"]

        report_lines = [
            f"Validation failed: {invalid_count} invalid records found",
            f"Total records processed: {total_count}",
            f"Valid records: {valid_count}",
            "",
            "Validation errors:",
        ]

        for i, error in enumerate(self.errors, 1):
            report_lines.append(f"{i}. {error}")

        return "\n".join(report_lines)


class DataValidator:
    """Pydantic-based data validator for pipeline data quality assurance."""

    def __init__(self):
        """Initialize validator with default settings."""
        self.batch_size = 100  # Process records in batches for performance

    def validate_hasura_response(
        self, response_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate Hasura GraphQL API response structure.

        Args:
            response_data: Raw response from Hasura API

        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult()

        try:
            # Validate overall response structure
            hasura_response = HasuraResponse.model_validate(response_data)

            # Check for GraphQL errors
            if hasura_response.errors:
                for error in hasura_response.errors:
                    result.add_invalid_record(
                        response_data, f"GraphQL error: {error.message}"
                    )

            # Validate data payload if present
            if hasura_response.data:
                result.add_valid_record(hasura_response.data)
            else:
                result.add_invalid_record(
                    response_data, "Missing data payload in Hasura response"
                )

        except ValidationError as e:
            result.add_invalid_record(
                response_data,
                f"Invalid Hasura response structure: "
                f"{self._format_validation_error(e)}",
            )

        result.finalize()
        return result

    def validate_materialized_view_data(
        self, records: List[Dict[str, Any]], view_name: str
    ) -> ValidationResult:
        """
        Validate materialized view records in batches.

        Args:
            records: List of records from materialized view
            view_name: Name of materialized view for error context

        Returns:
            ValidationResult with batch validation results
        """
        result = ValidationResult()

        # Process records in batches for performance
        for batch_start in range(0, len(records), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(records))
            batch = records[batch_start:batch_end]

            for i, record in enumerate(batch):
                record_index = batch_start + i

                try:
                    # Validate individual record structure
                    validated_record = MaterializedViewRecord.model_validate(
                        {"data": record}
                    )
                    result.add_valid_record(validated_record.data)

                except ValidationError as e:
                    result.add_invalid_record(
                        record,
                        f"Record {record_index} in view '{view_name}': "
                        f"{self._format_validation_error(e)}",
                    )

        result.finalize()
        return result

    def validate_node_data(
        self, records: List[Dict[str, Any]], node_mapping: NodeMapping
    ) -> ValidationResult:
        """
        Validate data against node mapping requirements.

        Args:
            records: List of records to validate for node creation
            node_mapping: Node mapping configuration with required fields

        Returns:
            ValidationResult with node validation results
        """
        result = ValidationResult()
        id_field = node_mapping.id_field
        properties_keys = node_mapping.properties.keys()
        required_fields = {id_field} | set(properties_keys)

        for i, record in enumerate(records):
            try:
                # Check for required ID field
                if node_mapping.id_field not in record:
                    result.add_invalid_record(
                        record,
                        f"Node record {i} missing required ID field "
                        f"'{node_mapping.id_field}' for label "
                        f"'{node_mapping.label}'",
                    )
                    continue

                # Check for required property fields
                missing_fields = required_fields - set(record.keys())
                if missing_fields:
                    result.add_invalid_record(
                        record,
                        f"Node record {i} missing required fields "
                        f"{missing_fields} for label '{node_mapping.label}'",
                    )
                    continue

                # Validate against Neo4j node model
                node_data = {
                    "id": str(record[node_mapping.id_field]),
                    "label": node_mapping.label,
                    "properties": {
                        field: record.get(field)
                        for field in node_mapping.properties.keys()
                        if field in record
                    },
                }

                Neo4jNode.model_validate(node_data)
                result.add_valid_record(record)

            except ValidationError as e:
                result.add_invalid_record(
                    record,
                    f"Node record {i} validation failed for label "
                    f"'{node_mapping.label}': "
                    f"{self._format_validation_error(e)}",
                )

        result.finalize()
        return result

    def validate_relationship_data(
        self,
        records: List[Dict[str, Any]],
        relationship_mapping: RelationshipMapping,
    ) -> ValidationResult:
        """
        Validate data against relationship mapping requirements.

        Args:
            records: List of records to validate for relationship creation
            relationship_mapping: Relationship mapping configuration

        Returns:
            ValidationResult with relationship validation results
        """
        result = ValidationResult()
        start_field = relationship_mapping.start_node_id_field
        end_field = relationship_mapping.end_node_id_field
        properties_keys = relationship_mapping.properties.keys()
        required_fields = {start_field, end_field} | set(properties_keys)

        for i, record in enumerate(records):
            try:
                # Check for required start/end node ID fields
                if relationship_mapping.start_node_id_field not in record:
                    result.add_invalid_record(
                        record,
                        f"Relationship record {i} missing start node ID "
                        f"field '{relationship_mapping.start_node_id_field}' "
                        f"for type '{relationship_mapping.type}'",
                    )
                    continue

                if relationship_mapping.end_node_id_field not in record:
                    result.add_invalid_record(
                        record,
                        f"Relationship record {i} missing end node ID "
                        f"field '{relationship_mapping.end_node_id_field}' "
                        f"for type '{relationship_mapping.type}'",
                    )
                    continue

                # Check for required property fields
                missing_fields = required_fields - set(record.keys())
                if missing_fields:
                    result.add_invalid_record(
                        record,
                        f"Relationship record {i} missing required fields "
                        f"{missing_fields} for type "
                        f"'{relationship_mapping.type}'",
                    )
                    continue

                # Validate against Neo4j relationship model
                start_id_field = relationship_mapping.start_node_id_field
                end_id_field = relationship_mapping.end_node_id_field
                relationship_data = {
                    "start_id": str(record[start_id_field]),
                    "end_id": str(record[end_id_field]),
                    "type": relationship_mapping.type,
                    "properties": {
                        field: record.get(field)
                        for field in relationship_mapping.properties.keys()
                        if field in record
                    },
                }

                Neo4jRelationship.model_validate(relationship_data)
                result.add_valid_record(record)

            except ValidationError as e:
                result.add_invalid_record(
                    record,
                    f"Relationship record {i} validation failed for type "
                    f"'{relationship_mapping.type}': "
                    f"{self._format_validation_error(e)}",
                )

        result.finalize()
        return result

    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        model_class: Type[BaseModel],
        context: str = "",
    ) -> ValidationResult:
        """
        Generic batch validation for any Pydantic model.

        Args:
            records: List of records to validate
            model_class: Pydantic model class to validate against
            context: Context string for error messages

        Returns:
            ValidationResult with batch validation results
        """
        result = ValidationResult()
        context_prefix = f"{context}: " if context else ""

        for i, record in enumerate(records):
            try:
                model_class.model_validate(record)
                result.add_valid_record(record)
            except ValidationError as e:
                result.add_invalid_record(
                    record,
                    f"{context_prefix}Record {i} validation failed: "
                    f"{self._format_validation_error(e)}",
                )

        result.finalize()
        return result

    def _format_validation_error(self, error: ValidationError) -> str:
        """
        Format Pydantic validation error for actionable error messages.

        Args:
            error: Pydantic ValidationError

        Returns:
            Formatted error string with field paths and descriptions
        """
        error_details = []

        for err in error.errors():
            if err["loc"]:
                field_path = " → ".join(str(loc) for loc in err["loc"])
            else:
                field_path = "root"
            error_message = err["msg"]
            error_type = err["type"]

            error_details.append(
                f"Field '{field_path}': {error_message} (type: {error_type})"
            )

        return "; ".join(error_details)

    def set_batch_size(self, batch_size: int) -> None:
        """
        Configure batch size for validation performance tuning.

        Args:
            batch_size: Number of records to process in each batch
        """
        if batch_size <= 0:
            raise ValueError("Batch size must be positive")
        self.batch_size = batch_size
