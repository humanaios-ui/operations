#!/usr/bin/env python3
"""
Test ACAT-X tasks with local Ollama model
"""

import os
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

from inspect_ai import Task, eval
from inspect_ai.solver import generate
from acat_x_consist import consist_task

print("Testing consist task with local Ollama model...")
print("Using: mistral (local)")

# Run task with local model
# Note: This will make actual API calls to Ollama
# result = eval(consist_task, model="ollama:mistral")
# print(result)

print("✅ Test script ready")
print("   Run: python3 test_acat_with_ollama.py")
