import pytest
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBase,
    UpdateDocument,
    CreateDocument,
    KnowledgeBaseDocument,
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
)


@pytest.mark.asyncio
async def test_list_documents(kb: KnowledgeBase):
    _ = await kb.acreate_document(CreateDocument(name="test_doc1", prefix="/test1"))
    _ = await kb.acreate_document(CreateDocument(name="test_doc2", prefix="/test2"))

    documents = await kb.alist_documents()
    assert len(documents) >= 2
    assert any(d.name == "test_doc1" for d in documents)
    assert any(d.name == "test_doc2" for d in documents)

    docs_by_status = await kb.alist_documents(status="uploaded")
    assert all(d.status == "uploaded" for d in docs_by_status)

    page1 = await kb.alist_documents(page=1, page_size=1)
    page2 = await kb.alist_documents(page=2, page_size=1)
    assert len(page1) == 1
    assert len(page2) == 1
    assert page1[0].id != page2[0].id


@pytest.mark.asyncio
async def test_document_operations(kb: KnowledgeBase):
    test_doc = await kb.acreate_document(
        CreateDocument(name="test_doc", prefix="/test")
    )
    assert isinstance(test_doc, KnowledgeBaseDocument)
    assert test_doc.name == "test_doc"
    assert test_doc.prefix == "/test"
    assert test_doc.status in ["uploaded", "training", "trained", "error"]
    assert test_doc.source_type == "document"
    assert test_doc.error is None

    doc = await kb.aget_document(test_doc.id)
    assert doc.id == test_doc.id
    assert doc.name == test_doc.name
    assert doc.created_at is not None
    assert doc.updated_at is not None

    updated_doc = await kb.aupdate_document(
        doc.id, UpdateDocument(prefix="/updated/path")
    )
    assert updated_doc.prefix == "/updated/path"
    assert updated_doc.id == doc.id
    assert updated_doc.updated_at >= doc.updated_at

    deleted_doc = await kb.adelete_document(doc.id)
    assert deleted_doc.id == doc.id

    with pytest.raises(Exception):
        await kb.aget_document(doc.id)


@pytest.mark.asyncio
async def test_kb_status(kb: KnowledgeBase):
    await kb.acreate_document(CreateDocument(name="doc1", prefix="/test"))
    await kb.acreate_document(CreateDocument(name="doc2", prefix="/test"))

    await kb.arefresh()
    assert kb.status in ["active", "training", "error"]
    assert kb.total_documents >= 2
    assert isinstance(kb.trained_documents, int)
    assert isinstance(kb.error_documents, int)
    assert kb.total_documents >= kb.trained_documents + kb.error_documents


@pytest.mark.asyncio
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

        page1 = await client.knowledge_bases.alist(page=1, page_size=1)
        page2 = await client.knowledge_bases.alist(page=2, page_size=1)
        assert len(page1) == 1
        assert len(page2) == 1
        if len(knowledge_bases) > 1:
            assert page1[0].id != page2[0].id

    finally:
        await test_kb.adelete()


@pytest.mark.asyncio
async def test_kb_cleanup(kb: KnowledgeBase):
    _ = await kb.acreate_document(CreateDocument(name="cleanup_doc1", prefix="/test"))
    _ = await kb.acreate_document(CreateDocument(name="cleanup_doc2", prefix="/test"))

    documents = await kb.alist_documents()
    assert len(documents) >= 2

    for doc in documents:
        deleted_doc = await kb.adelete_document(doc.id)
        assert deleted_doc.id == doc.id

    remaining_docs = await kb.alist_documents()
    assert len(remaining_docs) == 0

    success = await kb.adelete()
    assert success is True

    with pytest.raises(Exception):
        await kb.arefresh()
