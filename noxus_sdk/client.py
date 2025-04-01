import os
import anyio
import httpx
import time
from typing import List, Any

from regex import W


class Requester:
    base_url = os.environ.get("NOXUS_BACKEND_URL", "https://backend.noxus.ai")

    def __init__(self, api_key: str, extra_headers: dict | None = None):
        self.api_key = api_key
        self.extra_headers = extra_headers

    async def arequest(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/{url}",
                headers=headers_,
                follow_redirects=True,
                json=json,
                params=params,
                timeout=timeout or httpx.USE_CLIENT_DEFAULT,
            )
            response.raise_for_status()
            return response.json()

    async def aget(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        return await self.arequest(
            "GET", url, headers=headers, params=params, timeout=timeout
        )

    async def apget(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        page: int = 1,
        page_size: int = 10,
        timeout: int | None = None,
    ):
        params_ = params or {}
        params_["page"] = page
        params_["page_size"] = page_size

        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        result = await self.arequest(
            "GET", url, headers=headers_, params=params_, timeout=timeout
        )
        if "items" not in result:
            return []
        return result["items"]

    async def apost(
        self,
        url: str,
        body: Any,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return await self.arequest(
            "POST", url, json=body, headers=headers, timeout=timeout
        )

    async def apatch(
        self,
        url: str,
        body: Any,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return await self.arequest(
            "PATCH", url, json=body, headers=headers, timeout=timeout
        )

    async def adelete(
        self,
        url: str,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return await self.arequest("DELETE", url, headers=headers, timeout=timeout)

    def request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        response = httpx.request(
            method,
            f"{self.base_url}{url}",
            headers=headers_,
            follow_redirects=True,
            json=json,
            params=params,
            timeout=timeout or 10,
        )
        response.raise_for_status()
        return response.json()

    def get(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        return self.request("GET", url, headers=headers, params=params, timeout=timeout)

    def pget(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        page: int = 1,
        page_size: int = 10,
        timeout: int | None = None,
    ):
        params_ = params or {}
        params_["page"] = page
        params_["page_size"] = page_size
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        result = self.request(
            "GET", url, headers=headers_, params=params_, timeout=timeout
        )
        if "items" not in result:
            return []
        return result["items"]

    def patch(
        self,
        url: str,
        body: Any,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return self.request("PATCH", url, json=body, headers=headers, timeout=timeout)

    def post(
        self,
        url: str,
        body: Any,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return self.request("POST", url, json=body, headers=headers, timeout=timeout)

    def delete(
        self,
        url: str,
        headers: dict | None = None,
        timeout: int | None = None,
    ):
        return self.request("DELETE", url, headers=headers, timeout=timeout)


class Client(Requester):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://backend.noxus.ai",
        load_nodes: bool = True,
        extra_headers: dict | None = None,
    ):
        from noxus_sdk.workflows import load_node_types
        from noxus_sdk.resources.workflows import WorkflowService
        from noxus_sdk.resources.assistants import AgentService
        from noxus_sdk.resources.conversations import ConversationService
        from noxus_sdk.resources.knowledge_bases import KnowledgeBaseService

        self.api_key = api_key
        self.base_url = os.environ.get("NOXUS_BACKEND_URL", base_url)
        self.extra_headers = extra_headers

        if load_nodes:
            self.nodes = self.get_nodes()
            load_node_types(self.nodes)
        else:
            self.nodes = []

        self.workflows = WorkflowService(self)
        self.agents = AgentService(self)
        self.conversations = ConversationService(self)
        self.knowledge_bases = KnowledgeBaseService(self)

    def get_nodes(self) -> List[dict]:
        return self.get("/nodes")

    async def async_get_nodes(self) -> List[dict]:
        return await self.aget("/nodes")
