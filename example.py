#!/usr/bin/env python3
import os
from spot import Client

c = Client(os.getenv("SPOT_API_KEY"))
workflows = c.list_workflows()
input(f"Run: {workflows[0].data.name} (press enter)")
workflows[0].run({})
