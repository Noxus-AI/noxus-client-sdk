from typing import TypeAlias

from pydantic import ConfigDict

from noxus_sdk.resources.base import BaseResource, BaseService
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    KnowledgeBaseQaTool,
    KnowledgeBaseSelectorTool,
    NoxusQaTool,
    WebResearchTool,
    WorkflowTool,
)

AgentSettings: TypeAlias = ConversationSettings


class Agent(BaseResource):
    id: str
    name: str
    definition: AgentSettings
    draft_definition: AgentSettings | None = None
    model_config = ConfigDict(validate_assignment=True, extra="allow")

    def update(
        self, name: str, settings: AgentSettings, preview: bool = False
    ) -> "Agent":
        result = self.client.patch(
            f"/v1/agents/{self.id}",
            {"name": name, "definition": settings.model_dump()},
            params={"preview": preview},
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

    def update(
        self, agent_id: str, name: str, settings: AgentSettings, preview: bool = False
    ) -> Agent:
        result = self.client.patch(
            f"/v1/agents/{agent_id}",
            {"name": name, "definition": settings.model_dump()},
            params={"preview": preview},
        )
        return Agent(client=self.client, **result)

    async def aupdate(
        self, agent_id: str, name: str, settings: AgentSettings, preview: bool = False
    ) -> Agent:
        result = await self.client.apatch(
            f"/v1/agents/{agent_id}",
            {"name": name, "definition": settings.model_dump()},
            params={"preview": preview},
        )
        return Agent(client=self.client, **result)

    def delete(self, agent_id: str) -> None:
        self.client.delete(f"/v1/agents/{agent_id}")

    async def adelete(self, agent_id: str) -> None:
        await self.client.adelete(f"/v1/agents/{agent_id}")
