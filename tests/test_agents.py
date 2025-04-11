import pytest
import httpx
from uuid import uuid4
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    MessageRequest,
)
from noxus_sdk.resources.assistants import (
    AgentSettings,
    WorkflowInfo,
    WorkflowTool,
    KnowledgeBaseSelectorTool,
    NoxusQaTool,
    WebResearchTool,
    KnowledgeBaseQaTool,
    KnowledgeBaseInfo,
)
from noxus_sdk.resources.workflows import (
    WorkflowDefinition,
)
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
)
from noxus_sdk.client import Client


@pytest.fixture
def agent_settings():
    return AgentSettings(
        model_selection=["gpt-4o"],
        temperature=0.7,
        tools=[WebResearchTool(), NoxusQaTool()],
        max_tokens=150,
        extra_instructions="Be concise and helpful.",
    )


@pytest.mark.anyio
async def test_create_agent(client: Client, agent_settings: AgentSettings):
    agent = await client.agents.acreate(name="Test Agent", settings=agent_settings)

    try:
        assert agent.name == "Test Agent"
        assert agent.definition.model_selection == ["gpt-4o"]
        assert agent.definition.temperature == 0.7
        assert agent.definition.max_tokens == 150
        assert agent.definition.extra_instructions == "Be concise and helpful."
        assert len(agent.definition.tools) == 2

        # Verify the tool types
        tool_types = [tool.type for tool in agent.definition.tools]
        assert "web_research" in tool_types
        assert "noxus_qa" in tool_types

        # Test get agent
        fetched = await client.agents.aget(agent.id)
        assert fetched.id == agent.id
        assert fetched.name == agent.name

    finally:
        await client.agents.adelete(agent.id)


@pytest.mark.anyio
async def test_list_agents(client: Client, agent_settings: AgentSettings):
    agent1 = await client.agents.acreate(name="Test Agent 1", settings=agent_settings)
    agent2 = await client.agents.acreate(name="Test Agent 2", settings=agent_settings)

    try:
        agents = await client.agents.alist()
        assert len(agents) >= 2
        agent_names = [agent.name for agent in agents]
        assert "Test Agent 1" in agent_names
        assert "Test Agent 2" in agent_names

    finally:
        await client.agents.adelete(agent1.id)
        await client.agents.adelete(agent2.id)


@pytest.mark.anyio
async def test_update_agent(client: Client, agent_settings: AgentSettings):
    agent = await client.agents.acreate(name="Original Name", settings=agent_settings)

    # Create a workflow for testing
    workflow = WorkflowDefinition(client=client, name="Test Workflow")
    input_node = workflow.node("InputNode")
    ai_node = workflow.node("TextGenerationNode").config(
        label="Test Generation",
        template="Write a poem about ((Input 1))",
        model=["gpt-4o"],
    )
    output_node = workflow.node("OutputNode")
    workflow.link(input_node.output(), ai_node.input("variables", "Input 1"))
    workflow.link(ai_node.output(), output_node.input())
    created_workflow = await workflow.asave()

    # Create a knowledge base for testing
    kb_settings = KnowledgeBaseSettings(
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
        name="test_agent_kb",
        description="Test KB for agent",
        document_types=["text"],
        settings_=kb_settings,
    )

    try:
        # Update settings with real workflow ID
        new_settings = ConversationSettings(
            model_selection=["gpt-4o"],
            temperature=0.5,
            tools=[
                WorkflowTool(
                    workflow=WorkflowInfo(
                        id=created_workflow.id, name=created_workflow.name
                    )
                )
            ],
            max_tokens=200,
            extra_instructions="Updated instructions",
        )

        updated = await client.agents.aupdate(
            agent.id, name="Updated Name", settings=new_settings
        )

        assert updated.name == "Updated Name"
        assert updated.definition.model_selection == ["gpt-4o"]
        assert updated.definition.temperature == 0.5
        assert updated.definition.max_tokens == 200
        assert updated.definition.extra_instructions == "Updated instructions"
        assert len(updated.definition.tools) == 1
        assert updated.definition.tools[0].type == "workflow"
        assert updated.definition.tools[0].workflow.id == created_workflow.id

        # Test instance update method with real KB
        instance_updated = await client.agents.aget(agent.id)
        instance_settings = ConversationSettings(
            model_selection=["gpt-4o"],
            temperature=0.8,
            tools=[KnowledgeBaseSelectorTool()],
            max_tokens=300,
        )
        result = instance_updated.update(
            name="Instance Updated", settings=instance_settings
        )

        assert result.name == "Instance Updated"
        assert result.definition.model_selection == ["gpt-4o"]
        assert result.definition.temperature == 0.8
        assert result.definition.max_tokens == 300
        assert len(result.definition.tools) == 1
        assert result.definition.tools[0].type == "kb_selector"

    finally:
        await client.agents.adelete(agent.id)
        await test_kb.adelete()


@pytest.mark.anyio
async def test_create_conversation_with_agent(
    client: Client, agent_settings: AgentSettings
):
    # Create an agent
    agent = await client.agents.acreate(
        name="Conversation Agent", settings=agent_settings
    )

    # Create a conversation with the agent
    conversation = await client.conversations.acreate(
        name="Agent Conversation", agent_id=agent.id
    )
    try:
        assert conversation.name == "Agent Conversation"

        # Send a message to the conversation
        message = MessageRequest(content="Hello agent, how are you?")
        await conversation.aadd_message(message)

        # Get messages
        messages = await conversation.aget_messages()
        assert len(messages) >= 1

    finally:
        # Clean up
        await client.agents.adelete(agent.id)
        await client.conversations.adelete(conversation.id)


@pytest.mark.anyio
async def test_agent_with_all_tool_types(client: Client):
    # Create a workflow for testing
    workflow = WorkflowDefinition(client=client, name="Test All Tools Workflow")
    input_node = workflow.node("InputNode")
    ai_node = workflow.node("TextGenerationNode").config(
        label="Test Generation",
        template="Write a poem about ((Input 1))",
        model=["gpt-4o"],
    )
    output_node = workflow.node("OutputNode")
    workflow.link(input_node.output(), ai_node.input("variables", "Input 1"))
    workflow.link(ai_node.output(), output_node.input())
    created_workflow = await workflow.asave()

    # Create a knowledge base for testing
    kb_settings = KnowledgeBaseSettings(
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
        name="test_all_tools_kb",
        description="Test KB for all tools",
        document_types=["text"],
        settings_=kb_settings,
    )

    # Create an agent with all tool types and real IDs
    settings = ConversationSettings(
        model_selection=["gpt-4"],
        temperature=0.7,
        tools=[
            WebResearchTool(),
            NoxusQaTool(),
            KnowledgeBaseSelectorTool(),
            KnowledgeBaseQaTool(
                knowledge_base=KnowledgeBaseInfo(id=test_kb.id, name=test_kb.name)
            ),
            WorkflowTool(
                workflow=WorkflowInfo(
                    id=created_workflow.id, name=created_workflow.name
                )
            ),
        ],
        max_tokens=150,
    )

    agent = await client.agents.acreate(name="Multi-Tool Agent", settings=settings)

    try:
        # Verify all tools were set
        assert len(agent.definition.tools) == 5

        # Check if all tool types are present
        tool_types = [tool.type for tool in agent.definition.tools]
        assert "web_research" in tool_types
        assert "noxus_qa" in tool_types
        assert "kb_selector" in tool_types
        assert "kb_qa" in tool_types
        assert "workflow" in tool_types

        # Verify specific tool properties
        workflow_tool = next(
            tool for tool in agent.definition.tools if tool.type == "workflow"
        )
        assert workflow_tool.workflow.id == created_workflow.id

    finally:
        await client.agents.adelete(agent.id)
        await test_kb.adelete()


@pytest.mark.anyio
async def test_nonexistent_agent(client: Client):
    agent_id = str(uuid4())  # Mock agent ID
    with pytest.raises(httpx.HTTPStatusError):
        res = await client.agents.aget(agent_id)


@pytest.mark.anyio
async def test_delete_agent(client: Client, agent_settings: AgentSettings):
    # Create an agent
    agent = await client.agents.acreate(name="To Be Deleted", settings=agent_settings)

    # Delete it
    await client.agents.adelete(agent.id)

    # Verify it's gone
    with pytest.raises(httpx.HTTPStatusError):
        await client.agents.aget(agent.id)


def test_synchronous_agent_operations(client: Client, agent_settings: AgentSettings):
    # Test synchronous create
    agent = client.agents.create(name="Sync Agent", settings=agent_settings)

    try:
        # Test synchronous get
        fetched = client.agents.get(agent.id)
        assert fetched.id == agent.id

        # Test synchronous list
        agents = client.agents.list()
        assert any(a.id == agent.id for a in agents)

        # Test synchronous update
        updated_settings = ConversationSettings(
            model_selection=["gpt-4"],
            temperature=0.5,
            tools=[NoxusQaTool()],
            max_tokens=100,
        )
        updated = client.agents.update(
            agent_id=agent.id, name="Updated Sync Agent", settings=updated_settings
        )
        assert updated.name == "Updated Sync Agent"
        assert updated.definition.temperature == 0.5

    finally:
        # Test synchronous delete
        client.agents.delete(agent.id)

        # Verify deletion
        with pytest.raises(httpx.HTTPStatusError):
            client.agents.get(agent.id)
