import pytest
import os
from noxus_sdk.client import Client
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def api_key():
    return os.environ.get("NOXUS_API_KEY", "")


@pytest.fixture
def client(api_key: str):
    return Client(
        api_key, base_url=os.environ.get("NOXUS_BASE_URL", "https://backend.noxus.ai")
    )


@pytest.fixture
async def kb(client: Client):
    settings = KnowledgeBaseSettings(
        ingestion=KnowledgeBaseIngestion(
            batch_size=10,
            default_chunk_size=1000,
            default_chunk_overlap=100,
            enrich_chunks_mode="contextual",
            enrich_pre_made_qa=False,
        ),
        retrieval=KnowledgeBaseRetrieval(
            type="hybrid_reranking",
            hybrid_settings={"fts_weight": 0.5},
            reranker_settings={},
        ),
    )

    kb = await client.knowledge_bases.acreate(
        name="test_kb",
        description="Test Knowledge Base",
        document_types=["text"],
        settings_=settings,
    )

    yield kb

    try:  # noqa: SIM105
        await kb.adelete()
    except Exception:
        pass
