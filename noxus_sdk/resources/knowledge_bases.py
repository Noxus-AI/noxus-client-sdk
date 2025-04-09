from pydantic import BaseModel
from typing import List, Literal
from noxus_sdk.resources.base import BaseResource, BaseService


class KnowledgeBaseIngestion(BaseModel):
    batch_size: int
    default_chunk_size: int
    default_chunk_overlap: int
    enrich_chunks_mode: Literal["inject_summary", "contextual"] = "contextual"
    enrich_pre_made_qa: bool
    methods: dict


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
    embeddings: dict


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
            },
        )

        return KnowledgeBase(client=self.client, **knowledge_base)
