import pytest
import pandas as pd
from uuid import UUID

from pipeline.mappers import SchemaMapper, DataLineage
from models.config import NodeMapping, RelationshipMapping, FieldMapping


class TestDataLineage:
    def test_record_field_transformation(self):
        lineage = DataLineage()
        lineage.record_field_transformation("source", "target", "uppercase")

        assert len(lineage.transformations) == 1
        transformation = lineage.transformations[0]
        assert transformation["type"] == "field_mapping"
        assert transformation["source_field"] == "source"
        assert transformation["target_field"] == "target"
        assert transformation["transformation"] == "uppercase"

    def test_record_id_generation(self):
        lineage = DataLineage()
        lineage.record_id_generation("123", "uuid-456", "Unit")

        assert "Unit:123" in lineage.id_mappings
        assert lineage.id_mappings["Unit:123"] == "uuid-456"
        assert len(lineage.transformations) == 1
        transformation = lineage.transformations[0]
        assert transformation["type"] == "id_generation"


class TestSchemaMapper:
    @pytest.fixture
    def sample_node_mapping(self):
        return NodeMapping(
            label="Unit",
            id_field="unit_id",
            properties={
                "id": FieldMapping(source_field="unit_id", target_type="string"),
                "title": FieldMapping(source_field="unit_title", target_type="string"),
                "key_stage": FieldMapping(source_field="key_stage", target_type="int"),
            },
        )

    @pytest.fixture
    def sample_relationship_mapping(self):
        return RelationshipMapping(
            type="CONTAINS",
            start_node_id_field="unit_id",
            end_node_id_field="lesson_id",
            properties={
                "order": FieldMapping(source_field="order_in_unit", target_type="int")
            },
        )

    @pytest.fixture
    def sample_node_data(self):
        return [
            {
                "unit_id": "unit_1",
                "unit_title": "Introduction to Science",
                "key_stage": "2",
                "created_at": "2023-01-01",
            },
            {
                "unit_id": "unit_2",
                "unit_title": "Advanced Chemistry",
                "key_stage": "4",
                "created_at": "2023-02-01",
            },
        ]

    def test_map_node_data_basic(self, sample_node_mapping, sample_node_data):
        mapper = SchemaMapper()
        df, lineage = mapper.map_node_data(sample_node_data, sample_node_mapping)

        assert len(df) == 2
        assert ":ID" in df.columns
        assert ":LABEL" in df.columns
        assert "id" in df.columns
        assert "title" in df.columns
        assert "key_stage" in df.columns

        # Check labels are correct
        assert (df[":LABEL"] == "Unit").all()

        # Check IDs are generated (UUIDs)
        for generated_id in df[":ID"]:
            UUID(generated_id)  # Should not raise exception

        # Check data mapping
        assert df.iloc[0]["title"] == "Introduction to Science"
        assert df.iloc[0]["key_stage"] == 2  # Converted to int

    def test_map_node_data_empty(self, sample_node_mapping):
        mapper = SchemaMapper()
        df, lineage = mapper.map_node_data([], sample_node_mapping)

        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)

    def test_map_node_data_missing_id_field(self, sample_node_mapping):
        mapper = SchemaMapper()
        data = [{"unit_title": "Test", "key_stage": "2"}]  # Missing unit_id
        df, lineage = mapper.map_node_data(data, sample_node_mapping)

        assert len(df) == 0

    def test_id_generation_consistency(self, sample_node_mapping):
        mapper = SchemaMapper()
        data = [
            {"unit_id": "unit_1", "unit_title": "Test 1", "key_stage": "1"},
            {
                "unit_id": "unit_1",
                "unit_title": "Test 2",
                "key_stage": "2",
            },  # Same ID
        ]
        df, lineage = mapper.map_node_data(data, sample_node_mapping)

        # Same original ID should get same generated ID
        assert df.iloc[0][":ID"] == df.iloc[1][":ID"]

    def test_map_relationship_data_basic(self, sample_relationship_mapping):
        # First create nodes to have generated IDs
        node_mapping = NodeMapping(
            label="Unit",
            id_field="unit_id",
            properties={
                "id": FieldMapping(source_field="unit_id", target_type="string")
            },
        )
        lesson_mapping = NodeMapping(
            label="Lesson",
            id_field="lesson_id",
            properties={
                "id": FieldMapping(source_field="lesson_id", target_type="string")
            },
        )

        mapper = SchemaMapper()

        # Create nodes first to generate IDs
        mapper.map_node_data([{"unit_id": "unit_1"}], node_mapping)
        mapper.map_node_data([{"lesson_id": "lesson_1"}], lesson_mapping)

        # Now create relationship
        rel_data = [{"unit_id": "unit_1", "lesson_id": "lesson_1", "order_in_unit": 1}]
        df, lineage = mapper.map_relationship_data(
            rel_data, sample_relationship_mapping
        )

        assert len(df) == 1
        assert ":START_ID" in df.columns
        assert ":END_ID" in df.columns
        assert ":TYPE" in df.columns
        assert "order" in df.columns

        assert df.iloc[0][":TYPE"] == "CONTAINS"
        assert df.iloc[0]["order"] == 1

    def test_map_relationship_data_missing_nodes(self, sample_relationship_mapping):
        mapper = SchemaMapper()
        rel_data = [{"unit_id": "unit_1", "lesson_id": "lesson_1", "order_in_unit": 1}]
        df, lineage = mapper.map_relationship_data(
            rel_data, sample_relationship_mapping
        )

        # Should return empty DataFrame as referenced nodes don't exist
        assert len(df) == 0

    def test_field_transformations(self):
        mapper = SchemaMapper()

        # Test transformations
        assert mapper._apply_transformation("hello", "uppercase") == "HELLO"
        assert mapper._apply_transformation("WORLD", "lowercase") == "world"
        assert mapper._apply_transformation("  test  ", "strip") == "test"
        assert mapper._apply_transformation("value", "prefix:PRE_") == "PRE_value"
        assert mapper._apply_transformation("value", "suffix:_SUF") == "value_SUF"
        assert mapper._apply_transformation("value", "unknown") == "value"

    def test_type_conversions(self):
        mapper = SchemaMapper()

        # Test string conversion
        assert mapper._convert_type(123, "string") == "123"
        assert mapper._convert_type(None, "string") is None

        # Test int conversion
        assert mapper._convert_type("123", "int") == 123
        assert mapper._convert_type("123.7", "int") == 123
        assert mapper._convert_type("", "int") is None
        assert mapper._convert_type(None, "int") is None

        # Test float conversion
        assert mapper._convert_type("123.45", "float") == 123.45
        assert mapper._convert_type("", "float") is None

        # Test boolean conversion
        assert mapper._convert_type("true", "boolean") is True
        assert mapper._convert_type("false", "boolean") is False
        assert mapper._convert_type("1", "boolean") is True
        assert mapper._convert_type("0", "boolean") is False
        assert mapper._convert_type(True, "boolean") is True

    def test_get_node_id_mapping(self, sample_node_mapping):
        mapper = SchemaMapper()
        data = [{"unit_id": "unit_1", "unit_title": "Test", "key_stage": "1"}]
        df, lineage = mapper.map_node_data(data, sample_node_mapping)

        generated_id = mapper.get_node_id_mapping("Unit", "unit_1")
        assert generated_id is not None
        assert generated_id == df.iloc[0][":ID"]

        # Non-existent mapping should return None
        assert mapper.get_node_id_mapping("Unit", "unit_999") is None

    def test_clear_lineage(self, sample_node_mapping):
        mapper = SchemaMapper()
        data = [{"unit_id": "unit_1", "unit_title": "Test", "key_stage": "1"}]
        mapper.map_node_data(data, sample_node_mapping)

        # Should have lineage data
        assert len(mapper.lineage.transformations) > 0
        assert len(mapper._generated_ids) > 0

        mapper.clear_lineage()

        # Should be cleared
        assert len(mapper.lineage.transformations) == 0
        assert len(mapper._generated_ids) == 0

    def test_data_lineage_tracking(self, sample_node_mapping):
        mapper = SchemaMapper()
        data = [{"unit_id": "unit_1", "unit_title": "Test", "key_stage": "1"}]
        df, lineage = mapper.map_node_data(data, sample_node_mapping)

        # Should have recorded transformations
        transformations = [
            t for t in lineage.transformations if t["type"] == "field_mapping"
        ]
        assert len(transformations) == 3  # id, title, key_stage

        # Should have recorded ID generation
        id_generations = [
            t for t in lineage.transformations if t["type"] == "id_generation"
        ]
        assert len(id_generations) == 1

    def test_error_handling_invalid_mapping(self):
        mapping = NodeMapping(
            label="Unit",
            id_field="nonexistent_field",
            properties={
                "id": FieldMapping(source_field="unit_id", target_type="string")
            },
        )
        mapper = SchemaMapper()
        data = [{"unit_id": "unit_1"}]

        df, lineage = mapper.map_node_data(data, mapping)
        assert len(df) == 0  # Should handle missing field gracefully

    def test_comprehensive_transformation_with_lineage(self):
        mapping = NodeMapping(
            label="TestNode",
            id_field="id",
            properties={
                "upper_name": FieldMapping(
                    source_field="name",
                    target_type="string",
                    transformation="uppercase",
                ),
                "prefixed_code": FieldMapping(
                    source_field="code",
                    target_type="string",
                    transformation="prefix:CODE_",
                ),
                "numeric_value": FieldMapping(source_field="value", target_type="int"),
            },
        )

        mapper = SchemaMapper()
        data = [{"id": "1", "name": "test", "code": "abc", "value": "123"}]
        df, lineage = mapper.map_node_data(data, mapping)

        # Check transformations applied
        assert df.iloc[0]["upper_name"] == "TEST"
        assert df.iloc[0]["prefixed_code"] == "CODE_abc"
        assert df.iloc[0]["numeric_value"] == 123

        # Check lineage recorded all transformations
        field_mappings = [
            t for t in lineage.transformations if t["type"] == "field_mapping"
        ]
        assert len(field_mappings) == 3

        transformation_types = [t["transformation"] for t in field_mappings]
        assert "uppercase" in transformation_types
        assert "prefix:CODE_" in transformation_types
