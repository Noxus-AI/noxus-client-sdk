from uuid import UUID
from datetime import datetime
from typing import Annotated, List, Literal
from pydantic import BaseModel, Discriminator

from noxus_sdk.resources.base import BaseResource, BaseService


class ConversationTool(BaseModel):
    type: str
    name: str
    description: str
    enabled: bool = True
    extra_instructions: str | None = None


class WebResearchSettings(ConversationTool):
    """Tool that allows the user to search the web for information"""

    type: Literal["web_research"] = "web_research"
    name: str = "Web Research"
    description: str = "Search the web for information"


class NoxusQaSettings(ConversationTool):
    """Tool that allows the user to answer questions about the Noxus platform"""

    type: Literal["noxus_qa"] = "noxus_qa"
    name: str = "Noxus Q&A"
    description: str = "Answer questions about the Noxus platform"


class KnowledgeBaseSelectorSettings(ConversationTool):
    """Tool that allows the user to select a knowledge base to answer questions about"""

    type: Literal["kb_selector"] = "kb_selector"
    name: str = "Select Knowledge Base Q&A"
    description: str = "Select a knowledge base to answer questions about"
    kb_id: UUID | None = None


class KnowledgeBaseQaSettings(ConversationTool):
    """Tool that allows the user to answer questions about a specific pre-selected knowledge base"""

    type: Literal["kb_qa"] = "kb_qa"
    name: str = "Knowledge Base Q&A"
    description: str = "Answer questions about the knowledge base"
    kb_id: UUID | None = None


class WorkflowSettings(ConversationTool):
    """Tool that allows the user to run a workflow"""

    type: Literal["workflow"] = "workflow"
    name: str = "Workflow Runner"
    description: str = "Run a workflow"
    workflow_id: UUID


AnyToolSettings = Annotated[
    WebResearchSettings
    | NoxusQaSettings
    | KnowledgeBaseSelectorSettings
    | KnowledgeBaseQaSettings
    | WorkflowSettings,
    Discriminator("type"),
]


class ConversationSettings(BaseModel):
    model_selection: list[str]
    temperature: float
    max_tokens: int | None = None
    tools: list[AnyToolSettings]
    extra_instructions: str | None = None


class ConversationFile(BaseModel):
    status: Literal["sucess"] = "sucess"
    name: str
    url: str


class MessageRequest(BaseModel):
    content: str
    tool: Literal["web_research", "kb_qa"] | str | None = None
    kb_id: str | None = None
    files: list[ConversationFile] | None = None
    model_selection: list[str] | None = None


class Message(BaseModel):
    id: UUID
    created_at: datetime
    message_parts: list[dict]


class Conversation(BaseResource):
    id: str
    name: str
    created_at: str
    last_updated_at: str
    settings: ConversationSettings
    etag: str | None = None
    messages: list[Message]

    def refresh(self) -> "Conversation":
        response = self.client.get(f"/v1/conversations/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    async def arefresh(self) -> "Conversation":
        response = await self.client.aget(f"/v1/conversations/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    async def aget_messages(self) -> list[Message]:
        response = await self.arefresh()
        return response.messages

    def get_messages(self) -> list[Message]:
        response = self.refresh()
        return response.messages

    async def aadd_message(self, message: MessageRequest) -> "Conversation":
        response = await self.client.apost(
            f"/v1/conversations/{self.id}",
            body=message.model_dump(),
            timeout=30,
        )
        for key, value in response.items():
            setattr(self, key, value)
        return self

    def add_message(self, message: MessageRequest) -> "Message":
        response = self.client.post(
            f"/v1/conversations/{self.id}",
            body=message.model_dump(),
            timeout=30,
        )
        for key, value in response.items():
            setattr(self, key, value)

        if len(self.messages) == 0:
            raise ValueError("No response from the server")

        return self.messages[-1]


class ConversationService(BaseService[Conversation]):
    def list(self, page: int = 1, page_size: int = 10) -> list[Conversation]:
        conversations = self.client.pget(
            "/v1/conversations", params={"page": page, "page_size": page_size}
        )
        return [
            Conversation(client=self.client, **conversation)
            for conversation in conversations
        ]

    async def alist(self, page: int = 1, page_size: int = 10) -> List[Conversation]:
        conversations = await self.client.apget(
            "/v1/conversations", params={"page": page, "page_size": page_size}
        )
        return [
            Conversation(client=self.client, **conversation)
            for conversation in conversations
        ]

    def create(self, name: str, settings: ConversationSettings) -> Conversation:
        result = self.client.post(
            "/v1/conversations", {"name": name, "settings": settings.model_dump()}
        )
        return Conversation(client=self.client, **result)

    async def acreate(self, name: str, settings: ConversationSettings) -> Conversation:
        result = await self.client.apost(
            "/v1/conversations", {"name": name, "settings": settings.model_dump()}
        )
        return Conversation(client=self.client, **result)

    def get(self, conversation_id: str) -> Conversation:
        result = self.client.get(f"/v1/conversations/{conversation_id}")
        return Conversation(client=self.client, **result)

    async def aget(self, conversation_id: str) -> Conversation:
        result = await self.client.aget(f"/v1/conversations/{conversation_id}")
        return Conversation(client=self.client, **result)

    def update(
        self, conversation_id: str, name: str, settings: ConversationSettings
    ) -> Conversation:
        result = self.client.patch(
            f"/conversations/{conversation_id}", {"name": name, "settings": settings}
        )
        return Conversation(client=self.client, **result)

    async def aupdate(
        self, conversation_id: str, name: str, settings: ConversationSettings
    ) -> Conversation:
        result = await self.client.apatch(
            f"/v1/conversations/{conversation_id}",
            {"name": name, "settings": settings.model_dump()},
        )
        return Conversation(client=self.client, **result)

    def delete(self, conversation_id: str) -> None:
        self.client.delete(f"/conversations/{conversation_id}")

    async def adelete(self, conversation_id: str) -> None:
        await self.client.adelete(f"/v1/conversations/{conversation_id}")
