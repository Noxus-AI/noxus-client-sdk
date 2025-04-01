from pydantic import BaseModel

from noxus_sdk.resources.base import BaseResource, BaseService


class AgentTool(BaseModel):
    name: str
    description: str
    definition: dict
    enabled: bool
    type: str


class AgentSettings(BaseModel):
    model_selection: list[str]
    temperature: float
    max_tokens: int
    tools: list[AgentTool]
    extra_instructions: str


class Agent(BaseResource):
    id: str
    name: str
    created_at: str
    last_updated_at: str
    etag: str
    settings: AgentSettings

    def update(self, name: str, settings: AgentSettings) -> "Agent":
        result = self.client.patch(
            f"/v1/agents/{self.id}",
            {"name": name, "settings": settings},
        )
        return Agent(client=self.client, **result)

    def delete(self) -> None:
        self.client.delete(f"/v1/agents/{self.id}")


class AgentService(BaseService[Agent]):
    def list(self) -> list[Agent]:
        results = self.client.get("/v1/agents")
        return [Agent(client=self.client, **result) for result in results]

    def create(self, name: str, settings: AgentSettings) -> Agent:
        result = self.client.post("/v1/agents", {"name": name, "settings": settings})
        return Agent(client=self.client, **result)

    def get(self, agent_id: str) -> Agent:
        result = self.client.get(f"/v1/agents/{agent_id}")
        return Agent(client=self.client, **result)

    def update(self, agent_id: str, name: str, settings: AgentSettings) -> Agent:
        result = self.client.patch(
            f"/v1/agents/{agent_id}", {"name": name, "settings": settings}
        )
        return Agent(client=self.client, **result)

    def delete(self, agent_id: str) -> None:
        self.client.delete(f"/v1/agents/{agent_id}")
