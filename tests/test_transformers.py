import os
import tempfile
import pytest
import pandas as pd

from pipeline.transformers import (
    CSVTransformer,
    TransformerFactory,
    CSVNodeTransformationStrategy,
    CSVRelationshipTransformationStrategy,
)
from models.config import NodeMapping, RelationshipMapping, FieldMapping


class TestCSVTransformer:
    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_node_mapping(self):
        return NodeMapping(
            label="Unit",
            id_field="unit_id",
            properties={
                "id": FieldMapping(source_field="unit_id", target_type="string"),
                "title": FieldMapping(source_field="unit_title", target_type="string"),
                "stage": FieldMapping(source_field="key_stage", target_type="int"),
                "active": FieldMapping(source_field="is_active", target_type="boolean"),
            },
        )

    @pytest.fixture
    def sample_relationship_mapping(self):
        return RelationshipMapping(
            type="CONTAINS",
            start_node_id_field="unit_id",
            end_node_id_field="lesson_id",
            properties={
                "order": FieldMapping(source_field="order_in_unit", target_type="int"),
                "weight": FieldMapping(
                    source_field="weight_value", target_type="float"
                ),
            },
        )

    @pytest.fixture
    def sample_node_dataframe(self):
        return pd.DataFrame(
            [
                {
                    ":ID": "uuid-1",
                    ":LABEL": "Unit",
                    "id": "unit_1",
                    "title": "Test Unit 1",
                    "stage": 2,
                    "active": True,
                },
                {
                    ":ID": "uuid-2",
                    ":LABEL": "Unit",
                    "id": "unit_2",
                    "title": "Test Unit 2",
                    "stage": 3,
                    "active": False,
                },
            ]
        )

    @pytest.fixture
    def sample_relationship_dataframe(self):
        return pd.DataFrame(
            [
                {
                    ":START_ID": "uuid-1",
                    ":END_ID": "uuid-3",
                    ":TYPE": "CONTAINS",
                    "order": 1,
                    "weight": 0.8,
                },
                {
                    ":START_ID": "uuid-2",
                    ":END_ID": "uuid-4",
                    ":TYPE": "CONTAINS",
                    "order": 2,
                    "weight": 0.9,
                },
            ]
        )

    def test_init(self, temp_output_dir):
        transformer = CSVTransformer(temp_output_dir)
        assert transformer.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)

    def test_init_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_parent:
            output_dir = os.path.join(temp_parent, "new_output")
            CSVTransformer(output_dir)
            assert os.path.exists(output_dir)

    def test_transform_nodes_to_csv(
        self, temp_output_dir, sample_node_dataframe, sample_node_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        csv_path = transformer.transform_nodes_to_csv(
            sample_node_dataframe, sample_node_mapping
        )

        # Check file was created
        assert os.path.exists(csv_path)
        assert csv_path.endswith("unit_nodes.csv")

        # Read and validate CSV content
        df = pd.read_csv(csv_path)
        assert len(df) == 2

        # Check headers have proper type annotations
        expected_headers = [
            ":ID",
            ":LABEL",
            "id:string",
            "title:string",
            "stage:int",
            "active:boolean",
        ]
        assert list(df.columns) == expected_headers

        # Check data integrity
        assert df.iloc[0]["id:string"] == "unit_1"
        assert df.iloc[0]["title:string"] == "Test Unit 1"
        assert df.iloc[0]["stage:int"] == 2
        assert df.iloc[0]["active:boolean"]

    def test_transform_nodes_to_csv_empty_data(
        self, temp_output_dir, sample_node_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="No data to transform for node Unit"):
            transformer.transform_nodes_to_csv(empty_df, sample_node_mapping)

    def test_transform_nodes_to_csv_missing_columns(
        self, temp_output_dir, sample_node_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        invalid_df = pd.DataFrame([{"id": "1", "title": "Test"}])  # Missing :ID, :LABEL

        with pytest.raises(ValueError, match="Missing required columns.*:ID.*:LABEL"):
            transformer.transform_nodes_to_csv(invalid_df, sample_node_mapping)

    def test_transform_relationships_to_csv(
        self,
        temp_output_dir,
        sample_relationship_dataframe,
        sample_relationship_mapping,
    ):
        transformer = CSVTransformer(temp_output_dir)
        csv_path = transformer.transform_relationships_to_csv(
            sample_relationship_dataframe, sample_relationship_mapping
        )

        # Check file was created
        assert os.path.exists(csv_path)
        assert csv_path.endswith("contains_relationships.csv")

        # Read and validate CSV content
        df = pd.read_csv(csv_path)
        assert len(df) == 2

        # Check headers have proper type annotations
        expected_headers = [
            ":START_ID",
            ":END_ID",
            ":TYPE",
            "order:int",
            "weight:float",
        ]
        assert list(df.columns) == expected_headers

        # Check data integrity
        assert df.iloc[0][":START_ID"] == "uuid-1"
        assert df.iloc[0][":END_ID"] == "uuid-3"
        assert df.iloc[0][":TYPE"] == "CONTAINS"
        assert df.iloc[0]["order:int"] == 1
        assert df.iloc[0]["weight:float"] == 0.8

    def test_transform_relationships_to_csv_empty_data(
        self, temp_output_dir, sample_relationship_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        empty_df = pd.DataFrame()

        with pytest.raises(
            ValueError, match="No data to transform for relationship CONTAINS"
        ):
            transformer.transform_relationships_to_csv(
                empty_df, sample_relationship_mapping
            )

    def test_transform_relationships_to_csv_missing_columns(
        self, temp_output_dir, sample_relationship_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        invalid_df = pd.DataFrame([{"order": 1}])  # Missing :START_ID, :END_ID, :TYPE

        with pytest.raises(
            ValueError, match="Missing required columns.*:START_ID.*:END_ID.*:TYPE"
        ):
            transformer.transform_relationships_to_csv(
                invalid_df, sample_relationship_mapping
            )

    def test_generate_typed_headers(self, temp_output_dir, sample_node_mapping):
        transformer = CSVTransformer(temp_output_dir)
        df = pd.DataFrame(
            columns=[":ID", ":LABEL", "id", "title", "stage", "unknown_field"]
        )

        typed_headers = transformer._generate_typed_headers(df, sample_node_mapping)

        expected = [
            ":ID",
            ":LABEL",
            "id:string",
            "title:string",
            "stage:int",
            "unknown_field:string",
        ]
        assert typed_headers == expected

    def test_generate_typed_relationship_headers(
        self, temp_output_dir, sample_relationship_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        df = pd.DataFrame(
            columns=[
                ":START_ID",
                ":END_ID",
                ":TYPE",
                "order",
                "weight",
                "unknown_field",
            ]
        )

        typed_headers = transformer._generate_typed_relationship_headers(
            df, sample_relationship_mapping
        )

        expected = [
            ":START_ID",
            ":END_ID",
            ":TYPE",
            "order:int",
            "weight:float",
            "unknown_field:string",
        ]
        assert typed_headers == expected

    def test_get_field_type_from_mapping(self, temp_output_dir, sample_node_mapping):
        transformer = CSVTransformer(temp_output_dir)

        # Test known field
        assert (
            transformer._get_field_type_from_mapping("title", sample_node_mapping)
            == "string"
        )
        assert (
            transformer._get_field_type_from_mapping("stage", sample_node_mapping)
            == "int"
        )

        # Test unknown field (should default to string)
        assert (
            transformer._get_field_type_from_mapping("unknown", sample_node_mapping)
            == "string"
        )

    def test_get_relationship_field_type_from_mapping(
        self, temp_output_dir, sample_relationship_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)

        # Test known field
        assert (
            transformer._get_relationship_field_type_from_mapping(
                "order", sample_relationship_mapping
            )
            == "int"
        )
        assert (
            transformer._get_relationship_field_type_from_mapping(
                "weight", sample_relationship_mapping
            )
            == "float"
        )

        # Test unknown field (should default to string)
        assert (
            transformer._get_relationship_field_type_from_mapping(
                "unknown", sample_relationship_mapping
            )
            == "string"
        )

    def test_generate_import_summary(
        self,
        temp_output_dir,
        sample_node_dataframe,
        sample_relationship_dataframe,
        sample_node_mapping,
        sample_relationship_mapping,
    ):
        transformer = CSVTransformer(temp_output_dir)

        # Create test CSV files
        node_path = transformer.transform_nodes_to_csv(
            sample_node_dataframe, sample_node_mapping
        )
        rel_path = transformer.transform_relationships_to_csv(
            sample_relationship_dataframe, sample_relationship_mapping
        )

        summary = transformer.generate_import_summary([node_path], [rel_path])

        assert summary["total_files"] == 2
        assert summary["node_files"] == 1
        assert summary["relationship_files"] == 1
        assert summary["total_records"] == 4  # 2 nodes + 2 relationships

        # Check file details
        assert len(summary["files"]["nodes"]) == 1
        assert len(summary["files"]["relationships"]) == 1
        assert summary["files"]["nodes"][0]["records"] == 2
        assert summary["files"]["relationships"][0]["records"] == 2

    def test_generate_import_summary_nonexistent_files(self, temp_output_dir):
        transformer = CSVTransformer(temp_output_dir)
        summary = transformer.generate_import_summary(["/nonexistent/file.csv"], [])

        assert summary["total_files"] == 1
        assert summary["total_records"] == 0
        assert len(summary["files"]["nodes"]) == 0

    def test_validate_csv_format_valid_node(
        self, temp_output_dir, sample_node_dataframe, sample_node_mapping
    ):
        transformer = CSVTransformer(temp_output_dir)
        csv_path = transformer.transform_nodes_to_csv(
            sample_node_dataframe, sample_node_mapping
        )

        is_valid, errors = transformer.validate_csv_format(csv_path, "node")
        assert is_valid
        assert len(errors) == 0

    def test_validate_csv_format_valid_relationship(
        self,
        temp_output_dir,
        sample_relationship_dataframe,
        sample_relationship_mapping,
    ):
        transformer = CSVTransformer(temp_output_dir)
        csv_path = transformer.transform_relationships_to_csv(
            sample_relationship_dataframe, sample_relationship_mapping
        )

        is_valid, errors = transformer.validate_csv_format(csv_path, "relationship")
        assert is_valid
        assert len(errors) == 0

    def test_validate_csv_format_invalid_node_missing_id(self, temp_output_dir):
        transformer = CSVTransformer(temp_output_dir)

        # Create invalid node CSV (missing :ID)
        invalid_df = pd.DataFrame([{":LABEL": "Test", "name:string": "test"}])
        csv_path = os.path.join(temp_output_dir, "invalid_node.csv")
        invalid_df.to_csv(csv_path, index=False)

        is_valid, errors = transformer.validate_csv_format(csv_path, "node")
        assert not is_valid
        assert "Missing required :ID column" in " ".join(errors)

    def test_validate_csv_format_invalid_relationship_missing_columns(
        self, temp_output_dir
    ):
        transformer = CSVTransformer(temp_output_dir)

        # Create invalid relationship CSV (missing required columns)
        invalid_df = pd.DataFrame([{"order:int": 1}])
        csv_path = os.path.join(temp_output_dir, "invalid_rel.csv")
        invalid_df.to_csv(csv_path, index=False)

        is_valid, errors = transformer.validate_csv_format(csv_path, "relationship")
        assert not is_valid
        assert any("Missing required" in error for error in errors)

    def test_validate_csv_format_missing_type_annotations(self, temp_output_dir):
        transformer = CSVTransformer(temp_output_dir)

        # Create CSV with missing type annotations
        invalid_df = pd.DataFrame(
            [{":ID": "1", ":LABEL": "Test", "name": "test"}]
        )  # 'name' missing type
        csv_path = os.path.join(temp_output_dir, "no_types.csv")
        invalid_df.to_csv(csv_path, index=False)

        is_valid, errors = transformer.validate_csv_format(csv_path, "node")
        assert not is_valid
        assert "missing type annotation" in " ".join(errors)

    def test_validate_csv_format_nonexistent_file(self, temp_output_dir):
        transformer = CSVTransformer(temp_output_dir)

        is_valid, errors = transformer.validate_csv_format(
            "/nonexistent/file.csv", "node"
        )
        assert not is_valid
        assert "does not exist" in errors[0]

    def test_csv_encoding_and_quoting(self, temp_output_dir, sample_node_mapping):
        transformer = CSVTransformer(temp_output_dir)

        # Test with special characters and unicode
        df_with_unicode = pd.DataFrame(
            [
                {
                    ":ID": "uuid-1",
                    ":LABEL": "Unit",
                    "id": "unit_1",
                    "title": "Test Ünit with 'quotes' and, commas",
                    "stage": 2,
                    "active": True,
                }
            ]
        )

        csv_path = transformer.transform_nodes_to_csv(
            df_with_unicode, sample_node_mapping
        )

        # Read back and verify content
        df_read = pd.read_csv(csv_path)
        assert df_read.iloc[0]["title:string"] == "Test Ünit with 'quotes' and, commas"

    def test_csv_na_handling(self, temp_output_dir, sample_node_mapping):
        transformer = CSVTransformer(temp_output_dir)

        # Test with NA/None values
        df_with_na = pd.DataFrame(
            [
                {
                    ":ID": "uuid-1",
                    ":LABEL": "Unit",
                    "id": "unit_1",
                    "title": None,  # NA value
                    "stage": 2,
                    "active": True,
                }
            ]
        )

        csv_path = transformer.transform_nodes_to_csv(df_with_na, sample_node_mapping)

        # Read back and verify NA is handled correctly (should be empty string)
        with open(csv_path, "r") as f:
            content = f.read()
            # Should have empty quoted string for None values
            assert '"","' in content or '"",' in content


class TestCSVNodeTransformationStrategy:
    def test_init(self):
        strategy = CSVNodeTransformationStrategy("test_dir")
        assert strategy.csv_transformer.output_dir == "test_dir"

    def test_transform_not_implemented(self):
        strategy = CSVNodeTransformationStrategy()

        with pytest.raises(
            NotImplementedError, match="Use CSVTransformer.transform_nodes_to_csv"
        ):
            strategy.transform(
                [], NodeMapping(label="Test", id_field="id", properties={})
            )


class TestCSVRelationshipTransformationStrategy:
    def test_init(self):
        strategy = CSVRelationshipTransformationStrategy("test_dir")
        assert strategy.csv_transformer.output_dir == "test_dir"

    def test_transform_relationships_not_implemented(self):
        strategy = CSVRelationshipTransformationStrategy()

        with pytest.raises(
            NotImplementedError,
            match="Use CSVTransformer.transform_relationships_to_csv",
        ):
            strategy.transform_relationships(
                [],
                RelationshipMapping(
                    type="TEST",
                    start_node_id_field="start",
                    end_node_id_field="end",
                    properties={},
                ),
            )


class TestTransformerFactory:
    def test_csv_strategies_registered(self):
        node_strategies = TransformerFactory.get_available_node_strategies()
        rel_strategies = TransformerFactory.get_available_relationship_strategies()

        assert "csv" in node_strategies
        assert "csv" in rel_strategies

    def test_create_csv_node_transformer(self):
        transformer = TransformerFactory.create_node_transformer("csv")
        assert isinstance(transformer, CSVNodeTransformationStrategy)

    def test_create_csv_relationship_transformer(self):
        transformer = TransformerFactory.create_relationship_transformer("csv")
        assert isinstance(transformer, CSVRelationshipTransformationStrategy)

    def test_create_unknown_strategy_raises_error(self):
        with pytest.raises(ValueError, match="Unknown node transformation strategy"):
            TransformerFactory.create_node_transformer("unknown")

        with pytest.raises(
            ValueError, match="Unknown relationship transformation strategy"
        ):
            TransformerFactory.create_relationship_transformer("unknown")

    def test_register_custom_node_strategy(self):
        class CustomNodeStrategy:
            pass

        TransformerFactory.register_node_strategy("custom", CustomNodeStrategy)
        strategies = TransformerFactory.get_available_node_strategies()
        assert "custom" in strategies

        transformer = TransformerFactory.create_node_transformer("custom")
        assert isinstance(transformer, CustomNodeStrategy)

    def test_register_custom_relationship_strategy(self):
        class CustomRelStrategy:
            pass

        TransformerFactory.register_relationship_strategy(
            "custom_rel", CustomRelStrategy
        )
        strategies = TransformerFactory.get_available_relationship_strategies()
        assert "custom_rel" in strategies

        transformer = TransformerFactory.create_relationship_transformer("custom_rel")
        assert isinstance(transformer, CustomRelStrategy)
