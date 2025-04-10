import os
from noxus_sdk import Client
from noxus_sdk.workflows import WorkflowDefinition

client = Client(os.environ["NOXUS_API_KEY"])

# STEP 1 create a combine text workflow
workflow_def = WorkflowDefinition(name="CombineText Testing")

# Add nodes to the workflow
input_node1 = workflow_def.node("InputNode")
input_node2 = workflow_def.node("InputNode")
combine_node = workflow_def.node("ComposeTextNode").config(
    template="((Input 1))\n\n((Input 2))",
)
output_node = workflow_def.node("OutputNode")

# Connect nodes together (from output to input)
workflow_def.link(
    input_node1.output("output"), combine_node.input("variables", "Input 1")
)
workflow_def.link(
    input_node2.output("output"), combine_node.input("variables", "Input 2")
)
workflow_def.link(combine_node.output(), output_node.input())
new_workflow = client.workflows.save(workflow_def)
run = new_workflow.run(
    body={input_node1.inputs[0].id: "test1", input_node2.inputs[0].id: "test2"}
)
output = run.wait(output_only=True)
data = output.get(output_node.outputs[0].id, {"text": ""})["text"]
assert "test1" in data
assert "test2" in data


# Step 2 update  it
workflow = [w for w in client.workflows.list() if w.name == "CombineText Testing"][0]

input3 = workflow.node("InputNode")
compose = [w for w in workflow.nodes if w.type == "ComposeTextNode"][0]
compose.config(
    template="((Input 1))\n\n((Input 2))\n\n((Input 3))",
)
workflow.link(input3.output("output"), compose.input("variables", "Input 3"))

# Step 3 save the updated workflow
updated_workflow = client.workflows.update(workflow.id, workflow)
run = updated_workflow.run(
    body={
        input_node1.inputs[0].id: "test1",
        input_node2.inputs[0].id: "test2",
        input3.inputs[0].id: "test3",
    }
)
output = run.wait(output_only=True)
data = output.get(output_node.outputs[0].id, {"text": ""})["text"]
assert "test1" in data
assert "test2" in data
assert "test3" in data
