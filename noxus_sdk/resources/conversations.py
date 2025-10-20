from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Annotated, Any, Literal, TYPE_CHECKING

from uuid import UUID, uuid4

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    ValidationError,
    model_validator,
)

from noxus_sdk.resources.base import BaseResource, BaseService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator


class ConversationTool(BaseModel):
    type: str
    enabled: bool = True
    extra_instructions: str | None = None


class WebResearchTool(ConversationTool):
    """Tool that allows the user to search the web for information"""

    type: Literal["web_research"] = "web_research"


class NoxusQaTool(ConversationTool):
    """Tool that allows the user to answer questions about the Noxus platform"""

    type: Literal["noxus_qa"] = "noxus_qa"


class AttachFileTool(ConversationTool):
    """Tool that allows attaching files to a conversation"""

    type: Literal["attach_file"] = "attach_file"


class KnowledgeBaseSelectorTool(ConversationTool):
    """Tool that allows the user to select a knowledge base to answer questions about"""

    type: Literal["kb_selector"] = "kb_selector"


class KnowledgeBaseQaTool(ConversationTool):
    """Tool that allows the user to answer questions about a specific pre-selected knowledge base"""

    type: Literal["kb_qa"] = "kb_qa"
    kb_id: str


class HumanInTheLoopTool(ConversationTool):
    """Tool that allows the agent to escalate to human"""

    type: Literal["human_in_the_loop"] = "human_in_the_loop"


class WorkflowTool(ConversationTool):
    """Tool that allows the user to run a workflow"""

    type: Literal["workflow"] = "workflow"
    workflow_id: str


AnyToolSettings = Annotated[
    WebResearchTool
    | NoxusQaTool
    | KnowledgeBaseSelectorTool
    | KnowledgeBaseQaTool
    | WorkflowTool
    | HumanInTheLoopTool
    | AttachFileTool,
    Discriminator("type"),
]


class ConversationSettings(BaseModel):
    model: list[str] = Field(validation_alias=AliasChoices("model", "model_selection"))
    temperature: float
    max_tokens: int = 64000
    tools: list[AnyToolSettings]
    extra_instructions: str | None = None
    agent_flow_id: str | None = None

    @model_validator(mode="before")
    def validate_extra_instructions(self, data: Any) -> Any:
        if data.get("extra_instructions") is not None and isinstance(
            data.get("extra_instructions"), dict
        ):
            data["extra_instructions"] = data.get("extra_instructions", {}).get("text")
        return data


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
    status: str
    agent_id: str | None = Field(
        default=None, validation_alias=AliasChoices("assistant_id", "agent_id")
    )

    def _update_w_response(self, response: dict) -> None:
        for key, value in response.items():
            if key == "assistant_id":
                key = "agent_id"  # noqa: PLW2901
            if hasattr(self, key):
                setattr(self, key, value)

    def refresh(self) -> Conversation:
        response = self.client.get(f"/v1/conversations/{self.id}")
        self._update_w_response(response)
        return self

    async def arefresh(self) -> Conversation:
        response = await self.client.aget(f"/v1/conversations/{self.id}")
        self._update_w_response(response)
        return self

    async def aget_messages(self) -> list[Message]:
        response = await self.arefresh()
        return [Message.model_validate(msg) for msg in response.messages]

    def get_messages(self) -> list[Message]:
        response = self.refresh()
        return [Message.model_validate(msg) for msg in response.messages]

    async def aadd_message(self, message: MessageRequest) -> Conversation:
        response = await self.client.apost(
            f"/v1/conversations/{self.id}",
            body=message.model_dump(),
            timeout=30,
        )
        self._update_w_response(response)
        return self

    def iter_messages(self) -> Iterator[MessageEvent]:
        resp = self.client.event_stream(
            f"/v1/conversations/{self.id}/events"
            + ("?etag=" + self.etag if self.etag else "")
        )
        for event in resp:
            message = MessageEvent.model_validate_json(event.data)
            if message.role == "user":
                continue
            if message.type == "conversation_end":
                yield message
                break
            yield message
            self.refresh()

    async def aiter_messages(self) -> AsyncIterator[MessageEvent]:
        resp = self.client.aevent_stream(
            f"/v1/conversations/{self.id}/events"
            + ("?etag=" + self.etag if self.etag else "")
        )
        async for event in resp:
            message = MessageEvent.model_validate_json(event.data)
            if message.role == "user":
                continue
            if message.type == "conversation_end":
                yield message
                break
            yield message
            await self.arefresh()

    def add_message(self, message: MessageRequest) -> Message:
        response = self.client.post(
            f"/v1/conversations/{self.id}",
            body=message.model_dump(),
            timeout=30,
        )
        self._update_w_response(response)

        if len(self.messages) == 0:
            raise ValueError("No response from the server")

        return Message.model_validate(self.messages[-1])


class MessageEvent(BaseModel):
    role: str
    type: str
    content: str | None = None


class ConversationService(BaseService[Conversation]):
    async def alist(self, page: int = 1, page_size: int = 10) -> list[Conversation]:
        conversations = await self.client.apget(
            "/v1/conversations",
            params={"page": page, "page_size": page_size},
            page=page,
            page_size=page_size,
        )
        return [
            Conversation(client=self.client, **conversation)
            for conversation in conversations
        ]

    def list(self, page: int = 1, page_size: int = 10) -> list[Conversation]:
        conversations = self.client.pget(
            "/v1/conversations",
            params={"page": page, "page_size": page_size},
            page=page,
            page_size=page_size,
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
