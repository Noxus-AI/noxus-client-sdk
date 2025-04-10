import pytest
import httpx
from uuid import uuid4
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    MessageRequest,
    WebResearchTool,
    NoxusQaTool,
    ConversationFile,
)

@pytest.fixture
def conversation_settings():
    return ConversationSettings(
        model_selection=["gpt-4"],
        temperature=0.7,
        tools=[
            NoxusQaTool()
        ]
    )

@pytest.mark.anyio
async def test_create_conversation(client, conversation_settings):
    conversation = await client.conversations.acreate(
        name="Test Conversation",
        settings=conversation_settings
    )
    
    try:
        assert conversation.name == "Test Conversation"
        assert conversation.settings.model_selection == ["gpt-4"]
        assert conversation.settings.temperature == 0.7
        assert len(conversation.settings.tools) == 1
        
        # Test get conversation
        fetched = await client.conversations.aget(conversation.id)
        assert fetched.id == conversation.id
        assert fetched.name == conversation.name
        
    finally:
        await client.conversations.adelete(conversation.id)

@pytest.mark.anyio
async def test_list_conversations(client, conversation_settings):
    conv1 = await client.conversations.acreate(
        name="Test Conv 1",
        settings=conversation_settings
    )
    conv2 = await client.conversations.acreate(
        name="Test Conv 2", 
        settings=conversation_settings
    )
    
    try:
        conversations = await client.conversations.alist()
        assert len(conversations) >= 2
        
        # Test pagination
        page1 = await client.conversations.alist()
        assert len(page1) == 1
        
    finally:
        await client.conversations.adelete(conv1.id)
        await client.conversations.adelete(conv2.id)

@pytest.mark.anyio
async def test_conversation_messages(client, conversation_settings):
    conversation = await client.conversations.acreate(
        name="Test Messages",
        settings=conversation_settings
    )
    
    try:
        # Add a message
        message = MessageRequest(content="Hello, world!")
        await conversation.aadd_message(message)
        
        # Get messages
        messages = await conversation.aget_messages()

        assert len(messages) >= 1
        assert any(
            any("Hello, world!" in part.get("content", "") 
                for part in msg.message_parts)
            for msg in messages
        ), messages
        
    finally:
        await client.conversations.adelete(conversation.id)

@pytest.mark.anyio
async def test_conversation_with_file(client, conversation_settings):
    conversation = await client.conversations.acreate(
        name="Test With File",
        settings=conversation_settings
    )
    
    try:
        file = ConversationFile(
            name="test.txt",
            url="https://example.com/test.txt",
            status="success"
        )
        
        message = MessageRequest(
            content="Process this file",
            files=[file]
        )
        
        await conversation.aadd_message(message)
        messages = await conversation.aget_messages()
        assert len(messages) >= 1
        
    finally:
        await client.conversations.adelete(conversation.id)

@pytest.mark.anyio
@pytest.mark.skip(reason="Not implemented")
async def test_update_conversation(client, conversation_settings):
    conversation = await client.conversations.acreate(
        name="Original Name",
        settings=conversation_settings
    )
    
    try:
        # Update settings
        new_settings = ConversationSettings(
            model_selection=["gpt-3.5-turbo"],
            temperature=0.5,
            tools=[WebResearchTool()]
        )
        
        updated = await client.conversations.aupdate(
            conversation.id,
            name="Updated Name",
            settings=new_settings
        )
        
        assert updated.name == "Updated Name"
        assert updated.settings.model_selection == ["gpt-3.5-turbo"]
        assert updated.settings.temperature == 0.5
        assert len(updated.settings.tools) == 1
        
    finally:
        await client.conversations.adelete(conversation.id)

@pytest.mark.anyio
async def test_create_nonexistant_with_agent(client):
    agent_id = str(uuid4())  # Mock agent ID
    with pytest.raises(httpx.HTTPStatusError):
        conversation = await client.conversations.acreate(
            name="Agent Conversation",
            agent_id=agent_id
        )

def test_invalid_creation_params(client, conversation_settings):
    with pytest.raises(ValueError):
        client.conversations.create(
            name="Invalid",
            settings=conversation_settings,
            agent_id="some-id"
        )
        
    with pytest.raises(ValueError):
        client.conversations.create(
            name="Invalid"
        )
