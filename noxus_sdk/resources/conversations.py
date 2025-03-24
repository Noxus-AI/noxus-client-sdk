from typing import List
from pydantic import BaseModel

from noxus_sdk.resources.base import BaseResource, BaseService


class ConversationTool(BaseModel):
    name: str
    description: str
    enabled: bool
    type: str


class ConversationSettings(BaseModel):
    model_selection: list[str]
    temperature: float
    max_tokens: int
    tools: list[ConversationTool]
    extra_instructions: str


class Conversation(BaseResource):
    id: str
    name: str
    created_at: str
    last_updated_at: str
    etag: str
    settings: ConversationSettings

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
            "/conversations", {"name": name, "settings": settings}
        )
        return Conversation.model_validate(result)

    def get(self, conversation_id: str) -> Conversation:
        result = self.client.get(f"/conversations/{conversation_id}")
        return Conversation.model_validate(result)

    def update(
        self, conversation_id: str, name: str, settings: ConversationSettings
    ) -> Conversation:
        result = self.client.patch(
            f"/conversations/{conversation_id}", {"name": name, "settings": settings}
        )
        return Conversation.model_validate(result)

    def delete(self, conversation_id: str) -> None:
        self.client.delete(f"/conversations/{conversation_id}")
