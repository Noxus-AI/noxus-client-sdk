import os
from noxus_sdk.workflows import Workflow
from noxus_sdk.client import Client

client = Client(os.getenv("NOXUS_API_KEY"))
existing_workflows = {w.data.name: w.data.id for w in client.list_workflows()}
workflow = Workflow(name="🧀 Poem")
input = workflow.node("InputNode").config(fixed_value=True, value="cheese")
ai = workflow.node("TextGenerationNode").config(
    template="Write a poem about ((Input 1))"
)
output = workflow.node("OutputNode")
workflow.link(input.output(), ai.input("variables", "Input 1"))
workflow.link(ai.output(), output.input())

if "Noxus Poem" not in existing_workflows:
    workflow_id = workflow.save(client).data.id
else:
    workflow_id = existing_workflows["Noxus Poem"]
input = workflow.node("InputNode").config(fixed_value=True, value="Noxus AI")
workflow.name = "Noxus Poem"
workflow.update_workflow(workflow_id, client)
