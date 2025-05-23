import asyncio
from pathlib import Path
import time

import pytest
from noxus_sdk.resources.knowledge_bases import (
    CreateDocument,
    KnowledgeBase,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
    KnowledgeBaseSettings,
    UpdateDocument,
)
from noxus_sdk.client import Client


async def wait_for_documents(kb: KnowledgeBase, expected_count: int, timeout: int = 30):
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        await kb.arefresh()
        if kb.total_documents >= expected_count:
            return True
        await asyncio.sleep(2)
    return False


@pytest.mark.anyio
async def test_list_documents(kb: KnowledgeBase, test_file: Path):
    doc = await kb.acreate_document(CreateDocument(name="test1", prefix="/test1"))

    documents = await kb.alist_documents(status="uploaded")
    assert len(documents) == 1


@pytest.mark.anyio
async def test_document_operations(kb: KnowledgeBase, test_file: Path):
    doc = await kb.acreate_document(CreateDocument(name="test1", prefix="/test1"))

    documents = await kb.alist_documents(status="uploaded")
    assert len(documents) == 1
    updated_doc = await kb.aupdate_document(
        doc.id, UpdateDocument(prefix="/updated/path")
    )
    assert updated_doc.prefix == "/updated/path"
    assert updated_doc.id == doc.id

    deleted_doc = await kb.adelete_document(doc.id)
    assert deleted_doc.id == doc.id

    with pytest.raises(Exception):
        await kb.aget_document(doc.id)


@pytest.mark.anyio
async def test_list_knowledge_bases(client):
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

    test_kb = await client.knowledge_bases.acreate(
        name="test_list_kb",
        description="Test KB for listing",
        document_types=["text"],
        settings_=settings,
    )

    try:
        knowledge_bases = await client.knowledge_bases.alist(page=1, page_size=10)
        assert len(knowledge_bases) > 0

        found_kb = next((kb for kb in knowledge_bases if kb.id == test_kb.id), None)
        assert found_kb is not None
        assert found_kb.name == "test_list_kb"
        assert found_kb.description == "Test KB for listing"
        assert found_kb.document_types == ["text"]
        assert found_kb.kb_type == "entity"

        # We have a kb from fixtures
        page1 = await client.knowledge_bases.alist(page=1, page_size=10)
        assert len(page1) == 1

    finally:
        await test_kb.adelete()


@pytest.mark.anyio
async def test_kb_cleanup(client: Client):
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
    success = await kb.adelete()
    assert success is True

    with pytest.raises(Exception):
        await kb.arefresh()


@pytest.mark.anyio
async def test_kb_training(client: Client, test_file: Path):
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
    assert kb.status == "created"
    await kb.arefresh()
    assert kb.status == "created"
    # assert await wait_for_documents(kb, 1)
    await kb.aupload_document([test_file], prefix="/test1")
    while kb.status not in ["training", "error"]:
        await kb.arefresh()
    assert kb.status in ["training"]

    trained_docs = await kb.alist_documents(status="trained")
    timeout = time.time() + 60  # 60s timeout
    while len(trained_docs) == 0 and timeout - time.time() > 0:
        trained_docs = await kb.alist_documents(status="trained")
        await asyncio.sleep(0.5)
    training_docs = await kb.alist_documents(status="training")
    uploaded_docs = await kb.alist_documents(status="uploaded")
    assert len(trained_docs) + len(training_docs) + len(uploaded_docs) == 1
