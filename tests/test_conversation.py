import asyncio
import base64
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from noxus_sdk.client import Client
from noxus_sdk.resources.conversations import (
    ConversationFile,
    ConversationSettings,
    KnowledgeBaseQaTool,
    KnowledgeBaseSelectorTool,
    MessageRequest,
    NoxusQaTool,
    WebResearchTool,
)
from noxus_sdk.resources.knowledge_bases import KnowledgeBase


@pytest.fixture
def conversation_settings():
    return ConversationSettings(
        model=["gpt-4o"], temperature=0.7, tools=[NoxusQaTool()]
    )


@pytest.mark.anyio
async def test_create_conversation(
    client: Client, conversation_settings: ConversationSettings
):
    conversation = await client.conversations.acreate(
        name="Test Conversation", settings=conversation_settings
    )

    try:
        assert conversation.name == "Test Conversation"
        assert conversation.settings.model == ["gpt-4o"]
        assert conversation.settings.temperature == 0.7
        assert len(conversation.settings.tools) == 1

        # Test get conversation
        fetched = await client.conversations.aget(conversation.id)
        assert fetched.id == conversation.id
        assert fetched.name == conversation.name

    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_list_conversations(
    client: Client, conversation_settings: ConversationSettings
):
    conv1 = await client.conversations.acreate(
        name="Test Conv 1", settings=conversation_settings
    )
    conv2 = await client.conversations.acreate(
        name="Test Conv 2", settings=conversation_settings
    )
    conversations = await client.conversations.alist()
    assert len(conversations) == 0

    await conv1.aadd_message(MessageRequest(content="Hello, world!"))
    await conv2.aadd_message(MessageRequest(content="Hello, world!"))

    try:
        conversations = await client.conversations.alist()
        assert len(conversations) == 2

        # Test pagination
        page1 = await client.conversations.alist(page=1, page_size=1)
        assert len(page1) == 1

    finally:
        await client.conversations.adelete(conv1.id)
        await client.conversations.adelete(conv2.id)


@pytest.mark.anyio
async def test_conversation_messages(
    client: Client, conversation_settings: ConversationSettings
):
    conversation = await client.conversations.acreate(
        name="Test Messages", settings=conversation_settings
    )

    try:
        # Add a message
        message = MessageRequest(content="Hello, world!")
        await conversation.aadd_message(message)

        # Get messages
        messages = await conversation.aget_messages()

        assert len(messages) >= 1
        assert any(
            any(
                "Hello, world!" in part.get("content", "") for part in msg.message_parts
            )
            for msg in messages
        ), messages

    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_conversation_with_kb(client: Client, kb: KnowledgeBase, test_file: Path):
    conversation_settings = ConversationSettings(
        model=["gpt-4o"], temperature=0.7, tools=[KnowledgeBaseSelectorTool()]
    )

    conversation = await client.conversations.acreate(
        name="Test With KB", settings=conversation_settings
    )
    await kb.aupload_document([test_file], prefix="/test1")
    await asyncio.sleep(1)

    try:
        message = MessageRequest(
            content="What is the capital of France?", kb_id=kb.id, tool="kb_qa"
        )
        await conversation.aadd_message(message)

        messages = await conversation.aget_messages()
        assert len(messages) >= 2
        assert any(
            # check if any message part has tool calls, meaning it called the kb
            any(part.get("role", None) == "function" for part in msg.message_parts)
            for msg in messages
        ), messages
    finally:
        await client.conversations.adelete(conversation.id)
        await kb.arefresh()
        await kb.adelete_document(kb.documents[0].id)


@pytest.mark.anyio
async def test_conversation_with_web_search(client: Client):
    conversation_settings = ConversationSettings(
        model=["gpt-4o"], temperature=0.7, tools=[WebResearchTool()]
    )

    conversation = await client.conversations.acreate(
        name="Test With Web Search", settings=conversation_settings
    )

    try:
        message = MessageRequest(
            content="What is the capital of France?", tool="web_research"
        )
        await conversation.aadd_message(message)

        messages = await conversation.aget_messages()
        assert len(messages) >= 2
        assert any(
            # check if any message part has tool calls, meaning it called the kb
            any(part.get("role", None) == "function" for part in msg.message_parts)
            for msg in messages
        ), messages
    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_conversation_with_noxus_qa(client: Client):
    conversation_settings = ConversationSettings(
        model=["gpt-4o"], temperature=0.7, tools=[NoxusQaTool()]
    )

    conversation = await client.conversations.acreate(
        name="Test With Noxus QA", settings=conversation_settings
    )

    try:
        message = MessageRequest(
            content="What is the capital of France?", tool="noxus_qa"
        )
        await conversation.aadd_message(message)

        messages = await conversation.aget_messages()
        assert len(messages) >= 2
        assert any(
            # check if any message part has tool calls, meaning it called the kb
            any(part.get("role", None) == "function" for part in msg.message_parts)
            for msg in messages
        ), messages
    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_conversation_with_file_b64(
    client: Client, conversation_settings: ConversationSettings
):
    conversation = await client.conversations.acreate(
        name="Test With File", settings=conversation_settings
    )

    try:
        file = ConversationFile(
            name="test.txt",
            status="success",
            b64_content=base64.b64encode(b"Hello, world!").decode("utf-8"),
        )

        message = MessageRequest(content="What does the file say?", files=[file])

        await conversation.aadd_message(message)
        messages = await conversation.aget_messages()
        assert len(messages) >= 1
        assert any(
            "hello, world!" in part.get("content", "").lower()
            for msg in messages
            for part in msg.message_parts
        )

    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_update_conversation(
    client: Client, conversation_settings: ConversationSettings
):
    conversation = await client.conversations.acreate(
        name="Original Name", settings=conversation_settings
    )

    try:
        # Update settings
        new_settings = ConversationSettings(
            model=["gpt-3.5-turbo"],
            temperature=0.5,
            tools=[WebResearchTool()],
        )

        updated = await client.conversations.aupdate(
            conversation.id, name="Updated Name", settings=new_settings
        )

        assert updated.name == "Updated Name"
        assert updated.settings.model == ["gpt-3.5-turbo"]
        assert updated.settings.temperature == 0.5
        assert len(updated.settings.tools) == 1

    finally:
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_create_nonexistant_with_agent(client: Client):
    agent_id = str(uuid4())  # Mock agent ID
    with pytest.raises(httpx.HTTPStatusError):
        conversation = await client.conversations.acreate(
            name="Agent Conversation", agent_id=agent_id
        )


def test_invalid_creation_params(
    client: Client, conversation_settings: ConversationSettings
):
    with pytest.raises(ValueError):
        client.conversations.create(
            name="Invalid", settings=conversation_settings, agent_id="some-id"
        )

    with pytest.raises(ValueError):
        client.conversations.create(name="Invalid")
