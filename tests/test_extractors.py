import json
import os
import pytest
import requests
from unittest.mock import Mock, patch
from models.config import PipelineConfig
from pipeline.extractors import HasuraExtractor, ExtractorFactory


class TestHasuraExtractor:
    @pytest.fixture
    def sample_config(self):
        return PipelineConfig(
            hasura_endpoint="https://test-hasura.com/v1/graphql",
            materialized_views=["curriculum_units", "curriculum_lessons"],
            node_mappings=[],
            relationship_mappings=[],
        )

    @pytest.fixture
    def mock_fixtures(self):
        fixtures_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "hasura_responses.json"
        )
        with open(fixtures_path, "r") as f:
            return json.load(f)

    def test_init_with_api_key(self):
        extractor = HasuraExtractor(api_key="test-key")
        assert extractor.api_key == "test-key"

    def test_init_with_env_var(self):
        with patch.dict(os.environ, {"HASURA_API_KEY": "env-key"}):
            extractor = HasuraExtractor()
            assert extractor.api_key == "env-key"

    def test_init_without_api_key_raises_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Hasura API key required"):
                HasuraExtractor()

    @patch("pipeline.extractors.requests.post")
    def test_successful_extraction(
        self, mock_post, sample_config, mock_fixtures
    ):
        extractor = HasuraExtractor(api_key="test-key")

        # Mock successful responses for both views
        mock_responses = [
            Mock(
                status_code=200,
                json=Mock(
                    return_value=mock_fixtures["curriculum_units_success"]
                ),
            ),
            Mock(
                status_code=200,
                json=Mock(
                    return_value=mock_fixtures["curriculum_lessons_success"]
                ),
            ),
        ]
        mock_post.side_effect = mock_responses

        result = extractor.extract(sample_config)

        assert len(result) == 4  # 2 units + 2 lessons
        assert mock_post.call_count == 2

        # Verify API calls were made correctly
        for call in mock_post.call_args_list:
            args, kwargs = call
            assert args[0] == sample_config.hasura_endpoint
            assert kwargs["headers"]["x-hasura-admin-secret"] == "test-key"
            assert kwargs["headers"]["Content-Type"] == "application/json"
            assert "query" in kwargs["json"]

    @patch("pipeline.extractors.requests.post")
    def test_graphql_error_handling(
        self, mock_post, sample_config, mock_fixtures
    ):
        extractor = HasuraExtractor(api_key="test-key")

        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_fixtures["graphql_error_response"]),
        )

        with pytest.raises(RuntimeError, match="GraphQL errors"):
            extractor.extract(sample_config)

    @patch("pipeline.extractors.requests.post")
    def test_authentication_error_handling(
        self, mock_post, sample_config, mock_fixtures
    ):
        extractor = HasuraExtractor(api_key="invalid-key")

        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=mock_fixtures["authentication_error_response"]
            ),
        )

        with pytest.raises(RuntimeError, match="GraphQL errors"):
            extractor.extract(sample_config)

    @patch("pipeline.extractors.requests.post")
    def test_network_error_handling(self, mock_post, sample_config):
        extractor = HasuraExtractor(api_key="test-key")

        mock_post.side_effect = requests.ConnectionError("Network error")

        with pytest.raises(RuntimeError, match="API request failed"):
            extractor.extract(sample_config)

    @patch("pipeline.extractors.requests.post")
    def test_http_error_handling(self, mock_post, sample_config):
        extractor = HasuraExtractor(api_key="test-key")

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error"
        )
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="API request failed"):
            extractor.extract(sample_config)

    @patch("pipeline.extractors.requests.post")
    def test_empty_data_handling(
        self, mock_post, sample_config, mock_fixtures
    ):
        extractor = HasuraExtractor(api_key="test-key")

        # Return empty data for both views
        mock_responses = [
            Mock(
                status_code=200,
                json=Mock(return_value=mock_fixtures["empty_data_response"]),
            ),
            Mock(
                status_code=200,
                json=Mock(
                    return_value={
                        "data": {"curriculum_lessons": []},
                        "errors": None,
                    }
                ),
            ),
        ]
        mock_post.side_effect = mock_responses

        result = extractor.extract(sample_config)
        assert result == []

    @patch("pipeline.extractors.requests.post")
    def test_missing_view_data_error(self, mock_post, sample_config):
        extractor = HasuraExtractor(api_key="test-key")

        # Response missing the requested view
        mock_response_data = {"data": {"other_view": []}, "errors": None}
        mock_post.return_value = Mock(
            status_code=200, json=Mock(return_value=mock_response_data)
        )

        with pytest.raises(RuntimeError, match="No data returned for view"):
            extractor.extract(sample_config)

    def test_build_graphql_query(self):
        extractor = HasuraExtractor(api_key="test-key")
        query = extractor._build_graphql_query("curriculum_units")

        assert "curriculum_units" in query
        assert "query" in query.lower()
        assert "__typename" in query

    def test_build_graphql_query_with_underscores(self):
        extractor = HasuraExtractor(api_key="test-key")
        query = extractor._build_graphql_query("lesson_relationships")

        assert "lesson_relationships" in query
        assert "GetLessonRelationships" in query

    @patch("pipeline.extractors.requests.post")
    def test_partial_failure_handling(self, mock_post, sample_config):
        extractor = HasuraExtractor(api_key="test-key")

        # First call succeeds, second fails
        mock_responses = [
            Mock(
                status_code=200,
                json=Mock(
                    return_value={
                        "data": {"curriculum_units": [{"id": "test"}]},
                        "errors": None,
                    }
                ),
            ),
            Mock(side_effect=requests.ConnectionError("Network error")),
        ]
        mock_post.side_effect = mock_responses

        with pytest.raises(
            RuntimeError,
            match="Failed to extract from view 'curriculum_lessons'",
        ):
            extractor.extract(sample_config)


class TestExtractorFactory:
    def test_hasura_strategy_registered(self):
        strategies = ExtractorFactory.get_available_strategies()
        assert "hasura" in strategies

    def test_create_hasura_extractor(self):
        with patch.dict(os.environ, {"HASURA_API_KEY": "test-key"}):
            extractor = ExtractorFactory.create_extractor("hasura")
            assert isinstance(extractor, HasuraExtractor)

    def test_unknown_strategy_raises_error(self):
        with pytest.raises(ValueError, match="Unknown extraction strategy"):
            ExtractorFactory.create_extractor("unknown")

    def test_register_custom_strategy(self):
        class CustomExtractor:
            pass

        ExtractorFactory.register_strategy("custom", CustomExtractor)
        strategies = ExtractorFactory.get_available_strategies()
        assert "custom" in strategies

        extractor = ExtractorFactory.create_extractor("custom")
        assert isinstance(extractor, CustomExtractor)
