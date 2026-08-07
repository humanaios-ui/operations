#!/usr/bin/env python3
"""
inspect_ai + Ollama Local LLM Integration
Configure inspect_ai to use local Ollama model
"""

import os
from inspect_ai import Task, eval
from inspect_ai.solver import generate

# Set Ollama endpoint (local)
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

# Example: Running a task with local model
# Replace "mistral" with your model name

# task = Task(
#     name="example",
#     dataset=[{"id": "1", "input": "What is 2+2?"}],
#     plan=[generate(model="ollama:mistral")],
# )

# result = eval(task, model="ollama:mistral")

print("✅ Ollama integration ready")
print("   Use: generate(model='ollama:mistral')")
print("   Or: eval(task, model='ollama:mistral')")
