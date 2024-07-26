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
            f"{self.base_url}/{url}",
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

    def run(self, body) -> "Run":
        validate_body(self.data, body)
        response = self.post(f"/v1/workflows/{self.data.id}/run", body)
        response.raise_for_status()
        return Run(self.api_key, response.json())

    async def async_run(self, body) -> "Run":
        validate_body(self.data, body)
        response = await self.apost(f"/v1/workflows/{self.data.id}/run", body)
        response.raise_for_status()
        return Run(self.api_key, response.json())


class Run(Requester):
    def __init__(self, api_key: str, data: Any):
        self.api_key = api_key
        self.data = data

    def wait(self):
        while self.get_progress() < 100:
            time.sleep(1)

    def get_progress(self):
        response = self.get(f"{self.data['url']}/progress")
        response.raise_for_status()
        return response.json()["progress"]

    async def async_wait(self):
        while await self.get_progress() < 100:
            await anyio.sleep(1)

    async def async_get_progress(self):
        response = await self.aget(f"{self.data['url']}/progress")
        response.raise_for_status()
        return response.json()["progress"]
