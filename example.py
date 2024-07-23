#!/usr/bin/env python3
import os
from spot import Client

c = Client(os.getenv("SPOT_API_KEY"))
c.list_workflows()
