#!/usr/bin/env python3
import os, sys, json
from spotsdk import Client

c = Client(os.getenv("SPOT_API_KEY"))
workflows = c.list_workflows()
workflow = [w for w in workflows if w.data.name == "sanity test"][0]
print(f"Workflow: {workflows[0].data.id} -> {workflows[0].inputs[0].node_config.label}")
workflow_run = workflows[0].run({f"{workflows[0].inputs[0].id}::input": sys.argv[1]})
print(f"Started run... {workflow_run.data['id']}")
result = workflow_run.wait()
listings = []

# Assumes output is a list of JSON strings
for output, listing_strings in result.items():
    for listing in listing_strings:
        listing = listing.replace("```json", "").replace("```", "")
        listings.append(json.loads(listing))

print(f"Wrote {len(listings)} listings to listing.json")
with open("listing.json", "w") as f:
    json.dump(listings, f, indent=2)
