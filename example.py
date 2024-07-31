#!/usr/bin/env python3
import os, sys
from spot import Client

c = Client(os.getenv("SPOT_API_KEY"))
workflows = c.list_workflows()
print(f"Workflow: {workflows[0].data.id} -> {workflows[0].inputs[0].node_config.label}")
input(f"Run: {workflows[0].data.name} (press enter)")
o = workflows[0].run({workflows[0].inputs[0].id: sys.argv[1]})
print(f"Started run... {o.data['id']}")
print(o.wait())
