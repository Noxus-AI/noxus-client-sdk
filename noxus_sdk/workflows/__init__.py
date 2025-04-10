import enum
import uuid
from typing import Any, TYPE_CHECKING
from pydantic import BaseModel, Field, TypeAdapter, model_validator
from pydantic.config import ConfigDict

from noxus_sdk.client import Client

if TYPE_CHECKING:
    from noxus_sdk.resources.runs import Run


class ConfigError(Exception):
    pass


class DataType(str, enum.Enum):
    int = "int"
    float = "float"
    bool = "bool"
    dict = "dict"
    str = "str"
    list = "list"
    Image = "Image"
    Audio = "Audio"
    File = "File"
    Quote = "Quote"
    Custom = "Custom"
    NoxusAny = "Any"
    GoogleSheet = "GoogleSheet"
    SourceType = "SourceType"

    def validate(self, value: Any):
        try:
            match self:
                case DataType.int:
                    if not isinstance(value, int):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.float:
                    if not isinstance(value, (float, int)):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.bool:
                    if not isinstance(value, bool):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.dict:
                    if not isinstance(value, dict):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.str:
                    if not isinstance(value, str):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.list:
                    if not isinstance(value, list):
                        raise ValueError(
                            f"value '{value}' for data type {self} is invalid"
                        )
                case DataType.Image:
                    return value
                case DataType.Audio:
                    return value
                case DataType.File:
                    return value
                case DataType.Quote:
                    return value
                case DataType.Custom:
                    return value
                case DataType.NoxusAny:
                    return value
                case DataType.GoogleSheet:
                    return value
                case DataType.SourceType:
                    return value
                case _:
                    raise ValueError(f"Invalid data type: {self}")
        except Exception as e:
            raise ValueError(f"value '{value}' for data type {self} is invalid ({e})")


class ConfigDefinition(BaseModel):
    type: DataType
    description: str | None
    visible: bool
    optional: bool
    default: Any

    def check_value(self, key: str, value: Any):
        if value is None:
            if not self.optional:
                raise ConfigError(f"Missing required config value for {key}")
            if self.default is not None:
                value = self.default
            if value == self.default:
                return
        try:
            self.type.validate(value)
        except Exception as e:
            raise ConfigError(f"Invalid config value for {key}: [{e}]")


class NodeDefinition(BaseModel):
    type: str
    title: str
    description: str
    integrations: list[str]
    inputs: list[dict]
    outputs: list[dict]
    config: dict[str, ConfigDefinition]
    is_available: bool
    visible: bool
    config_endpoint: str | None


NODE_TYPES: dict[str, NodeDefinition] = {}


def load_node_types(nodes_: list[dict]):
    NODE_TYPES.clear()
    nodes: list[NodeDefinition] = TypeAdapter(list[NodeDefinition]).validate_python(
        nodes_
    )
    for node in nodes:
        NODE_TYPES[node.type] = node


class ConnectorType(str, enum.Enum):
    variable_connector = "variable_connector"
    variable_type_connector = "variable_type_connector"
    variable_type_size_connector = "variable_type_size_connector"
    variable_type_input = "variable_type_input"
    variable_type_output = "variable_type_output"
    connector = "connector"
    input = "input"
    output = "output"


class NodeInput(BaseModel):
    node_id: str
    name: str
    fixed_value: Any = None
    type: ConnectorType

    @property
    def id(self):
        return f"{self.node_id}::{self.name}"


class EdgePoint(BaseModel):
    node_id: str
    connector_name: str
    key: str | None = None
    optional: bool = False


class Edge(BaseModel):
    from_id: EdgePoint
    to_id: EdgePoint
    id: str | None = None


class NodeOutput(BaseModel):
    node_id: str
    name: str
    type: ConnectorType

    @property
    def id(self):
        return f"{self.node_id}::{self.name}"


class Node(BaseModel):
    type: str
    id: str
    name: str = ""
    display: dict = {}

    node_config: dict = {}
    connector_config: dict = {}
    config_definition: dict[str, ConfigDefinition] = {}
    inputs: list[NodeInput] = []
    outputs: list[NodeOutput] = []

    def input(self, name: str | None = None, key: str | None = None) -> EdgePoint:
        if name is None:
            if len(self.inputs) != 1:
                raise ValueError("Multiple inputs found, please specify a name")
            name = self.inputs[0].name
        i = {i.name: i for i in self.inputs}
        if name not in i:
            raise KeyError(f"Input {name} not found (possible: {list(i.keys())})")
        input = i[name]
        if input.type == "variable_connector":
            if key is None:
                raise ValueError("key is required for variable_connector")
            connector_config = self.connector_config.get("inputs")
            if not connector_config:
                raise ValueError(f"connector_config is missing {self.connector_config}")
            connector_inputs = {i["name"]: i for i in connector_config}
            if name not in connector_inputs:
                raise ValueError(
                    f"Invalid key: {name} (possible: {list(connector_inputs.keys())})"
                )
            connector_keys = connector_inputs[name].get("keys", [])
            if key not in connector_keys:
                connector_keys.append(key)
            return EdgePoint(node_id=input.node_id, connector_name=input.name, key=key)
        return EdgePoint(node_id=input.node_id, connector_name=input.name, key=None)

    def output(self, name: str | None = None, key: str | None = None) -> EdgePoint:
        if name is None:
            if len(self.outputs) != 1:
                raise ValueError("Multiple outputs found, please specify a name")
            name = self.outputs[0].name
        i = {i.name: i for i in self.outputs}
        if name not in i:
            raise KeyError(f"Output {name} not found (possible: {list(i.keys())})")
        output = i[name]
        if output.type == "variable_connector":
            if key is None:
                raise ValueError("key is required for variable_connector")
            connector_config = self.connector_config.get("outputs")
            if not connector_config:
                raise ValueError("connector_config is missing")
            connector_outputs = {o["name"]: o for o in connector_config}
            if name not in connector_outputs:
                raise ValueError(
                    f"Invalid key: {name} (possible: {list(connector_outputs.keys())})"
                )
            connector_keys = connector_outputs[name].get("keys", [])
            if key not in connector_keys:
                connector_keys.append(key)
            return EdgePoint(
                node_id=output.node_id, connector_name=output.name, key=key
            )
        return EdgePoint(node_id=output.node_id, connector_name=output.name, key=None)

    def create(self, x: int, y: int) -> "Node":
        node_type = NODE_TYPES.get(self.type)
        assert node_type, f"Node type {self.type} not found"
        self.config_definition = node_type.config
        self.inputs = [
            NodeInput(node_id=str(self.id), name=input["name"], type=input["type"])
            for input in node_type.inputs
        ]
        self.outputs = [
            NodeOutput(node_id=str(self.id), name=output["name"], type=output["type"])
            for output in node_type.outputs
        ]
        if not self.connector_config:
            self.connector_config = {
                "inputs": node_type.inputs,
                "outputs": node_type.outputs,
            }
        self.name = node_type.title
        self.display = {"position": {"x": x, "y": y}}
        return self

    def config(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.config_definition:
                raise ConfigError(
                    f"Invalid config key: {key} (possible: {[k for k,v in self.config_definition.items() if v.visible]})"
                )
            self.config_definition[key].check_value(key, value)
            self.node_config[key] = value
        for k, v in self.config_definition.items():
            if k not in self.node_config:
                v.check_value(k, None)
        return self

    @model_validator(mode="after")
    def call_create_after_validate(self):
        old_display = dict(self.display)
        self.create(0, 0)
        if old_display:
            self.display = old_display
        return self


class WorkflowDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: Client | None = Field(default=None, exclude=True)
    id: str = ""
    group_id: str | None = Field(default=None, exclude=True)
    name: str = "Untitled Workflow"
    type: str = "flow"
    nodes: list["Node"] = []
    edges: list["Edge"] = []
    x: int = 0

    @model_validator(mode="before")
    @classmethod
    def foo(cls, values):
        if "definition" in values:
            values["nodes"] = values["definition"]["nodes"]
            values["edges"] = values["definition"]["edges"]
        return values

    def to_noxus(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "definition": {
                "nodes": [n.model_dump() for n in self.nodes],
                "edges": [e.model_dump() for e in self.edges],
            },
        }

    def refresh_from_data(self, **data):
        n = self.__class__.model_validate(data)
        for k in n.model_fields_set:
            v = getattr(n, k)
            setattr(self, k, v)
        return self

    def refresh(self) -> "WorkflowDefinition":
        if not self.client:
            raise ValueError("Client not set")
        response = self.client.get(f"/v1/workflows/{self.id}")
        self.refresh_from_data(client=self.client, **response)
        return self

    async def arefresh(self) -> "WorkflowDefinition":
        if not self.client:
            raise ValueError("Client not set")
        response = await self.client.aget(f"/v1/workflows/{self.id}")
        self.refresh_from_data(client=self.client, **response)
        return self

    def run(self, body: dict[str, Any]) -> "Run":
        from noxus_sdk.resources.runs import Run

        if not self.client:
            raise ValueError("Client not set")
        response = self.client.post(f"/v1/workflows/{self.id}/runs", {"input": body})
        return Run(client=self.client, **response)

    async def arun(self, body: dict[str, Any]) -> "Run":
        if not self.client:
            raise ValueError("Client not set")
        from noxus_sdk.resources.runs import Run

        response = await self.client.apost(
            f"/v1/workflows/{self.id}/runs", {"input": body}
        )
        return Run(client=self.client, **response)

    def update(self, force: bool = False):
        if not self.client:
            raise ValueError("Client not set")
        w = self.client.workflows.update(self.id, self, force)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    async def aupdate(self, force: bool = False):
        if not self.client:
            raise ValueError("Client not set")
        w = await self.client.workflows.aupdate(self.id, self, force)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    def save(self):
        if not self.client:
            raise ValueError("Client not set")
        w = self.client.workflows.save(self)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    async def asave(self):
        if not self.client:
            raise ValueError("Client not set")
        w = await self.client.workflows.asave(self)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    def node(self, name) -> "Node":
        self.x += 350
        n = Node(id=str(uuid.uuid4()), type=name)
        n.create(x=self.x, y=0)
        self.nodes.append(n)
        return n

    def link(self, from_node: EdgePoint, to_node: EdgePoint) -> "Edge":
        e = Edge(id=str(uuid.uuid4()), from_id=from_node, to_id=to_node)
        self.edges.append(e)
        return e

    def link_many(self, *nodes: Node):
        for i in range(len(nodes) - 1):
            assert len(nodes[i].outputs) == 1
            if nodes[i].outputs[0].type == "variable_connector":
                raise ValueError(
                    f"A key is required for variable_connector output so unable to link {nodes[i].type} to {nodes[i + 1].type} automatically"
                )
            assert len(nodes[i + 1].inputs) == 1
            if nodes[i + 1].inputs[0].type == "variable_connector":
                raise ValueError(
                    f"A key is required for variable_connector input so unable to link {nodes[i].type} to {nodes[i + 1].type} automatically"
                )
            self.link(nodes[i].output(), nodes[i + 1].input())
