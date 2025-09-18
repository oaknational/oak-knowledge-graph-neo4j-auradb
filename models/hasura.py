from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HasuraError(BaseModel):
    message: str
    extensions: Optional[Dict[str, Any]] = None


class HasuraResponse(BaseModel):
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[HasuraError]] = None


class MaterializedViewRecord(BaseModel):
    data: Dict[str, Any]


class MaterializedViewResponse(BaseModel):
    records: List[MaterializedViewRecord]
    total_count: Optional[int] = None
