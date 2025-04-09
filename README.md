# noxus-client-sdk

## Overview

The `noxus-client-sdk` is a Python library designed to interact with the Noxus AI backend. It provides a convenient interface for managing workflows, conversations, knowledge bases, agents, and more. This SDK abstracts away the complexity of direct API calls, allowing developers to focus on building applications rather than managing HTTP requests.

## Installation

To install the SDK, run the following command in the root directory of the project:

```bash
pip install .
```

The SDK requires Python 3.8 or later and automatically installs all necessary dependencies.

## Startup

### Client Initialization

The client is your entry point to all SDK functionality. All you need is your API key:

```python
from noxus_sdk.client import Client

# Initialize the client with your API key
client = Client(api_key="your_api_key_here")
```

You can also specify a custom backend URL if needed by setting the `NOXUS_BACKEND_URL` environment variable or passing the `base_url` parameter to the `Client` constructor.

<br>

> 💡 **Tip**
>
> You can create an API key on the Noxus platform by going to the `API Keys` tab on the settings of your workspace of choice. You can find these settings by going to `Settings -> Organization -> Workspaces`, and selecting a workspace.

### Quick Example

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

## Usage

Below we provide detailed examples for working with various Noxus resources. Each example demonstrates the common operations (list, get, create, use, update, delete) for that resource type.

### Workflows

Workflows allow you to define complex sequences of operations that can be executed on demand. They are built with `nodes` (functional and logical blocks) connected through `edges` to form a Graph. Each `node` has its own configuration that defines how it will be executed.

#### Listing Workflows

```python
# List all workflows
workflows = client.workflows.list(page=1, page_size=10)
for workflow in workflows:
    print(f"Workflow ID: {workflow.id}, Name: {workflow.name}")

# Get a specific workflow
workflow = client.workflows.get(workflow_id="workflow_id_here")
print(f"Workflow ID: {workflow.id}, Name: {workflow.name}")
```

#### Building Workflows

The SDK provides a powerful programmatic way to build complex workflows by connecting different nodes together:

```python
from noxus_sdk.workflows import WorkflowDefinition

# Create a new workflow definition
workflow = WorkflowDefinition(name="Simple Workflow")

# Add nodes to the workflow
input_node = workflow.node("InputNode").config(label="Fixed Input", fixed_value=True, value="Write a joke.", type="str")
ai_node = workflow.node("TextGenerationNode").config(
    template="Please insert a fact about an animal after fulfilling the following request: ((Input 1))",
    model=["gpt-4o-mini"],
)
output_node = workflow.node("OutputNode")

# Connect nodes together (from output to input)
workflow.link(input_node.output(), ai_node.input("variables", "Input 1"))
workflow.link(ai_node.output(), output_node.input())

# Save the workflow to Noxus
#client = Client(api_key="your_api_key_here")
simple_workflow = workflow.save(client)
print(f"Created workflow with ID: {simple_workflow.id}")
```

For more complex workflows, you can also chain multiple nodes more easily:

```python
from noxus_sdk.workflows import WorkflowDefinition

# Create a workflow for writitng and summarizing an essay
workflow = WorkflowDefinition(name="Complex Workflow")

# Add nodes in sequence
input_node = workflow.node("InputNode")
text_generator = workflow.node("TextGenerationNode").config(template="Write an essay on ((Input 1)).")
summarizer = workflow.node("SummaryNode").config(summary_format="Concise", summary_topic="Summarize the essay in around 300 words.")
combiner = workflow.node("ComposeTextNode").config(template="Summary: \n\n ((Input 1)) \n\n Extended text: \n ((Input 2))")

output = workflow.node("OutputNode")

# Create a branched workflow with multiple paths
workflow.link(input_node.output(), text_generator.input("variables", key="Input 1"))
workflow.link(text_generator.output(), summarizer.input())
workflow.link(summarizer.output(), combiner.input("variables", key="Input 1"))
workflow.link(text_generator.output(), combiner.input("variables", key="Input 2"))
workflow.link(combiner.output(), output.input())

# Save the workflow
complex_workflow = workflow.save(client)
print(f"Created workflow with ID: {complex_workflow.id}")
```

#### Updating Workflows

You can also update existing workflows if needed. Let's update the `Complex Workflow` from the example above:

```python
print(f"Updating workflow '{complex_workflow.name}' with ID: {complex_workflow.id}")

# Update existing workflow name
complex_workflow.name = "Essay Writer"

# Let's add an extra input with the author of the workflow
input_node = complex_workflow.node("InputNode").config(label="Author", fixed_value=True, value="John Peter Table", type="str")
  workflow_def.link(
        input_node3.output("output"), combine_node.input("variables", "Input 3")
    )

# Update the workflow
client.workflows.update(complex_workflow.id, complex_workflow)
print(f"Updated workflow {complex_workflow.name}")
```

#### Running Workflows

Once you have a workflow, you can execute it and retrieve the results:

```python
workflow = client.workflows.get(workflow_id="workflow_id_here")

# Run a workflow (If the input is fixed, it will be overridden)
run = workflow.run(body={"input_key": "input_value"})

# Run a workflow with no inputs or fixed inputs
run = workflow.run(body={})


# Wait for the workflow to complete
result = run.wait(interval=5)
print(f"Run status: {result.status}")
print(f"Output: {result.output}")

# Get a list of workflow runs
runs = client.runs.list(workflow_id="workflow_id_here", page=1, page_size=10)
```

The `wait()` method allows you to block until the workflow completes, making it easy to handle workflow execution in a synchronous manner. You can adjust the polling interval as needed.

> 💡 **Tip**
>
> The `input_key` can take two formats:
>
> - `{node_id}::{input_name}`. For an **Input Node** the `input_name` is `input`
> - `{node_id}::{input_name}`. For an **Input Node** the `input_name` is `input`

<br>

### Workflows Basics

#### Node Configuration

Each node type has specific configuration options that can be set using the `config()` method:

```python
# Configure an input node with a fixed value
input_node = workflow.node("InputNode").config(
    label="Input 1",
    fixed_value=True,
    value="This is a fixed input"
)

# Configure a text generation node with specific parameters
generation_node = workflow.node("TextGenerationNode").config(
    template="Write a summary about ((Input 1))",
    model=["gpt-4o-mini"],
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

<br>

### Conversations

Conversations represent chat interactions with AI models. Besides their base configuration, they can be augmented to use different tools.

#### Listing Conversations

```python
# List all conversations
conversations = client.conversations.list(page=1, page_size=10)
for conv in conversations:
    print(f"Conversation ID: {conv.id}, Name: {conv.name}")

# Get a specific conversation
conversation = client.conversations.get(conversation_id="conversation_id_here")
```

#### Creating a Conversation

```python
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    MessageRequest,
    WebResearchTool,
    KnowledgeBaseQaTool
)

# Create conversation tools
web_research_tool = WebResearchTool(
    enabled=True,
    extra_instructions="Focus on recent and reliable sources."
)

kb_qa_tool = KnowledgeBaseQaTool(
    enabled=True,
    kb_id="knowledge_base_uuid_here",
    extra_instructions="Reference specific sections when possible."
)

# Define conversation settings
settings = ConversationSettings(
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[web_research_tool, kb_qa_tool],
    extra_instructions="Please be concise."
)

# Create a new conversation
conversation = client.conversations.create(name="Example Conversation", settings=settings)
print(f"Created Conversation ID: {conversation.id}")
```

#### Deleting a Conversation

```python
# Delete a conversation
client.conversations.delete(conversation_id="conversation_id_here")
```

#### Sending Messages in a Conversation

Once you have a conversation, you can add messages to it and get the AI's response:

```python
from noxus_sdk.resources.conversations import MessageRequest, ConversationFile

# Simple message without using any tools
message = MessageRequest(content="Tell me about machine learning")
response = conversation.add_message(message)
print(f"AI Response: {response.message_parts} \n\n")

# Message using web research tool
web_research_message = MessageRequest(
    content="What are the latest advancements in quantum computing?",
    tool="web_research"
)
response = conversation.add_message(web_research_message)
print(f"Web Research Tool response: {response.message_parts} \n\n")

# Message with knowledge base query
kb_message = MessageRequest(
    content="What does our documentation say about API keys?",
    tool="kb_qa",
    kb_id="knowledge_base_uuid_here"
)
response = conversation.add_message(kb_message)
print(f"Knowledge Base response: {response.message_parts} \n\n")

# Message with attached files
file = ConversationFile(
    name="Eurasian_wolf_2.jpg",
    url="https://en.wikipedia.org/wiki/Wolf#/media/File:Eurasian_wolf_2.jpg"
)
file_message = MessageRequest(
    content="Describe the provided image",
    files=[file]
)
response = conversation.add_message(file_message)
print(f"File response: {response.message_parts} \n\n")
```

We can also get all messages in a single conversation:

```python
# Get all messages in a conversation
all_messages = conversation.get_messages()
for msg in all_messages:
    print(f"Message ID: {msg.id}, Created: {msg.created_at}")
```

#### Asynchronous Conversation Operations

For applications that need non-blocking operations:

```python
import asyncio

async def conversation_example():
    # Create a conversation asynchronously
    conversation = await client.conversations.acreate(name="Async Example", settings=settings)

    # Send a message and get response asynchronously
    message = MessageRequest(content="How does quantum computing work?")
    response = await conversation.aadd_message(message)

    # Refresh the conversation to get latest state
    updated_conversation = await conversation.arefresh()

    # Get all messages
    messages = await updated_conversation.aget_messages()
    return messages

# Run the async function
messages = asyncio.run(conversation_example())
```

> 💡 **Tip**
>
> Notice the extra `a` in the methods above for **async**.

#### Available Conversation Tools

The SDK supports various specialized tools that can be enabled in conversations:

```python
from noxus_sdk.resources.conversations import (
    WebResearchTool,
    NoxusQaTool,
    KnowledgeBaseSelectorTool,
    KnowledgeBaseQaTool,
    WorkflowTool
)

# Web research tool
web_tool = WebResearchTool(
    enabled=True,
    extra_instructions="Focus on academic sources"
)

# Noxus Q&A tool
noxus_qa_tool = NoxusQaTool(
    enabled=True,
    extra_instructions="Explain Noxus features in simple terms"
)

# Knowledge base selector tool
kb_selector_tool = KnowledgeBaseSelectorTool(
    enabled=True,
    extra_instructions="Choose the most relevant knowledge base"
)

# Knowledge base Q&A tool with specific KB
kb_qa_tool = KnowledgeBaseQaTool(
    enabled=True,
    kb_id="knowledge_base_uuid_here",
    extra_instructions="Provide detailed answers from the knowledge base"
)

# Workflow execution tool
workflow_tool = WorkflowTool(
    enabled=True,
    workflow_id="workflow_uuid_here",
    name="Data Analysis Workflow",
    description="Run the data analysis workflow on provided input"
)

# Create settings with all tools
settings = ConversationSettings(
    model_selection=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[web_tool, noxus_qa_tool, kb_selector_tool, kb_qa_tool, workflow_tool],
    extra_instructions="Use the most appropriate tool for each query."
)
```

### Agents (also known as Co-workers)

Agents are autonomous AI assistants that can perform tasks with specific configurations.
Agents use the same tools as conversations:

#### Listing Agents

```python
# List all agents
agents = client.agents.list()
for agent in agents:
    print(f"Agent ID: {agent.id}, Name: {agent.name}")

# Get a specific agent
agent = client.agents.get(agent_id="agent_id_here")
```

#### Creating an Agent

```python
from noxus_sdk.resources.assistants import AgentSettings
from noxus_sdk.resources.conversations import WebResearchTool

# Define agent tool
tool = WebResearchTool(
    enabled=True,
    extra_instructions="Focus on academic sources"
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
```

#### Updating and Deleting an Agent

```python
# Update an agent
updated_agent = client.agents.update(
    agent_id="agent_id_here",
    name="Updated Agent Name",
    settings=agent_settings
)

# Delete an agent
client.agents.delete(agent_id="agent_id_here")
```

We can also update and delete using the agent instance

```python
agent = client.agents.get(agent_id="agent_id_here")
agent.update(name="New Name", settings=agent_settings)
agent.delete()
```

#### Starting Conversations with Agents

You can start a conversation with an agent using the `agent_id` parameter in the conversation creation process:

```python
# Get the agent you want to chat with
agent = client.agents.get(agent_id="agent_id_here")

# Create a conversation with this agent
conversation = client.conversations.create(
    name="Chat with Agent",
    agent_id=agent.id
)

# Now you can send messages to the conversation
message = MessageRequest(content="Hello, can you help me with something?")
response = conversation.add_message(message)
print(f"Agent Response: {response.message_parts}")
```

You can also create a conversation with the agent asynchronously

```python
async def create_agent_conversation():
    agent = await client.agents.aget(agent_id="agent_id_here")
    conversation = await client.conversations.acreate(
        name="Async Agent Chat",
        agent_id=agent.id
    )
    return conversation
```

> 💡 **Tip**
>
> When providing an `agent_id` to a conversation, you don't need to provide settings. With this approach, the agent's settings, tools, and capabilities are automatically applied to the conversation without needing to specify them manually

### Knowledge Bases

Knowledge bases allow you to store and retrieve information that the AI can use to enhance its responses:

#### Listing Knowledge Bases

```python
# List all knowledge bases
knowledge_bases = client.knowledge_bases.list(page=1, page_size=10)
for kb in knowledge_bases:
    print(f"Knowledge Base ID: {kb.id}, Name: {kb.name}")

# Get a specific knowledge base
kb = client.knowledge_bases.get(knowledge_base_id="kb_id_here")
```

#### Creating a Knowledge Base

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
    enrich_chunks_mode="inject_summary",
    enrich_pre_made_qa=True,
    methods={}
)

hybrid_settings = KnowledgeBaseHybridSettings(fts_weight=0.5)

retrieval = KnowledgeBaseRetrieval(
    type="hybrid_reranking",
    hybrid_settings=hybrid_settings.model_dump(),
    reranker_settings={}
)

# Define complete knowledge base settings
kb_settings = KnowledgeBaseSettings(
    allowed_sources=["Document", "Google Drive", "OneDrive"],
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

### Platform Information Methods

The SDK provides methods to retrieve information about the Noxus platform, including available nodes, models, and chat presets. These methods are available in both synchronous and asynchronous versions:

```python
from noxus_sdk.client import Client

client = Client(api_key="your_api_key_here")

# Get available workflow nodes
nodes = client.get_nodes()  # Synchronous
nodes = await client.aget_nodes()  # Asynchronous

# Get available language models
models = client.get_models()  # Synchronous
models = await client.aget_models()  # Asynchronous

# Get chat model presets
presets = client.get_chat_presets()  # Synchronous
presets = await client.aget_chat_presets()  # Asynchronous
```

These methods are particularly useful when you need to:

- List available node types for workflow construction
- Check which language models are available for your tasks
- Access predefined chat configuration presets

For example, you might use these methods when setting up a new workflow or configuring a conversation:

```python
# Get available models and use them in conversation settings
models = client.get_models()
model_names = [model["name"] for model in models]

settings = ConversationSettings(
    model_selection=[model_names[0]],  # Use the first available model
    temperature=0.7,
    max_tokens=150,
    tools=[],
    extra_instructions="Please be concise."
)

# Create a conversation with the retrieved model
conversation = client.conversations.create(
    name="Model-specific Conversation",
    settings=settings
)
```

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
