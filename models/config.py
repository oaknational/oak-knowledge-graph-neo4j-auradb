from typing import Dict, List, Optional
from pydantic import BaseModel


class FieldMapping(BaseModel):
    source_field: str
    target_type: str
    transformation: Optional[str] = None


class NodeMapping(BaseModel):
    label: str
    id_field: str
    properties: Dict[str, FieldMapping]


class RelationshipMapping(BaseModel):
    type: str
    start_node_id_field: str
    end_node_id_field: str
    properties: Dict[str, FieldMapping]


class PipelineConfig(BaseModel):
    hasura_endpoint: str
    materialized_views: List[str]
    node_mappings: List[NodeMapping]
    relationship_mappings: List[RelationshipMapping]
    test_limit: Optional[int] = None
