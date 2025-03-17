import os
from noxus_sdk.workflows import Workflow
from noxus_sdk.client import Client

client = Client(os.getenv("NOXUS_API_KEY"))

workflow = Workflow(name="🧀 Poem")
input = workflow.node("InputNode").config(fixed_value=True, value="cheese")
ai = workflow.node("TextGenerationNode").config(
    template="Write a poem about ((Input 1))"
)
output = workflow.node("OutputNode")
workflow.link(input.output(), ai.input("variables", "Input 1"))
workflow.link(ai.output(), output.input())

workflow.save(client)
