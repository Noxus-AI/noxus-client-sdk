# noxus-client-sdk

## Overview

The `noxus-client-sdk` is a Python library designed to interact with the Noxus AI backend. It provides a convenient interface for managing workflows, conversations, knowledge bases, agents, and more. This SDK abstracts away the complexity of direct API calls, allowing developers to focus on building applications rather than managing HTTP requests.

## Installation

To install the SDK, use pip:

```bash
pip install noxus-client-sdk
```

The SDK requires Python 3.8 or later and automatically installs all necessary dependencies.

## Usage

Here's a quick example of how to use the SDK to interact with the Noxus backend:

```python
from noxus_sdk.client import Client

# Initialize the client with your API key
client = Client(api_key="your_api_key_here")

# List all workflows
workflows = client.workflows.list()
for workflow in workflows:
    print(workflow.name)

# Create a new conversation
from noxus_sdk.resources.conversations import ConversationSettings

settings = ConversationSettings(
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[],
    extra_instructions="Please be concise."
)

conversation = client.conversations.create(name="New Conversation", settings=settings)
print(conversation.id)
```

The SDK follows a consistent pattern across all resource types: initialize the client once, then access different resources through the client instance.

## Examples

Below are detailed examples for working with various Noxus resources. Each example demonstrates the common operations (list, create, get, update, delete) for that resource type.

### Client Initialization

The client is your entry point to all SDK functionality. All you need is your API key:

```python
from noxus_sdk.client import Client

# Initialize the client with your API key
client = Client(api_key="your_api_key_here")
```

You can also specify a custom backend URL if needed by setting the `NOXUS_BACKEND_URL` environment variable or passing the `base_url` parameter.

### Workflows

Workflows allow you to define complex sequences of operations that can be executed on demand:

```python
# List all workflows
workflows = client.workflows.list(page=1, page_size=10)
for workflow in workflows:
    print(f"Workflow ID: {workflow.id}, Name: {workflow.name}")

# Get a specific workflow
workflow = client.workflows.get(workflow_id="workflow_id_here")

# Create a new workflow using the WorkflowDefinition class
from noxus_sdk.workflows import WorkflowDefinition

workflow_def = WorkflowDefinition()
# Add nodes and connections to your workflow definition
new_workflow = client.workflows.save(workflow_def)
print(f"Created Workflow ID: {new_workflow.id}")

# Update an existing workflow
updated_workflow = client.workflows.update(
    workflow_id="workflow_id_here", 
    workflow=workflow_def,
    force=False
)
```

The `WorkflowDefinition` class provides a programmatic way to define workflow nodes and their connections.

### Running Workflows

Once you have a workflow, you can execute it and retrieve the results:

```python
# Run a workflow
workflow = client.workflows.get(workflow_id="workflow_id_here")
run = workflow.run(body={"input_key": "input_value"})

# Wait for the workflow to complete
result = run.wait(interval=5)
print(f"Run status: {result.status}")
print(f"Output: {result.output}")

# Get a list of workflow runs
runs = client.run.list(workflow_id="workflow_id_here", page=1, page_size=10)
```

The `wait()` method allows you to block until the workflow completes, making it easy to handle workflow execution in a synchronous manner. You can adjust the polling interval as needed.

### Building Workflows

The SDK provides a powerful programmatic way to build complex workflows by connecting different nodes together:

```python
from noxus_sdk.workflows import WorkflowDefinition

# Create a new workflow definition
workflow = WorkflowDefinition(name="Example Workflow")

# Add nodes to the workflow
input_node = workflow.node("InputNode").config(fixed_value=True, value="Hello, World!")
ai_node = workflow.node("TextGenerationNode").config(
    template="Generate a creative response to: ((Input 1))",
    model_selection=["gpt-4o-mini"],
    temperature=0.7
)
output_node = workflow.node("OutputNode")

# Connect nodes together (from output to input)
workflow.link(input_node.output(), ai_node.input("variables", "Input 1"))
workflow.link(ai_node.output(), output_node.input())

# Save the workflow to Noxus
client = Client(api_key="your_api_key_here")
created_workflow = workflow.save(client)
print(f"Created workflow with ID: {created_workflow.data.id}")
```

For more complex workflows, you can also chain multiple nodes more easily:

```python
# Create a workflow for processing and analyzing text
workflow = WorkflowDefinition(name="Text Processing Pipeline")

# Add nodes in sequence
input_node = workflow.node("InputNode")
text_splitter = workflow.node("TextSplitterNode").config(chunk_size=1000, overlap=100)
sentiment_analyzer = workflow.node("SentimentAnalysisNode")
summarizer = workflow.node("TextSummarizationNode").config(max_length=150)
output_node = workflow.node("OutputNode")

# Create a branched workflow with multiple paths
workflow.link(input_node.output(), text_splitter.input())
workflow.link(text_splitter.output(), sentiment_analyzer.input())
workflow.link(text_splitter.output(), summarizer.input())
workflow.link(sentiment_analyzer.output(), output_node.input("sentiment"))
workflow.link(summarizer.output(), output_node.input("summary"))

# Save the workflow
workflow.save(client)
```

You can also check for existing workflows and update them if needed:

```python
# Get a list of existing workflows
existing_workflows = {w.data.name: w.data.id for w in client.workflows.list()}

# Create or update a workflow
workflow = WorkflowDefinition(name="My Workflow")
# ... add nodes and connections ...

if workflow.name in existing_workflows:
    # Update existing workflow
    workflow_id = existing_workflows[workflow.name]
    workflow.update_workflow(workflow_id, client, force=True)
    print(f"Updated workflow {workflow.name}")
else:
    # Create new workflow
    result = workflow.save(client)
    print(f"Created new workflow with ID: {result.data.id}")
```

#### Node Configuration

Each node type has specific configuration options that can be set using the `config()` method:

```python
# Configure an input node with a fixed value
input_node = workflow.node("InputNode").config(
    fixed_value=True, 
    value="This is a fixed input"
)

# Configure a text generation node with specific parameters
generation_node = workflow.node("TextGenerationNode").config(
    template="Write a summary about ((Input 1))",
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=250,
    extra_instructions="Keep the summary concise and informative."
)

# Configure a code execution node
code_node = workflow.node("CodeExecutionNode").config(
    language="python",
    code="def process(input_text):\n    return input_text.upper()",
    timeout=30
)
```

#### Connecting Nodes

Nodes are connected through their inputs and outputs, creating a directed graph:

```python
# Basic connection from output to input
workflow.link(node_a.output(), node_b.input())

# Connection with named inputs/outputs
workflow.link(node_a.output("result"), node_b.input("data"))

# Connection with variable inputs (using key)
workflow.link(node_a.output(), node_b.input("variables", "Input 1"))

# Creating multiple connections at once for simple linear flows
workflow.link_many(node_a, node_b, node_c, node_d)
```

The `link_many()` method is a convenience function for creating a linear chain of nodes, but it only works for nodes with a single input and output.

### Conversations

Conversations represent chat interactions with AI models. They provide a way to configure and manage chat sessions:

```python
from noxus_sdk.resources.conversations import ConversationSettings, ConversationTool

# Define a conversation tool (optional)
tool = ConversationTool(
    name="example_tool",
    description="An example tool",
    enabled=True,
    type="function"
)

# Define conversation settings
settings = ConversationSettings(
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[tool],
    extra_instructions="Please be concise."
)

# Create a new conversation
conversation = client.conversations.create(name="Example Conversation", settings=settings)
print(f"Created Conversation ID: {conversation.id}")

# List all conversations
conversations = client.conversations.list(page=1, page_size=10)
for conv in conversations:
    print(f"Conversation ID: {conv.id}, Name: {conv.name}")

# Get a specific conversation
conversation = client.conversations.get(conversation_id="conversation_id_here")

# Update a conversation
updated_conversation = client.conversations.update(
    conversation_id="conversation_id_here",
    name="Updated Conversation",
    settings=settings
)

# Delete a conversation
client.conversations.delete(conversation_id="conversation_id_here")
```

The `ConversationSettings` class allows you to configure model parameters like temperature and token limits, as well as specify tools the conversation can use.

### Agents

Agents are autonomous AI assistants that can perform tasks with specific configurations:

```python
from noxus_sdk.resources.assistants import AgentSettings, AgentTool

# Define agent tool
tool = AgentTool(
    name="example_tool",
    description="An example tool",
    definition={},
    enabled=True,
    type="function"
)

# Define agent settings
agent_settings = AgentSettings(
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[tool],
    extra_instructions="Please be helpful and concise."
)

# Create a new agent
agent = client.agents.create(name="Example Agent", settings=agent_settings)
print(f"Created Agent ID: {agent.id}")

# List all agents
agents = client.agents.list()
for agent in agents:
    print(f"Agent ID: {agent.id}, Name: {agent.name}")

# Get a specific agent
agent = client.agents.get(agent_id="agent_id_here")

# Update an agent
updated_agent = client.agents.update(
    agent_id="agent_id_here",
    name="Updated Agent Name",
    settings=agent_settings
)

# Delete an agent
client.agents.delete(agent_id="agent_id_here")

# Update and delete using the agent instance
agent = client.agents.get(agent_id="agent_id_here")
agent.update(name="New Name", settings=agent_settings)
agent.delete()
```

Agents can be configured with specific tools and parameters to customize their behavior for different use cases.

### Knowledge Bases

Knowledge bases allow you to store and retrieve information that the AI can use to enhance its responses:

```python
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
    KnowledgeBaseHybridSettings
)

# Define knowledge base components
ingestion = KnowledgeBaseIngestion(
    batch_size=10,
    default_chunk_size=1000,
    default_chunk_overlap=200,
    enrich_chunks_mode="auto",
    enrich_pre_made_qa=True,
    methods={}
)

hybrid_settings = KnowledgeBaseHybridSettings(fts_weight=0.5)
retrieval = KnowledgeBaseRetrieval(
    type="hybrid",
    hybrid_settings=hybrid_settings.model_dump(),
    reranker_settings={}
)

# Define complete knowledge base settings
kb_settings = KnowledgeBaseSettings(
    allowed_sources=["pdf", "txt", "doc"],
    ingestion=ingestion,
    retrieval=retrieval,
    embeddings={}
)

# Create a new knowledge base
knowledge_base = client.knowledge_bases.create(
    name="Example Knowledge Base",
    description="A sample knowledge base",
    document_types=["article", "report"],
    settings_=kb_settings
)
print(f"Created Knowledge Base ID: {knowledge_base.id}")

# List all knowledge bases
knowledge_bases = client.knowledge_bases.list(page=1, page_size=10)
for kb in knowledge_bases:
    print(f"Knowledge Base ID: {kb.id}, Name: {kb.name}")

# Get a specific knowledge base
kb = client.knowledge_bases.get(knowledge_base_id="kb_id_here")
```

The ingestion settings control how documents are processed, while the retrieval settings determine how information is retrieved from the knowledge base.

## Advanced Usage

These examples demonstrate more sophisticated ways to use the SDK for advanced scenarios.

### Asynchronous Operations

The SDK supports asynchronous operations for improved performance in I/O-bound tasks. Here's an example of using asynchronous methods:

```python
import asyncio
from noxus_sdk.client import Client

async def main():
    client = Client(api_key="your_api_key_here")
    
    # List workflows asynchronously
    workflows = await client.workflows.alist()
    for workflow in workflows:
        print(workflow.name)
    
    # Create and run a knowledge base asynchronously
    kb_settings = KnowledgeBaseSettings(
        allowed_sources=["pdf"],
        ingestion={},
        retrieval={},
        embeddings={}
    )
    kb = await client.knowledge_bases.acreate(
        name="Async KB",
        description="Created asynchronously",
        document_types=["report"],
        settings_=kb_settings
    )
    
    # Run a workflow and wait for completion asynchronously
    workflow = await client.workflows.aget("workflow_id")
    run = await workflow.arun({"input": "value"})
    result = await run.a_wait(interval=2)

asyncio.run(main())
```

Asynchronous methods are prefixed with `a` (like `alist`, `arefresh`, `arun`), making it easy to identify them.

### Pagination

Most list operations support pagination. You can specify the `page` and `page_size` parameters to control the number of items returned:

```python
# Get the first 10 items
first_page = client.workflows.list(page=1, page_size=10)

# Get the next 10 items
second_page = client.workflows.list(page=2, page_size=10)

# Use a larger page size
large_page = client.conversations.list(page=1, page_size=50)
```

Pagination helps you manage large sets of data efficiently by retrieving only what you need.

## Troubleshooting

Here are solutions to common issues you might encounter:

- **Connection Issues**: Ensure your network connection is stable and the `NOXUS_BACKEND_URL` environment variable is correctly set if using a custom backend.
- **Authentication Errors**: Verify that your API key is correct and has the necessary permissions.
- **Rate Limiting**: If you encounter rate limiting, implement exponential backoff and retry logic in your code.
- **Timeout Errors**: For long-running operations, consider using asynchronous methods or increasing the client timeout.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any questions or issues, please contact support@noxus.ai.

## Additional Resources

- [Noxus AI Documentation](https://docs.noxus.ai)
- [GitHub Repository](https://github.com/noxus-ai/noxus-client-sdk)