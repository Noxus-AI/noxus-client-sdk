import os
import anyio
import httpx
import time
from typing import List, Any


class Requester:
    base_url = os.environ.get("NOXUS_BACKEND_URL", "https://backend.noxus.ai")

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def arequest(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
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
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def aget(
        self, url: str, headers: dict | None = None, params: dict | None = None
    ):
        return await self.arequest("GET", url, headers=headers, params=params)

    async def apget(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        params_ = params or {}
        params_["page"] = page
        params_["page_size"] = page_size
        result = await self.arequest("GET", url, headers=headers, params=params_)
        if "items" not in result:
            return []
        return result["items"]

    async def apost(self, url: str, body: Any, headers: dict | None = None):
        return await self.arequest("POST", url, json=body, headers=headers)

    async def apatch(self, url: str, body: Any, headers: dict | None = None):
        return await self.arequest("PATCH", url, json=body, headers=headers)

    async def adelete(self, url: str, headers: dict | None = None):
        return await self.arequest("DELETE", url, headers=headers)

    def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        response = httpx.request(
            method,
            f"{self.base_url}{url}",
            headers=headers_,
            follow_redirects=True,
            json=json,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get(self, url: str, headers: dict | None = None, params: dict | None = None):
        return self.request("GET", url, headers=headers, params=params)

    def pget(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        params_ = params or {}
        params_["page"] = page
        params_["page_size"] = page_size
        result = self.request("GET", url, headers=headers, params=params_)
        if "items" not in result:
            return []
        return result["items"]

    def patch(self, url: str, body: Any, headers: dict | None = None):
        return self.request("PATCH", url, json=body, headers=headers)

    def post(self, url: str, body: Any, headers: dict | None = None):
        return self.request("POST", url, json=body, headers=headers)

    def delete(self, url: str, headers: dict | None = None):
        return self.request("DELETE", url, headers=headers)


class Client(Requester):
    def __init__(self, api_key: str, base_url: str = "https://backend.noxus.ai"):
        from noxus_sdk.workflows import load_node_types
        from noxus_sdk.resources.workflows import WorkflowService
        from noxus_sdk.resources.assistants import AgentService
        from noxus_sdk.resources.conversations import ConversationService
        from noxus_sdk.resources.knowledge_bases import KnowledgeBaseService

        self.api_key = api_key
        self.base_url = os.environ.get("NOXUS_BACKEND_URL", base_url)
        self.nodes = self.get_nodes()

        load_node_types(self.nodes)

        self.workflows = WorkflowService(self)
        self.agents = AgentService(self)
        self.conversations = ConversationService(self)
        self.knowledge_bases = KnowledgeBaseService(self)

    def get_nodes(self) -> List[dict]:
        return self.get("/nodes")

    async def async_get_nodes(self) -> List[dict]:
        return await self.aget("/nodes")
