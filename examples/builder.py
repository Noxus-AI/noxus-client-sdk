import os
from noxus_sdk.workflows import WorkflowDefinition
from noxus_sdk.client import Client

api_key = os.getenv("NOXUS_API_KEY")
if api_key is None:
    raise ValueError("NOXUS_API_KEY environment variable is not set")

# Initialize client with API key
client = Client(api_key)

existing_workflows = {w.name: w.id for w in client.workflows.list()}

# Create a new workflow for generating cheese poems
workflow = WorkflowDefinition(name="🧀 Poem")

# Set up input node with a fixed value "cheese"
input = workflow.node("InputNode").config(fixed_value=True, value="cheese")

# Configure AI text generation node with a template
ai = workflow.node("TextGenerationNode").config(
    template="Write a poem about ((Input 1))"
)

# Add output node to capture the generated poem
output = workflow.node("OutputNode")

# Connect the nodes: input -> AI -> output
workflow.link(input.output(), ai.input("variables", "Input 1"))
workflow.link(ai.output(), output.input())

# Save or update the workflow
if "Noxus Poem" not in existing_workflows:
    workflow_id = client.workflows.save(workflow).id
else:
    workflow_id = existing_workflows["Noxus Poem"]

# Update the input to use "Noxus AI" instead of "cheese"
input = workflow.node("InputNode").config(fixed_value=True, value="Noxus AI")

# Rename the workflow
workflow.name = "Noxus Poem"

# Update the existing workflow with the new configuration
client.workflows.update(workflow_id, workflow)
