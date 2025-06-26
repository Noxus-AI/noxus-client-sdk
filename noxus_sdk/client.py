import asyncio
import os
import time
from typing import Any, BinaryIO, TYPE_CHECKING

import httpx
from httpx_sse import ServerSentEvent, connect_sse, aconnect_sse

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

FileContent = BinaryIO | bytes | str
HttpxFile = tuple[str, tuple[str, FileContent, str | None]]
RequestFiles = dict[str, Any] | list[HttpxFile] | None


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
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        ratelimited = True
        while ratelimited:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{url}",
                    headers=headers_,
                    follow_redirects=True,
                    json=json,
                    files=files,
                    params=params,
                    timeout=timeout or httpx.USE_CLIENT_DEFAULT,
                )
                if response.status_code == 429:
                    await asyncio.sleep(1)
                    continue
                ratelimited = False
                response.raise_for_status()
                return response.json()
        raise Exception("Request failed")

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
        params_["page"] = params_.get("page", page)
        params_["size"] = params_.get("page_size", page_size)

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
        body: Any | None = None,
        headers: dict | None = None,
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        return await self.arequest(
            "POST",
            url,
            json=body,
            headers=headers,
            files=files,
            params=params,
            timeout=timeout,
        )

    async def apatch(
        self,
        url: str,
        body: Any,
        headers: dict | None = None,
        timeout: int | None = None,
        params: dict | None = None,
    ):
        return await self.arequest(
            "PATCH", url, json=body, headers=headers, timeout=timeout, params=params
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
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        ratelimited = True
        while ratelimited:
            response = httpx.request(
                method,
                f"{self.base_url}{url}",
                headers=headers_,
                follow_redirects=True,
                json=json,
                files=files,
                params=params,
                timeout=timeout or 30,
            )
            if response.status_code == 429:
                time.sleep(1)
                continue
            ratelimited = False
            response.raise_for_status()
            return response.json()
        raise Exception("Request failed")

    def event_stream(
        self,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ) -> "Iterator[ServerSentEvent]":
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        ratelimited = True
        with httpx.Client() as client:
            while ratelimited:
                with connect_sse(
                    client=client,
                    method="GET",
                    url=f"{self.base_url}{url}",
                    headers=headers_,
                    follow_redirects=True,
                    json=json,
                    files=files,
                    params=params,
                    timeout=timeout or 30,
                ) as response:
                    yield from response.iter_sse()
        raise Exception("Request failed")

    async def aevent_stream(
        self,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ) -> "AsyncIterator[ServerSentEvent]":
        headers_ = {"X-API-Key": self.api_key}
        if headers:
            headers_.update(headers)
        if self.extra_headers:
            headers_.update(self.extra_headers)
        ratelimited = True
        async with httpx.AsyncClient() as client:
            while ratelimited:
                async with aconnect_sse(
                    client=client,
                    method="GET",
                    url=f"{self.base_url}{url}",
                    headers=headers_,
                    follow_redirects=True,
                    json=json,
                    files=files,
                    params=params,
                    timeout=timeout or 30,
                ) as response:
                    async for event in response.aiter_sse():
                        yield event
        raise Exception("Request failed")

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
        params_["page"] = params_.get("page", page)
        params_["size"] = params_.get("page_size", page_size)

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
        params: dict | None = None,
    ):
        return self.request(
            "PATCH", url, json=body, headers=headers, timeout=timeout, params=params
        )

    def post(
        self,
        url: str,
        body: Any | None = None,
        headers: dict | None = None,
        files: RequestFiles = None,
        params: dict | None = None,
        timeout: int | None = None,
    ):
        return self.request(
            "POST",
            url,
            json=body,
            headers=headers,
            files=files,
            params=params,
            timeout=timeout,
        )

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
        load_me: bool = True,
        extra_headers: dict | None = None,
    ):
        from noxus_sdk.resources.admin import AdminService
        from noxus_sdk.resources.assistants import AgentService
        from noxus_sdk.resources.conversations import ConversationService
        from noxus_sdk.resources.knowledge_bases import KnowledgeBaseService
        from noxus_sdk.resources.runs import RunService
        from noxus_sdk.resources.workflows import WorkflowService
        from noxus_sdk.resources.agentflows import AgentFlowService
        from noxus_sdk.workflows import load_node_types

        self.api_key = api_key
        self.base_url = os.environ.get("NOXUS_BACKEND_URL", base_url)
        self.extra_headers = extra_headers

        if load_nodes:
            self.nodes = self.get_nodes()
            load_node_types(self.nodes)
        else:
            self.nodes = []

        self.workflows = WorkflowService(self)
        self.agentflows = AgentFlowService(self)
        self.agents = AgentService(self)
        self.conversations = ConversationService(self)
        self.knowledge_bases = KnowledgeBaseService(self)
        self.runs = RunService(self)
        self.admin = AdminService(self, enabled=bool(not load_me))
        if load_me:
            self.admin.enabled = self.admin.get_me().tenant_admin

    def get_nodes(self) -> list[dict]:
        return self.get("/v1/nodes")

    async def aget_nodes(self) -> list[dict]:
        return await self.aget("/v1/nodes")

    def get_models(self) -> list[dict]:
        return self.get("/v1/models/llms")

    async def aget_models(self) -> list[dict]:
        return await self.aget("/v1/models/llms")

    def get_chat_presets(self) -> list[dict]:
        return self.get("/v1/models/llms/presets")

    async def aget_chat_presets(self) -> list[dict]:
        return await self.aget("/v1/models/llms/presets")
