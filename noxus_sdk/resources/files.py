from uuid import UUID
from enum import Enum
from pydantic import ConfigDict, BaseModel
from datetime import datetime

from noxus_sdk.resources.base import BaseService
from typing import BinaryIO


class SourceType(str, Enum):
    Document = "Document"
    GoogleDrive = "Google Drive"
    Notion = "Notion"
    Website = "Website"
    OneDrive = "OneDrive"
    Slack = "Slack"
    Linear = "Linear"
    Github = "Github"
    Teams = "Teams"
    Sharepoint = "Sharepoint"
    Custom = "Custom"

    @classmethod
    def get_by_value(cls, value) -> "SourceType":
        # Get enum member by value
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No enum member with value {value} in {cls}")


class File(BaseModel):
    id: UUID
    uri: str
    size: float
    group_id: UUID | None = None

    filename: str
    content_type: str
    source_type: SourceType
    source_metadata: dict | None

    created_at: datetime | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class FileService(BaseService[File]):
    def save(self, fd: BinaryIO) -> File:
        w = self.client.post(f"/v1/file", files={"file": fd})
        return File.model_validate(w)

    async def asave(self, fd: BinaryIO) -> File:
        w = await self.client.apost(f"/v1/file", files={"file": fd})
        return File.model_validate(w)

    def get(self, file_id: str) -> bytes:
        w = self.client._request("GET", f"/v1/file/{file_id}")  # noqa
        return w.content

    async def aget(self, file_id: str) -> bytes:
        w = await self.client._arequest("GET", f"/v1/file/{file_id}")  # noqa
        return w.content
