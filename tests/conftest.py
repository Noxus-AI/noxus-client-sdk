import os
import tempfile
from pathlib import Path
import pytest
from noxus_sdk.client import Client
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
    KnowledgeBaseSettings,
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
async def test_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content for document upload")
        path = Path(f.name)

    yield path

    try:
        os.unlink(path)
    except Exception:
        pass


@pytest.fixture
async def kb(client: Client, test_file: Path):
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
    # await kb.aupload_document([test_file], prefix="/test1")

    yield kb

    try:  # noqa: SIM105
        await kb.adelete()
    except Exception:
        pass


@pytest.fixture(autouse=True)
async def cleanup_resources(client: Client):
    yield

    # Clean up knowledge bases
    kbs = await client.knowledge_bases.alist()
    for kb in kbs:
        try:
            await kb.adelete()
        except Exception:
            pass

    # Clean up agents
    agents = await client.agents.alist()
    for agent in agents:
        try:
            await client.agents.adelete(agent.id)
        except Exception:
            pass

    conversations = await client.conversations.alist()
    for conversation in conversations:
        try:
            await client.conversations.adelete(conversation.id)
        except Exception:
            pass

    workflows = await client.workflows.alist()
    for workflow in workflows:
        try:
            await client.workflows.adelete(workflow.id)
        except Exception:
            pass
