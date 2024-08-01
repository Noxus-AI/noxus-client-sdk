from typing import List, Optional, Any
from pydantic import BaseModel, Field


class Link(BaseModel):
    node_id: str
    connector_name: str
    key: Optional[str] = None


class Edge(BaseModel):
    id: str
    from_id: Link
    to_id: Link


class Variables(BaseModel):
    keys: List[str]


class ConnectorConfig(BaseModel):
    variables: Optional[Variables] = None


class NodeConfig(BaseModel):
    type: Optional[str] = None
    label: Optional[str] = None
    value: Optional[Optional[str]] = None
    fixed_value: Optional[bool] = None
    extract_as: Optional[str] = None
    navigate_pages: Optional[bool] = None
    extract_as_list: Optional[bool] = None
    continue_on_error: Optional[bool] = None
    navigate_page_count: Optional[int] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    remove_formatting: Optional[bool] = None
    depth: Optional[str | int] = None
    to_scroll: Optional[bool] = None
    parse_html: Optional[bool] = None
    template: Optional[str] = None


class Node(BaseModel):
    id: str
    name: str
    type: str
    node_config: NodeConfig
    connector_config: ConnectorConfig


class Definition(BaseModel):
    edges: List[Edge]
    nodes: List[Node]


class Workflow(BaseModel):
    id: str
    user_id: str
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
    triggers: Any
    apps: Any


def validate_body(data, body):
    return True
    # raise NotImplementedError("Foo")
