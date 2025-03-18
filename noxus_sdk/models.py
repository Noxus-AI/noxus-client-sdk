from typing import List, Optional, Any
from pydantic import BaseModel, Field


class Link(BaseModel):
    node_id: str
    connector_name: str
    key: Optional[str] = None


class Edge(BaseModel):
    from_id: Link
    to_id: Link


class Variables(BaseModel):
    keys: List[str]


class Node(BaseModel):
    id: str
    type: str
    node_config: dict
    connector_config: dict


class Definition(BaseModel):
    edges: List[Edge]
    nodes: List[Node]


class Workflow(BaseModel):
    id: str
    name: str
    type: str
    definition: Definition
    last_updated_at: str
    last_run_at: Any
    created_at: str
    deleted_at: Any
    runs_count: Any
    author_name: str
    description: Any
    saved: Any


def validate_body(data, body):
    return True
    # raise NotImplementedError("Foo")
