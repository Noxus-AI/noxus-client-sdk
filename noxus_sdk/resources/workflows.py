from noxus_sdk.resources.base import BaseService
from noxus_sdk.workflows import WorkflowDefinition


class WorkflowService(BaseService[WorkflowDefinition]):
    async def alist(
        self, page: int = 1, page_size: int = 10
    ) -> list[WorkflowDefinition]:
        workflows_data = await self.client.apget(
            f"/v1/workflows",
            params={"page": page, "page_size": page_size},
        )
        return [
            WorkflowDefinition.model_validate({"client": self.client, **data})
            for data in workflows_data
        ]

    def list(self, page: int = 1, page_size: int = 10) -> list[WorkflowDefinition]:
        workflows_data = self.client.pget(
            f"/v1/workflows",
            params={"page": page, "page_size": page_size},
        )
        return [
            WorkflowDefinition.model_validate({"client": self.client, **data})
            for data in workflows_data
        ]

    def delete(self, workflow_id: str):
        self.client.delete(f"/v1/workflows/{workflow_id}")

    async def adelete(self, workflow_id: str):
        await self.client.adelete(f"/v1/workflows/{workflow_id}")

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        w = self.client.post(f"/v1/workflows", workflow.to_noxus())
        workflow.refresh_from_data(**w)
        return WorkflowDefinition.model_validate({"client": self.client, **w})

    async def asave(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        w = await self.client.apost(f"/v1/workflows", workflow.to_noxus())
        workflow.refresh_from_data(**w)
        return WorkflowDefinition.model_validate({"client": self.client, **w})

    def get(self, workflow_id: str) -> WorkflowDefinition:
        w = self.client.get(f"/v1/workflows/{workflow_id}")
        return WorkflowDefinition.model_validate({"client": self.client, **w})

    async def aget(self, workflow_id: str) -> WorkflowDefinition:
        w = await self.client.aget(f"/v1/workflows/{workflow_id}")
        return WorkflowDefinition.model_validate({"client": self.client, **w})

    def update(
        self, workflow_id: str, workflow: WorkflowDefinition, force: bool = False
    ) -> WorkflowDefinition:
        w = self.client.patch(
            f"/v1/workflows/{workflow_id}?force={force}", workflow.to_noxus()
        )
        return WorkflowDefinition.model_validate({"client": self.client, **w})

    async def aupdate(
        self, workflow_id: str, workflow: WorkflowDefinition, force: bool = False
    ) -> WorkflowDefinition:
        w = await self.client.apatch(
            f"/v1/workflows/{workflow_id}?force={force}", workflow.to_noxus()
        )
        return WorkflowDefinition.model_validate({"client": self.client, **w})
