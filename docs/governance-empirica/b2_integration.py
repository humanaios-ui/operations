#!/usr/bin/env python3
"""
B2.1 + B2.2 Integration: Query → Render → REGISTERED.md
Pipeline that reads B2.1 query output (JSON) and generates REGISTERED.md via B2.2 renderer.
"""

import json
import sys

# Import the B2.2 renderer
sys.path.insert(0, '/tmp')
from b2_2_renderer import RegisteredRenderer

# Read candidate bundles from stdin (output of B2.1 query or sample data)
if len(sys.argv) > 1:
    with open(sys.argv[1]) as f:
        bundles = json.load(f)
else:
    bundles = json.load(sys.stdin)

# Render via B2.2
renderer = RegisteredRenderer(bundles)
print(renderer.render())
