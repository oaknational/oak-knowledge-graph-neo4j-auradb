from typing import Any, Dict, List
from pydantic import BaseModel


class Neo4jNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]


class Neo4jRelationship(BaseModel):
    start_id: str
    end_id: str
    type: str
    properties: Dict[str, Any]


class Neo4jImportNode(BaseModel):
    csv_headers: List[str]
    csv_data: List[List[Any]]
    label: str


class Neo4jImportRelationship(BaseModel):
    csv_headers: List[str]
    csv_data: List[List[Any]]
    type: str


class Neo4jImportCommand(BaseModel):
    database_name: str
    node_files: List[str]
    relationship_files: List[str]
    command: str
