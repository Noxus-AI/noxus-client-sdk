from typing import List, Optional, Any, TYPE_CHECKING
from pydantic import BaseModel

from noxus_sdk.resources.base import BaseResource, BaseService
from noxus_sdk.resources.runs import Run
from noxus_sdk.workflows import WorkflowDefinition

if TYPE_CHECKING:
    from noxus_sdk.workflows import WorkflowDefinition


class Link(BaseModel):
    node_id: str
    connector_name: str
    key: Optional[str] = None


class Edge(BaseModel):
    from_id: Link
    to_id: Link
    id: str | None = None


class Variables(BaseModel):
    keys: List[str]


class Node(BaseModel):
    id: str
    type: str
    node_config: dict
    connector_config: dict
    display: dict


class Definition(BaseModel):
    edges: List[Edge]
    nodes: List[Node]


class Workflow(BaseResource):
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

    def validate_body(self, body: dict[str, Any]):
        return True

    def to_builder(self) -> "WorkflowDefinition":
        from noxus_sdk.workflows import Node, Edge, WorkflowDefinition

        nodes = [Node.model_validate(n.model_dump()) for n in self.definition.nodes]
        x = 0
        for node in nodes:
            old_display = dict(node.display)
            node.create(x, 0)
            x += 350
            if old_display:
                node.display = old_display

        w = WorkflowDefinition.model_validate(
            dict(
                name=self.name,
                type=self.type,
                nodes=nodes,
                edges=[
                    Edge.model_validate(e.model_dump()) for e in self.definition.edges
                ],
            )
        )
        return w

    @property
    def inputs(self):
        return [n for n in self.definition.nodes if n.type == "InputNode"]

    @property
    def outputs(self):
        return [n for n in self.definition.nodes if n.type == "OutputNode"]

    def refresh(self) -> "Workflow":
        response = self.client.get(f"/v1/workflows/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    async def arefresh(self) -> "Workflow":
        response = await self.client.aget(f"/v1/workflows/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    def run(self, body: dict[str, Any]) -> Run:
        self.validate_body(body)
        response = self.client.post(f"/v1/workflows/{self.id}/runs", {"input": body})
        return Run(client=self.client, **response)

    async def arun(self, body: dict[str, Any]) -> Run:
        self.validate_body(body)
        response = await self.client.apost(
            f"/v1/workflows/{self.id}/runs", {"input": body}
        )
        return Run(client=self.client, **response)


class WorkflowService(BaseService[Workflow]):
    def list(self, page: int = 1, page_size: int = 10) -> List["Workflow"]:
        workflows_data = self.client.pget(
            f"/v1/workflows",
            params={"page": page, "page_size": page_size},
        )
        return [Workflow(client=self.client, **data) for data in workflows_data]

    async def alist(self, page: int = 1, page_size: int = 10) -> List["Workflow"]:
        workflows_data = await self.client.apget(
            f"/v1/workflows",
            params={"page": page, "page_size": page_size},
        )
        return [Workflow(client=self.client, **data) for data in workflows_data]

    def save(self, workflow: WorkflowDefinition):
        w = self.client.post(f"/v1/workflows", workflow.to_noxus())
        return Workflow(client=self.client, **w)

    def get(self, workflow_id: str) -> "Workflow":
        w = self.client.get(f"/v1/workflows/{workflow_id}")
        return Workflow(client=self.client, **w)

    async def aget(self, workflow_id: str) -> "Workflow":
        w = await self.client.aget(f"/v1/workflows/{workflow_id}")
        return Workflow(client=self.client, **w)

    def update(
        self, workflow_id: str, workflow: WorkflowDefinition, force: bool = False
    ) -> "Workflow":
        w = self.client.patch(
            f"/v1/workflows/{workflow_id}?force={force}", workflow.to_noxus()
        )
        return Workflow(client=self.client, **w)
