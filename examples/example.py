#!/usr/bin/env python3
import os, sys, json
from noxus_sdk.client import Client

api_key = os.getenv("NOXUS_API_KEY")
if api_key is None:
    raise ValueError("NOXUS_API_KEY environment variable is not set")

c = Client(api_key)

# Get all available workflows
workflows = c.workflows.list()

# Find a specific workflow by name
workflow = [w for w in workflows if w.data.name == "sanity test"][0]

# Print information about the first workflow
print(f"Workflow: {workflows[0].data.id} -> {workflows[0].inputs[0].node_config.label}")

# Run the workflow with the command line argument as input
# The format "{input_id}::input" is used to specify which input node to send data to
workflow_run = workflows[0].run({f"{workflows[0].inputs[0].id}::input": sys.argv[1]})
print(f"Started run... {workflow_run.data['id']}")

# Wait for the workflow to complete and get the results
result = workflow_run.wait()
listings = []

# Process the output data
# Assumes output is a list of JSON strings
for output, listing_strings in result.items():
    for listing in listing_strings:
        listing = listing.replace("```json", "").replace("```", "")
        listings.append(json.loads(listing))

print(f"Wrote {len(listings)} listings to listing.json")
with open("listing.json", "w") as f:
    json.dump(listings, f, indent=2)
