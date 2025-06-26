from typing import Any, TYPE_CHECKING
from noxus_sdk.workflows.workflow import WorkflowDefinition

if TYPE_CHECKING:
    from noxus_sdk.resources.conversations import Conversation


class AgentFlowDefinition(WorkflowDefinition):
    type: str = "agent_flow"

    def verify_name_legal(self, name):
        assert name not in [
            "InputNode",
            "OutputNode",
            "FileInputNode",
            "ImageInputNode",
        ]

    def update(self, force: bool = False):
        if not self.client:
            raise ValueError("Client not set")
        w = self.client.agentflows.update(self.id, self, force)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    async def aupdate(self, force: bool = False):
        if not self.client:
            raise ValueError("Client not set")
        w = await self.client.agentflows.aupdate(self.id, self, force)
        self.refresh_from_data(client=self.client, **w.model_dump())
        return w

    def save(self):
        if not self.client:
            raise ValueError("Client not set")
        return self.client.agentflows.save(self)

    async def asave(self):
        if not self.client:
            raise ValueError("Client not set")
        return await self.client.agentflows.asave(self)

    def run(self) -> "Conversation":  # type: ignore
        from noxus_sdk.resources.conversations import ConversationSettings

        if not self.client:
            raise ValueError("Client not set")
        return self.client.conversations.create(
            self.id,
            ConversationSettings(
                agent_flow_id=self.id,
                model_selection=[
                    "chat-balanced",
                    "gpt-4.1",
                    "claude-4-sonnet",
                    "claude-3.7-sonnet-thinking",
                    "claude-3.5-sonnet-v2",
                    "gemini-2.5-flash",
                    "gpt-4o",
                ],
                temperature=0.4,
                tools=[],
            ),
        )

    async def arun(self) -> "Conversation":  # type: ignore
        from noxus_sdk.resources.conversations import ConversationSettings

        if not self.client:
            raise ValueError("Client not set")
        return self.client.conversations.create(
            self.id,
            ConversationSettings(
                agent_flow_id=self.id,
                model_selection=[
                    "chat-balanced",
                    "gpt-4.1",
                    "claude-4-sonnet",
                    "claude-3.7-sonnet-thinking",
                    "claude-3.5-sonnet-v2",
                    "gemini-2.5-flash",
                    "gpt-4o",
                ],
                temperature=0.4,
                tools=[],
            ),
        )
