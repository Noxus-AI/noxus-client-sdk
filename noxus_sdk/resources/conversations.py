from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    Discriminator,
    Field,
    ValidationError,
    model_validator,
    ConfigDict,
)

from noxus_sdk.resources.base import BaseResource, BaseService


class ConversationTool(BaseModel):
    type: str
    name: str
    description: str
    enabled: bool = True
    extra_instructions: str | None = None


class WebResearchTool(ConversationTool):
    """Tool that allows the user to search the web for information"""

    type: Literal["web_research"] = "web_research"
    name: str = "Web Research"
    description: str = "Search the web for information"


class NoxusQaTool(ConversationTool):
    """Tool that allows the user to answer questions about the Noxus platform"""

    type: Literal["noxus_qa"] = "noxus_qa"
    name: str = "Noxus Q&A"
    description: str = "Answer questions about the Noxus platform"


class KnowledgeBaseSelectorTool(ConversationTool):
    """Tool that allows the user to select a knowledge base to answer questions about"""

    type: Literal["kb_selector"] = "kb_selector"
    name: str = "Select Knowledge Base Q&A"
    description: str = "Select a knowledge base to answer questions about"
    kb_id: str | None = None


class KnowledgeBaseQaTool(ConversationTool):
    """Tool that allows the user to answer questions about a specific pre-selected knowledge base"""

    type: Literal["kb_qa"] = "kb_qa"
    name: str = "Knowledge Base Q&A"
    description: str = "Answer questions about the knowledge base"
    kb_id: str | None = None


class WorkflowInfo(BaseModel):
    id: str
    name: str
    description: str | None = None


class WorkflowTool(ConversationTool):
    """Tool that allows the user to run a workflow"""

    type: Literal["workflow"] = "workflow"
    name: str = "Workflow Runner"
    description: str = "Run a workflow"
    workflow: WorkflowInfo


AnyToolSettings = Annotated[
    WebResearchTool
    | NoxusQaTool
    | KnowledgeBaseSelectorTool
    | KnowledgeBaseQaTool
    | WorkflowTool,
    Discriminator("type"),
]


class ConversationSettings(BaseModel):
    model_selection: list[str]
    temperature: float
    max_tokens: int | None = None
    tools: list[AnyToolSettings]
    extra_instructions: str | None = None


class ConversationFile(BaseModel):
    status: Literal["success"] = "success"
    name: str
    b64_content: str | None = None
    url: str | None = None
    id: str = Field(default_factory=lambda: str(uuid4()))
    size: int = 1
    type: str = ""

    @model_validator(mode="after")
    def validate_content_url(self):
        if self.b64_content is None and self.url is None:
            raise ValidationError("Either base64 content or url must be provided")
        return self


class MessageRequest(BaseModel):
    content: str
    tool: Literal["web_research", "kb_qa", "workflow"] | str | None = None
    kb_id: str | None = None
    workflow_id: str | None = None
    files: list[ConversationFile] | None = None
    model_selection: list[str] | None = None


class Message(BaseModel):
    id: UUID
    created_at: datetime
    message_parts: list[dict]


class Conversation(BaseResource):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    name: str
    created_at: str
    last_updated_at: str
    settings: ConversationSettings
    etag: str | None = None
    messages: list[Message] = []

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
        return [Message.model_validate(msg) for msg in response.messages]

    def get_messages(self) -> list[Message]:
        response = self.refresh()
        return [Message.model_validate(msg) for msg in response.messages]

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

        return Message.model_validate(self.messages[-1])


class ConversationService(BaseService[Conversation]):
    async def alist(self, page: int = 1, page_size: int = 10) -> list[Conversation]:
        conversations = await self.client.apget(
            "/v1/conversations", params={"page": page, "page_size": page_size}
        )
        return [
            Conversation(client=self.client, **conversation)
            for conversation in conversations
        ]

    def list(self, page: int = 1, page_size: int = 10) -> list[Conversation]:
        conversations = self.client.pget(
            "/v1/conversations", params={"page": page, "page_size": page_size}
        )
        return [
            Conversation(client=self.client, **conversation)
            for conversation in conversations
        ]

    def create(
        self,
        name: str,
        settings: ConversationSettings | None = None,
        agent_id: str | None = None,
    ) -> Conversation:
        if (settings is None and agent_id is None) or (
            settings is not None and agent_id is not None
        ):
            raise ValueError("Exactly one of settings or agent_id must be provided")

        params = {}
        if agent_id:
            params["assistant_id"] = agent_id

        # Match CreateConversation schema
        req = {"name": name, "settings": settings.model_dump() if settings else None}

        result = self.client.post(
            "/v1/conversations",
            body=req,
            params=params,
        )
        return Conversation(client=self.client, **result)

    async def acreate(
        self,
        name: str,
        settings: ConversationSettings | None = None,
        agent_id: str | None = None,
    ) -> Conversation:
        if (settings is None and agent_id is None) or (
            settings is not None and agent_id is not None
        ):
            raise ValueError("Exactly one of settings or agent_id must be provided")

        params = {}
        if agent_id:
            params["assistant_id"] = agent_id

        # Match CreateConversation schema
        req = {"name": name, "settings": settings.model_dump() if settings else None}

        result = await self.client.apost(
            "/v1/conversations",
            body=req,
            params=params,
        )
        return Conversation(client=self.client, **result)

    def get(self, conversation_id: str) -> Conversation:
        result = self.client.get(f"/v1/conversations/{conversation_id}")
        return Conversation(client=self.client, **result)

    async def aget(self, conversation_id: str) -> Conversation:
        result = await self.client.aget(f"/v1/conversations/{conversation_id}")
        return Conversation(client=self.client, **result)

    def update(
        self,
        conversation_id: str,
        name: str | None = None,
        settings: ConversationSettings | None = None,
    ) -> Conversation:
        result = self.client.patch(
            f"/v1/conversations/{conversation_id}",
            {"name": name, "settings": settings.model_dump() if settings else None},
        )
        return Conversation(client=self.client, **result)

    async def aupdate(
        self,
        conversation_id: str,
        name: str | None = None,
        settings: ConversationSettings | None = None,
    ) -> Conversation:
        result = await self.client.apatch(
            f"/v1/conversations/{conversation_id}",
            {"name": name, "settings": settings.model_dump() if settings else None},
        )
        return Conversation(client=self.client, **result)

    def delete(self, conversation_id: str) -> None:
        self.client.delete(f"/v1/conversations/{conversation_id}")

    async def adelete(self, conversation_id: str) -> None:
        await self.client.adelete(f"/v1/conversations/{conversation_id}")
