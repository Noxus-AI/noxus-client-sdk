from typing import TypeAlias

from noxus_sdk.resources.base import BaseResource, BaseService
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    WorkflowTool,
    WorkflowInfo,
    KnowledgeBaseQaTool,
    KnowledgeBaseSelectorTool,
    NoxusQaTool,
    WebResearchTool,
    KnowledgeBaseInfo,
)
from pydantic import ConfigDict

AgentSettings: TypeAlias = ConversationSettings


class Agent(BaseResource):
    id: str
    name: str
    definition: AgentSettings
    model_config = ConfigDict(validate_assignment=True, extra="allow")

    def update(self, name: str, settings: AgentSettings) -> "Agent":
        result = self.client.patch(
            f"/v1/agents/{self.id}",
            {"name": name, "definition": settings.model_dump()},
        )
        for key, value in result.items():
            setattr(self, key, value)
        return self

    def delete(self) -> None:
        self.client.delete(f"/v1/agents/{self.id}")


class AgentService(BaseService[Agent]):
    async def alist(self) -> list[Agent]:
        results = await self.client.apget("/v1/agents")
        return [Agent(client=self.client, **result) for result in results]

    def list(self) -> list[Agent]:
        results = self.client.pget("/v1/agents")
        return [Agent(client=self.client, **result) for result in results]

    def create(self, name: str, settings: AgentSettings) -> Agent:
        result = self.client.post(
            "/v1/agents", {"name": name, "definition": settings.model_dump()}
        )
        return Agent(client=self.client, **result)

    async def acreate(self, name: str, settings: AgentSettings) -> Agent:
        result = await self.client.apost(
            "/v1/agents", {"name": name, "definition": settings.model_dump()}
        )
        return Agent(client=self.client, **result)

    def get(self, agent_id: str) -> Agent:
        result = self.client.get(f"/v1/agents/{agent_id}")
        return Agent(client=self.client, **result)

    async def aget(self, agent_id: str) -> Agent:
        result = await self.client.aget(f"/v1/agents/{agent_id}")
        return Agent(client=self.client, **result)

    def update(self, agent_id: str, name: str, settings: AgentSettings) -> Agent:
        result = self.client.patch(
            f"/v1/agents/{agent_id}",
            {"name": name, "definition": settings.model_dump()},
        )
        return Agent(client=self.client, **result)

    async def aupdate(self, agent_id: str, name: str, settings: AgentSettings) -> Agent:
        result = await self.client.apatch(
            f"/v1/agents/{agent_id}",
            {"name": name, "definition": settings.model_dump()},
        )
        return Agent(client=self.client, **result)

    def delete(self, agent_id: str) -> None:
        self.client.delete(f"/v1/agents/{agent_id}")

    async def adelete(self, agent_id: str) -> None:
        await self.client.adelete(f"/v1/agents/{agent_id}")
