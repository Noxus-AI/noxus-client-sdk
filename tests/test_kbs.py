import pytest
import tempfile
import os
import asyncio
from pathlib import Path
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBase,
    UpdateDocument,
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
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
    run_ids1 = await kb.aupload_document([test_file], prefix="/test1")

    await wait_for_documents(kb, 1)

    training_documents = await kb.alist_documents(status="training")
    trained_documents = await kb.alist_documents(status="trained")
    assert len(training_documents) + len(trained_documents) == 1

    page1 = await kb.alist_documents(status="training", page=1, page_size=1)
    assert len(page1) == 1
    assert page1[0].id == training_documents[0].id


@pytest.mark.anyio
async def test_document_operations(kb: KnowledgeBase, test_file: Path):
    run_ids = await kb.aupload_document([test_file], prefix="/test")

    await wait_for_documents(kb, 1)

    training_documents = await kb.alist_documents(status="training")
    trained_documents = await kb.alist_documents(status="trained")
    assert len(training_documents) + len(trained_documents) == 1
    docs = trained_documents + training_documents
    doc = docs[0]
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
async def test_kb_status(kb: KnowledgeBase, test_file: Path):
    run_ids1 = await kb.aupload_document([test_file], prefix="/test1")
    run_ids2 = await kb.aupload_document([test_file], prefix="/test2")

    assert len(run_ids1) > 0
    assert len(run_ids2) > 0

    await asyncio.sleep(1)

    await kb.arefresh()
    assert kb.status in ["trained", "training"]
    assert kb.total_documents >= 2
    assert isinstance(kb.trained_documents, int)
    assert isinstance(kb.error_documents, int)
    assert kb.total_documents >= kb.trained_documents + kb.error_documents


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
        page1 = await client.knowledge_bases.alist(page=1, page_size=2)
        assert len(page1) == 2

    finally:
        await test_kb.adelete()


@pytest.mark.anyio
async def test_kb_cleanup(kb: KnowledgeBase, test_file: Path):
    success = await kb.adelete()
    assert success is True

    with pytest.raises(Exception):
        await kb.arefresh()
