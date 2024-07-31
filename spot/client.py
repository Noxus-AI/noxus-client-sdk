import anyio
import httpx
import time
from typing import List, Any
from .models import validate_body, Workflow as WorkflowModel


class Requester:
    base_url = "https://app.getspot.io/api/backend"

    async def arequest(
        self, method: str, url: str, headers: dict = None, json: dict = None
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{url}",
                headers=headers_,
                follow_redirects=True,
                json=json,
            )
            response.raise_for_status()
            return response.json()

    async def aget(self, url: str, headers: dict = None):
        return await self.arequest("GET", url, headers)

    async def apost(self, url: str, body: Any, headers: dict = None):
        return await self.arequest("POST", url, json=body, headers=headers)

    def request(self, method: str, url: str, headers: dict = None, json: dict = None):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        response = httpx.request(
            method,
            f"{self.base_url}{url}",
            headers=headers_,
            follow_redirects=True,
            json=json,
        )
        response.raise_for_status()
        return response.json()

    def get(self, url: str, headers: dict = None):
        return self.request("GET", url, headers)

    def post(self, url: str, body: Any, headers: dict = None):
        return self.request("POST", url, json=body, headers=headers)


class Client(Requester):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def list_workflows(self) -> List["Workflow"]:
        workflows_data = self.get(
            f"/v1/workflows",
        )["items"]
        # todo pagination
        return [
            Workflow(self.api_key, WorkflowModel.model_validate(data))
            for data in workflows_data
        ]

    async def async_list_workflows(self) -> List["Workflow"]:
        workflows_data = await self.aget(
            f"/v1/workflows",
        )["items"]
        # todo pagination
        return [
            Workflow(self.api_key, WorkflowModel.model_validate(data))
            for data in workflows_data
        ]


class Workflow(Requester):
    def __init__(self, api_key: str, data: Any):
        self.api_key = api_key
        self.data = data

    @property
    def inputs(self):
        return [n for n in self.data.definition.nodes if n.type == "InputNode"]

    @property
    def outputs(self):
        return [n for n in self.data.definition.nodes if n.type == "OutputNode"]

    def run(self, body) -> "Run":
        validate_body(self.data, body)
        response = self.post(f"/v1/workflows/{self.data.id}/run", {"input": body})
        return Run(self.api_key, self.data.id, response)

    async def async_run(self, body) -> "Run":
        validate_body(self.data, body)
        response = await self.apost(
            f"/v1/workflows/{self.data.id}/run", {"input": body}
        )
        return Run(self.api_key, self.data.id, response)


class RunFailure(Exception):
    pass


class Run(Requester):
    def __init__(self, api_key: str, workflow_id: str, data: Any):
        self.api_key = api_key
        self.workflow_id = workflow_id
        self.data = data

    def wait(self):
        while self.get_status() not in ["failed", "completed"]:
            time.sleep(5)
        run_status = self.get_run()
        if run_status["status"] == "failed":
            raise RunFailure(run_status)
        return run_status["output"]

    def get_run(self):
        response = self.get(f"/v1/workflows/{self.workflow_id}/run/{self.data['id']}")
        return response

    def get_status(self):
        return self.get_run()["status"]

    async def async_wait(self):
        while await self.get_status() not in ["failed", "completed"]:
            await anyio.sleep(5)
        run_status = await self.async_get_run()
        if run_status["status"] == "failed":
            raise RunFailure(run_status)
        return run_status["output"]

    async def async_get_run(self):
        response = await self.aget(
            f"/v1/workflows/{self.workflow_id}/run/{self.data['id']}"
        )
        return response

    async def async_get_status(self):
        return await self.async_get_run()["status"]
