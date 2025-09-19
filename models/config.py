from typing import Dict, List, Optional
from pydantic import BaseModel


class FieldMapping(BaseModel):
    source_field: str
    target_type: str
    transformation: Optional[str] = None
    computation: Optional[str] = None  # For computed fields like concat:field1, ,field2


class NodeMapping(BaseModel):
    label: str
    id_field: str
    properties: Dict[str, FieldMapping]
    deduplication_key: Optional[str] = None  # Comma-separated fields for deduplication
    id_generation: Optional[str] = "uuid"  # "uuid", "source_field", "computed"
    id_computation: Optional[str] = None  # For computed IDs


class RelationshipMapping(BaseModel):
    type: str
    start_node_id_field: str
    end_node_id_field: str
    properties: Dict[str, FieldMapping]
    match_strategy: Optional[str] = "direct"  # "direct" or "business_id"
    start_business_key: Optional[str] = None  # For UUID matching
    end_business_key: Optional[str] = None  # For UUID matching


class PipelineConfig(BaseModel):
    hasura_endpoint: str
    materialized_views: List[str]
    node_mappings: List[NodeMapping]
    relationship_mappings: List[RelationshipMapping]
    test_limit: Optional[int] = None
    clear_database_before_import: bool = False
