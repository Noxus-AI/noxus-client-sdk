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
    model=["gpt-4o-mini"],
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

#### Building Workflows

The SDK provides a powerful programmatic way to build complex workflows by connecting different nodes together. To define a structure you can use the `WorkflowDefinition` class, as in the example below:

```python
from noxus_sdk.workflows import WorkflowDefinition

# Create a new workflow definition
workflow_def = WorkflowDefinition(name="Simple Workflow")

# Add nodes to the workflow
input_node = workflow_def.node("InputNode").config(label="Fixed Input", fixed_value=True, value="Write a joke.", type="str")
ai_node = workflow_def.node("TextGenerationNode").config(
    template="Please insert a fact about an animal after fulfilling the following request: ((Input 1))",
    model=["gpt-4o-mini"],
)
output_node = workflow_def.node("OutputNode")

# Connect nodes together (from output to input)
workflow_def.link(input_node.output(), ai_node.input("variables", "Input 1"))
workflow_def.link(ai_node.output(), output_node.input())

# Save the workflow to Noxus
simple_workflow = client.workflows.save(workflow_def)
print(f"Created workflow with ID: {simple_workflow.id}")
```

A workflow is a graph and does not need to be linear. You can add more nodes and chain them however you like, as long as the connections are valid (a string input expects a string value, a file input expects a file, etc):

```python
from noxus_sdk.workflows import WorkflowDefinition

# Create a workflow for summarizing and analyzing text
workflow_def = WorkflowDefinition(name="Complex Workflow")

# Add nodes in sequence
input_node = workflow_def.node("InputNode")
text_generator = workflow_def.node("TextGenerationNode").config(template="Write an essay on ((Input 1)).")
summarizer = workflow_def.node("SummaryNode").config(summary_format="Concise", summary_topic="Summarize the essay in around 300 words.")
compose = workflow_def.node("ComposeTextNode").config(template="Summary: \n\n ((Input 1)) \n\n Extended text: \n ((Input 2))")
output = workflow_def.node("OutputNode")

# Create a branched workflow with multiple paths
workflow_def.link(input_node.output(), text_generator.input("variables", key="Input 1"))
workflow_def.link(text_generator.output(), summarizer.input())
workflow_def.link(summarizer.output(), compose.input("variables", key="Input 1"))
workflow_def.link(text_generator.output(), compose.input("variables", key="Input 2"))
workflow_def.link(compose.output(), output.input())

# Save the workflow
complex_workflow = client.workflows.save(workflow_def)
print(f"Created workflow with ID: {complex_workflow.id}")
```

> 💡 **Tip**
>
> Nodes with variable inputs must be set with the "variables" key. E.g. `node.input("variables", key="Input 1")`.

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

#### Updating Workflows

You can also update existing workflows if needed. Let's update the `Complex Workflow` from the example above:

```python
#We fetch the workflow to update
workflow_to_update = client.workflows.get(workflow_id="workflow_id_here")

# Update existing workflow name
workflow_to_update.name = "Essay Writer"

# Let's add an extra input with the author of the workflow
author_input = workflow_to_update.node("InputNode").config(label="Author", fixed_value=True, value="John Peter Table", type="str")
# We update the compose node config and connection (notice how we use the label)
compose = [w for w in workflow_to_update.nodes if w.type == "ComposeTextNode"][0]
compose.config(
    template="Summary: \n\n ((Input 1)) \n\n Extended text: \n ((Input 2)) \n\n Author: ((Author))",
)
workflow_to_update.link(
    author_input.output("output"), compose.input("variables", "Author")
)

# Update the workflow
updated_workflow = client.workflows.update(workflow_to_update.id, workflow_to_update)
print(f"Updated workflow {updated_workflow.name}")
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
```

#### Listing Runs

```python
# Get a list of workflow runs
runs = client.runs.list(workflow_id="workflow_id_here", page=1, page_size=10)
```

The `wait()` method allows you to block until the workflow completes, making it easy to handle workflow execution in a synchronous manner. You can adjust the polling interval as needed.

> 💡 **Tip**
>
> The `input_key` can be:
>
> - `{node_label}`. You can define it on the config of a node when creating it.
> - `{node_input_id}`. You can fetch it by doing something like `node.inputs[0].id`.
> - `{node_id}::{input_name}`. For an **Input Node** the default `input_name` is `input`.

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

### Knowledge Bases

Knowledge bases allow you to store and retrieve information. They can be used by other Noxus resources like Workflows or Agents:

#### Creating a Knowledge Base

```python
from noxus_sdk.resources.knowledge_bases import (
    KnowledgeBaseSettings,
    KnowledgeBaseIngestion,
    KnowledgeBaseRetrieval,
    KnowledgeBaseHybridSettings
)

# Define knowledge base components
settings = KnowledgeBaseSettings(
    ingestion=KnowledgeBaseIngestion(
        batch_size=10,
        default_chunk_size=1000,
        default_chunk_overlap=200,
        enrich_chunks_mode="contextual",
        enrich_pre_made_qa=False,
    ),
    retrieval=KnowledgeBaseRetrieval(
        type="hybrid_reranking",
        hybrid_settings={"fts_weight": 0.3},
        reranker_settings={}
    ),
)


# Create a new knowledge base
knowledge_base = client.knowledge_bases.create(
    name="Example Knowledge Base",
    description="A sample knowledge base",
    document_types=["pdf", "txt"],
    settings_=kb_settings
)
print(f"Created Knowledge Base ID: {knowledge_base.id}")
```

The ingestion settings control how documents are processed, while the retrieval settings determine how information is retrieved from the knowledge base.

#### Listing Knowledge Bases

```python
# List all knowledge bases
knowledge_bases = client.knowledge_bases.list(page=1, page_size=10)
for kb in knowledge_bases:
    print(f"Knowledge Base ID: {kb.id}, Name: {kb.name}")

# Get a specific knowledge base
kb = client.knowledge_bases.get(knowledge_base_id="your_kb_id")
```

#### More Knowledge Base Operations

```python
from noxus_sdk.resources.knowledge_bases import (
    UpdateDocument,
    DocumentStatus,
    RunStatus,
    File,
    Source,
    DocumentSource,
    DocumentSourceConfig,
    UpdateDocument
)

#Get the knowledge base
kb = client.knowledge_bases.get(knowledge_base_id="your_kb_id")

#Add a file (this process will take some time until the file is available)
run_ids = kb.upload_document(
    files=["notebook_kb_test.txt"],
    prefix="/files" #Where it will be stored on the KB
)
print(f"Upload started with run IDs: {run_ids}")

# We can also monitor these runs
print("\n=== Checking Runs ===")
runs = kb.get_runs(status="running")
print(f"Active runs: {len(runs)}")

# List documents
print("\n=== Listing Documents ===")
documents = kb.list_documents(status="trained")
for doc in documents:
    print(f"Document: {doc.name} (Status: {doc.status})")

# Get and update a document if any exist
if documents:
    doc = kb.get_document(documents[0].id)
    print(f"\nGot document: {doc.name}")

    updated_doc = kb.update_document(
        doc.id,
        UpdateDocument(prefix="/updated/path")
    )
    print(f"Updated document prefix to: {updated_doc.prefix}")

# Refresh KB to see latest status
kb.refresh()
print(f"\nKB status: {kb.status}")
print(f"Total documents: {kb.total_documents}")
print(f"Trained documents: {kb.trained_documents}")
print(f"Error documents: {kb.error_documents}")

# List all knowledge bases
print("\n=== All Knowledge Bases ===")
knowledge_bases = client.knowledge_bases.list(page=1, page_size=10)
for kb in knowledge_bases:
    print(f"KB: {kb.name} (ID: {kb.id})")

# Cleanup
print("\n=== Cleanup ===")
if documents:
    for doc in documents:
        kb.delete_document(doc.id)
        print(f"Deleted document: {doc.name}")

success = kb.delete()
print(f"Knowledge base deletion: {'successful' if success else 'failed'}")
```

<br>

### Conversations

Conversations represent chat interactions with AI models. Besides their base configuration, they can be augmented to use different tools.

#### Creating a Conversation

```python
from noxus_sdk.resources.conversations import (
    ConversationSettings,
    MessageRequest,
    WebResearchTool,
)

# Create conversation tools
web_research_tool = WebResearchTool(
    enabled=True,
    extra_instructions="Focus on recent and reliable sources."
)

# Define conversation settings
settings = ConversationSettings(
    model=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[web_research_tool],
    extra_instructions="Please be concise."
)

# Create a new conversation
conversation = client.conversations.create(name="Example Conversation", settings=settings)
print(f"Created Conversation ID: {conversation.id}")
```

#### Listing Conversations

```python
# List all conversations
conversations = client.conversations.list(page=1, page_size=10)
for conv in conversations:
    print(f"Conversation ID: {conv.id}, Name: {conv.name}")

# Get a specific conversation
conversation = client.conversations.get(conversation_id="conversation_id_here")
```

#### Sending Messages in a Conversation

Once you have a conversation, you can add messages to it and get the AI's response:

```python
import base64
from noxus_sdk.resources.conversations import MessageRequest, ConversationFile

# Simple message without using any tools
message = MessageRequest(content="How are you?")
response = conversation.add_message(message)
print(f"AI Response: {response.message_parts} \n\n")

# Message using web research tool
web_research_message = MessageRequest(
    content="What is the wordle word of yesterday?",
    tool="web_research"
)
response = conversation.add_message(web_research_message)
print(f"Web Research Tool response: {response.message_parts} \n\n")

# Message with attached files
file = ConversationFile(
    name="test.txt",
    status="success",
    b64_content=base64.b64encode(b"Hello, world!").decode("utf-8"),
)
message = MessageRequest(content="What does the file say?", files=[file])
response = conversation.add_message(message)
print(f"Message with file response: {response.message_parts} \n\n")
```

We can also get all messages in a single conversation:

```python
# Get all messages in a conversation
all_messages = conversation.get_messages()
for msg in all_messages:
    print(f"Message ID: {msg.id}, Created: {msg.created_at}")
```

#### Deleting a Conversation

```python
# Delete a conversation
client.conversations.delete(conversation_id="conversation_id_here")
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
> Asynchronous methods are prefixed with `a` (like `add_message`, `arefresh`, `aget_messages`), making it easy to identify them.

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
    workflow={"id": "your_workflow_id", "name": "Workflow Name", "description": "Workflow Description"},
    name="Data Analysis Workflow",
    description="Run the data analysis workflow on provided input"
)

# Create settings with all tools
settings = ConversationSettings(
    model=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[web_tool, noxus_qa_tool, kb_selector_tool, kb_qa_tool, workflow_tool],
    extra_instructions="Use the most appropriate tool for each query."
)

conversation = client.conversations.create(name="Tooljacked Conversation", settings=settings)
```

### Agents (also known as Co-workers)

Agents (Co-Workers) are autonomous AI assistants that can perform tasks with specific configurations.
Agents use the same tools as conversations:

#### Creating an Agent

```python
from noxus_sdk.resources.conversations import WebResearchTool
from noxus_sdk.resources.conversations import WorkflowTool
from noxus_sdk.resources.conversations import ConversationSettings

# Workflow execution tool
workflow_tool = WorkflowTool(
    enabled=True,
    workflow={"id": "workflow_id", "name":"name for workflow", "description": "description for workflow"},
    name="Name for workflow",
    description="Description for workflow"
)


# Define agent settings
agent_settings = ConversationSettings(
    model=["gpt-4o-mini"],
    temperature=0.7,
    max_tokens=150,
    tools=[workflow_tool],
    extra_instructions="Please be helpful and concise."
)

# Create a new agent
agent = client.agents.create(name="Example Agent", settings=agent_settings)
print(f"Created Agent with ID: {agent.id}, and name: {agent.name}")
```

#### Listing Agents

```python
# List all agents
agents = client.agents.list()
for agent in agents:
    print(f"Agent ID: {agent.id}, Name: {agent.name}")

# Get a specific agent
agent = client.agents.get(agent_id="agent_id_here")
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
agent = client.agents.get(agent_id="agent_id")

# Create a conversation with this agent
conversation = client.conversations.create(
    name="Chat with Agent",
    agent_id=agent.id
)

# Now you can send messages to the conversation
message = MessageRequest(content="Hello, what model are you using?")
response = conversation.add_message(message)
print(f"Agent Response: {response.message_parts}")

# You can ask it to run a workflow. Assume we add provided the agent with the Simple Workflow created above
message = MessageRequest(content="Hello, can you run Simple Workflow and tell it to tell a joke?")
response = conversation.add_message(message)
print(f"Agent Response: {response.message_parts}")
```

You can also create a conversation with the agent asynchronously

```python
async def create_agent_conversation():
    agent = await client.agents.aget(agent_id="agent_id")
    conversation = await client.conversations.acreate(
        name="Async Agent Chat",
        agent_id=agent.id
    )
    return conversation
```

> 💡 **Tip**
>
> When providing an `agent_id` to a **Conversation**, you don't need to provide settings. With this approach, the agent's settings, tools, and capabilities are automatically applied to the conversation without needing to specify them manually

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
    kb = await client.knowledge_bases.acreate(
        name="Async KB",
        description="Created asynchronously",
        document_types=["report"],
        settings_=kb_settings # Using a settings object like defined above
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
    model=[model_names[0]],  # Use the first available model
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
