import json
import io

from pydantic import BaseModel
from typing import List, Literal, Optional, Any, Union
from noxus_sdk.resources.base import BaseResource, BaseService
from noxus_sdk.resources.runs import Run
from typing_extensions import TypeAlias
from pathlib import Path
from noxus_sdk.client import HttpxFile


RunStatus = Literal["queued", "running", "failed", "completed", "stopped"]
DocumentStatus = Literal["trained", "training", "error", "uploaded", "folder"]

SourceType = Literal[
    "document", "google_drive", "onedrive", "sharepoint", "website", "custom"
]

RunID: TypeAlias = str


class File(BaseModel):
    name: str
    size: int
    content_type: str
    source_type: str
    uri: str


class GoogleFile(BaseModel):
    id: str
    name: str
    mime_type: str
    size: int


class OneDriveFile(BaseModel):
    id: str
    name: str
    size: int
    web_url: str


class WebsiteWithDepth(BaseModel):
    url: str
    depth: int = 1


# Base document source config
class BaseDocumentSourceConfig(BaseModel):
    pass


# Regular document source config
class SpotFileConfig(BaseDocumentSourceConfig):
    files: List[File]


# Upload document source config
class UploadFileConfig(BaseDocumentSourceConfig):
    name: str
    content: bytes
    content_type: str


# Document source with discriminated union
class DocumentSourceConfig(BaseModel):
    files: List[File]


class DocumentSource(BaseModel):
    config: DocumentSourceConfig
    source_type: Literal["document"] = "document"
    subtype: str | None = None


class Source(BaseModel):
    source: DocumentSource


class KnowledgeBaseIngestion(BaseModel):
    batch_size: int
    default_chunk_size: int
    default_chunk_overlap: int
    enrich_chunks_mode: Literal["inject_summary", "contextual"] = "contextual"
    enrich_pre_made_qa: bool


class KnowledgeBaseRetrieval(BaseModel):
    type: Literal[
        "full_text_search", "semantic_search", "hybrid_search", "hybrid_reranking"
    ] = "hybrid_reranking"
    hybrid_settings: dict
    reranker_settings: dict


class KnowledgeBaseHybridSettings(BaseModel):
    fts_weight: float


class KnowledgeBaseSettings(BaseModel):
    ingestion: KnowledgeBaseIngestion
    retrieval: KnowledgeBaseRetrieval


class KnowledgeBaseDocument(BaseModel):
    id: str
    name: str
    prefix: str
    status: DocumentStatus
    size: int
    source_type: str
    created_at: str
    updated_at: str
    error: Optional[dict] = None


class CreateDocument(BaseModel):
    name: str
    prefix: str = "/"
    source_type: str = "document"


class UpdateDocument(BaseModel):
    prefix: Optional[str] = None
    status: Optional[DocumentStatus] = None


class KnowledgeBase(BaseResource):
    id: str
    group_id: str
    name: str
    status: str
    description: str
    document_types: list[str]
    kb_type: str
    size: int
    num_docs: int
    created_at: str
    updated_at: str
    total_documents: int
    training_documents: int
    trained_documents: int
    error_documents: int
    uploaded_documents: int
    source_types: dict
    training_source_types: list[str]
    settings_: KnowledgeBaseSettings
    retrieval: dict | None = None
    error: dict | None = None
    embeddings: dict | None = None
    documents: list[KnowledgeBaseDocument] = []

    def refresh(self) -> "KnowledgeBase":
        response = self.client.get(f"/v1/knowledge-bases/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    async def arefresh(self) -> "KnowledgeBase":
        response = await self.client.aget(f"/v1/knowledge-bases/{self.id}")
        for key, value in response.items():
            setattr(self, key, value)
        return self

    def delete(self) -> bool:
        response = self.client.delete(f"/v1/knowledge-bases/{self.id}")
        return response["success"]

    async def adelete(self) -> bool:
        response = await self.client.adelete(f"/v1/knowledge-bases/{self.id}")
        return response["success"]

    def get_runs(
        self, status: RunStatus | None = None, run_ids: str | None = None
    ) -> List[Run]:
        params = {}
        if status:
            params["status"] = status
        if run_ids:
            params["run_ids"] = run_ids

        response = self.client.get(f"/v1/knowledge-bases/{self.id}/runs", params=params)
        return [Run(client=self.client, **run) for run in response]

    async def aget_runs(
        self, status: RunStatus | None = None, run_ids: str | None = None
    ) -> List[Run]:
        params = {}
        if status:
            params["status"] = status
        if run_ids:
            params["run_ids"] = run_ids

        response = await self.client.aget(
            f"/v1/knowledge-bases/{self.id}/runs", params=params
        )
        return [Run(client=self.client, **run) for run in response]

    def get_document(self, document_id: str) -> KnowledgeBaseDocument:
        response = self.client.get(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    async def aget_document(self, document_id: str) -> KnowledgeBaseDocument:
        response = await self.client.aget(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    def create_document(self, document: CreateDocument) -> KnowledgeBaseDocument:
        response = self.client.post(
            f"/v1/knowledge-bases/{self.id}/document", body=document.model_dump()
        )
        return KnowledgeBaseDocument(**response)

    async def acreate_document(self, document: CreateDocument) -> KnowledgeBaseDocument:
        response = await self.client.apost(
            f"/v1/knowledge-bases/{self.id}/document", body=document.model_dump()
        )
        return KnowledgeBaseDocument(**response)

    def upload_document(
        self, files: List[Union[str, Path]], prefix: str = "/"
    ) -> List[RunID]:
        files_list: List[HttpxFile] = [
            ("files", (Path(file).name, io.open(str(file), "rb"), None))
            for file in files
        ]

        response = self.client.post(
            f"/v1/knowledge-bases/{self.id}/upload_train",
            files=files_list,
            params={"prefix": prefix},
        )
        return response

    async def aupload_document(
        self, files: List[Union[str, Path]], prefix: str = "/"
    ) -> List[RunID]:
        files_list: List[HttpxFile] = [
            ("files", (Path(file).name, io.open(str(file), "rb"), None))
            for file in files
        ]

        response = await self.client.apost(
            f"/v1/knowledge-bases/{self.id}/upload_train",
            files=files_list,
            params={"prefix": prefix},
        )
        return response

    def update_document(
        self, document_id: str, update: UpdateDocument
    ) -> KnowledgeBaseDocument:
        response = self.client.patch(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}",
            update.model_dump(exclude_none=True),
        )
        return KnowledgeBaseDocument(**response)

    async def aupdate_document(
        self, document_id: str, update: UpdateDocument
    ) -> KnowledgeBaseDocument:
        response = await self.client.apatch(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}",
            update.model_dump(exclude_none=True),
        )
        return KnowledgeBaseDocument(**response)

    def delete_document(self, document_id: str) -> KnowledgeBaseDocument:
        response = self.client.delete(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    async def adelete_document(self, document_id: str) -> KnowledgeBaseDocument:
        response = await self.client.adelete(
            f"/v1/knowledge-bases/{self.id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    def list_documents(
        self, status: DocumentStatus | None = None, page: int = 1, page_size: int = 10
    ) -> List[KnowledgeBaseDocument]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status

        response = self.client.get(
            f"/v1/knowledge-bases/{self.id}/documents/{status if status else ''}",
            params=params,
        )
        print(response)
        return [KnowledgeBaseDocument(**doc) for doc in response["items"]]

    async def alist_documents(
        self, status: DocumentStatus | None = None, page: int = 1, page_size: int = 10
    ) -> List[KnowledgeBaseDocument]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status

        response = await self.client.aget(
            f"/v1/knowledge-bases/{self.id}/documents/{status if status else ''}",
            params=params,
        )
        return [KnowledgeBaseDocument(**doc) for doc in response]


class KnowledgeBaseService(BaseService[KnowledgeBase]):
    def list(self, page: int = 1, page_size: int = 10) -> list[KnowledgeBase]:
        knowledge_bases = self.client.pget(
            "/v1/knowledge-bases", params={"page": page, "page_size": page_size}
        )
        return [
            KnowledgeBase(client=self.client, **knowledge_base)
            for knowledge_base in knowledge_bases
        ]

    async def alist(self, page: int = 1, page_size: int = 10) -> List[KnowledgeBase]:
        knowledge_bases = await self.client.apget(
            "/v1/knowledge-bases", params={"page": page, "page_size": page_size}
        )
        return [
            KnowledgeBase(client=self.client, **knowledge_base)
            for knowledge_base in knowledge_bases
        ]

    def get(self, knowledge_base_id: str) -> KnowledgeBase:
        knowledge_base = self.client.get(f"/v1/knowledge-bases/{knowledge_base_id}")
        return KnowledgeBase(client=self.client, **knowledge_base)

    async def aget(self, knowledge_base_id: str) -> KnowledgeBase:
        knowledge_base = await self.client.aget(
            f"/v1/knowledge-bases/{knowledge_base_id}"
        )
        return KnowledgeBase(client=self.client, **knowledge_base)

    def create(
        self,
        name: str,
        description: str,
        document_types: List[str],
        settings_: KnowledgeBaseSettings,
    ) -> KnowledgeBase:
        knowledge_base = self.client.post(
            "/v1/knowledge-bases",
            {
                "name": name,
                "description": description,
                "document_types": document_types,
                "settings_": settings_.model_dump(),
                "kb_type": "entity",
            },
        )
        return KnowledgeBase(client=self.client, **knowledge_base)

    async def acreate(
        self,
        name: str,
        description: str,
        document_types: List[str],
        settings_: KnowledgeBaseSettings,
    ) -> KnowledgeBase:
        knowledge_base = await self.client.apost(
            "/v1/knowledge-bases",
            {
                "name": name,
                "description": description,
                "document_types": document_types,
                "settings_": settings_.model_dump(),
                "kb_type": "entity",
            },
        )

        return KnowledgeBase(client=self.client, **knowledge_base)

    def delete(self, knowledge_base_id: str) -> bool:
        response = self.client.delete(f"/v1/knowledge-bases/{knowledge_base_id}")
        return response["success"]

    async def adelete(self, knowledge_base_id: str) -> bool:
        response = await self.client.adelete(f"/v1/knowledge-bases/{knowledge_base_id}")
        return response["success"]

    def get_runs(
        self,
        knowledge_base_id: str,
        status: RunStatus | None = None,
        run_ids: str | None = None,
    ) -> List[Run]:
        params = {}
        if status:
            params["status"] = status
        if run_ids:
            params["run_ids"] = run_ids

        response = self.client.get(
            f"/v1/knowledge-bases/{knowledge_base_id}/runs", params=params
        )
        return [Run(client=self.client, **run) for run in response]

    async def aget_runs(
        self,
        knowledge_base_id: str,
        status: RunStatus | None = None,
        run_ids: str | None = None,
    ) -> List[Run]:
        params = {}
        if status:
            params["status"] = status
        if run_ids:
            params["run_ids"] = run_ids

        response = await self.client.aget(
            f"/v1/knowledge-bases/{knowledge_base_id}/runs", params=params
        )
        return [Run(client=self.client, **run) for run in response]

    def get_document(
        self, knowledge_base_id: str, document_id: str
    ) -> KnowledgeBaseDocument:
        response = self.client.get(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    async def aget_document(
        self, knowledge_base_id: str, document_id: str
    ) -> KnowledgeBaseDocument:
        response = await self.client.aget(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    def update_document(
        self, knowledge_base_id: str, document_id: str, update: UpdateDocument
    ) -> KnowledgeBaseDocument:
        response = self.client.patch(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}",
            update.model_dump(exclude_none=True),
        )
        return KnowledgeBaseDocument(**response)

    async def aupdate_document(
        self, knowledge_base_id: str, document_id: str, update: UpdateDocument
    ) -> KnowledgeBaseDocument:
        response = await self.client.apatch(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}",
            update.model_dump(exclude_none=True),
        )
        return KnowledgeBaseDocument(**response)

    def delete_document(
        self, knowledge_base_id: str, document_id: str
    ) -> KnowledgeBaseDocument:
        response = self.client.delete(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    async def adelete_document(
        self, knowledge_base_id: str, document_id: str
    ) -> KnowledgeBaseDocument:
        response = await self.client.adelete(
            f"/v1/knowledge-bases/{knowledge_base_id}/document/{document_id}"
        )
        return KnowledgeBaseDocument(**response)

    def list_documents(
        self,
        knowledge_base_id: str,
        status: DocumentStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> List[KnowledgeBaseDocument]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status

        response = self.client.get(
            f"/v1/knowledge-bases/{knowledge_base_id}/documents/{status if status else ''}",
            params=params,
        )
        print(response)
        return [KnowledgeBaseDocument(**doc) for doc in response]

    async def alist_documents(
        self,
        knowledge_base_id: str,
        status: DocumentStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> List[KnowledgeBaseDocument]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status

        response = await self.client.aget(
            f"/v1/knowledge-bases/{knowledge_base_id}/documents/{status if status else ''}",
            params=params,
        )
        return [KnowledgeBaseDocument(**doc) for doc in response]

    def create_document(
        self, knowledge_base_id: str, document: CreateDocument
    ) -> KnowledgeBaseDocument:
        response = self.client.post(
            f"/v1/knowledge-bases/{knowledge_base_id}/document",
            body=document.model_dump(),
        )
        return KnowledgeBaseDocument(**response)

    async def acreate_document(
        self, knowledge_base_id: str, document: CreateDocument
    ) -> KnowledgeBaseDocument:
        response = await self.client.apost(
            f"/v1/knowledge-bases/{knowledge_base_id}/document",
            body=document.model_dump(),
        )
        return KnowledgeBaseDocument(**response)

    def train_document(
        self, knowledge_base_id: str, source: Source, prefix: str = "/"
    ) -> List[RunID]:
        response = self.client.post(
            f"/v1/knowledge-bases/{knowledge_base_id}/generic_train",
            body=source.model_dump(),
            params={"prefix": prefix},
        )
        return response

    async def atrain_document(
        self, knowledge_base_id: str, source: Source, prefix: str = "/"
    ) -> List[RunID]:
        response = await self.client.apost(
            f"/v1/knowledge-bases/{knowledge_base_id}/generic_train",
            body=source.model_dump(),
            params={"prefix": prefix},
        )
        return response

    def upload_document(
        self, knowledge_base_id: str, files: List[Union[str, Path]], prefix: str = "/"
    ) -> List[RunID]:
        files_list: List[HttpxFile] = [
            ("files", (Path(file).name, io.open(str(file), "rb"), None))
            for file in files
        ]

        response = self.client.post(
            f"/v1/knowledge-bases/{knowledge_base_id}/upload_train",
            files=files_list,
            params={"prefix": prefix},
        )
        return response

    async def aupload_document(
        self, knowledge_base_id: str, files: List[Union[str, Path]], prefix: str = "/"
    ) -> List[RunID]:
        files_list: List[HttpxFile] = [
            ("files", (Path(file).name, io.open(str(file), "rb"), None))
            for file in files
        ]

        response = await self.client.apost(
            f"/v1/knowledge-bases/{knowledge_base_id}/upload_train",
            files=files_list,
            params={"prefix": prefix},
        )
        return response
