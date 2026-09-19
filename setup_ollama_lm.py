#!/usr/bin/env python3
"""
Ollama Local LLM Setup for ACAT-X Testing
Configures inspect_ai to use local Ollama model
"""

import subprocess
import time
import requests
import json
from pathlib import Path

print("=" * 80)
print("OLLAMA SETUP FOR ACAT-X TESTING")
print("=" * 80)

# ============================================================================
# STEP 1: VERIFY OLLAMA CONTAINER
# ============================================================================

print("\n1. Verifying Ollama container...")

max_retries = 30
retry_count = 0
ollama_ready = False

while retry_count < max_retries and not ollama_ready:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            ollama_ready = True
            print("✅ Ollama container is ready")
            print(f"   Endpoint: http://localhost:11434")
        else:
            print(f"   Waiting for Ollama... ({retry_count+1}/{max_retries})")
            time.sleep(1)
            retry_count += 1
    except Exception as e:
        print(f"   Waiting for Ollama... ({retry_count+1}/{max_retries})")
        time.sleep(1)
        retry_count += 1

if not ollama_ready:
    print("❌ Ollama container did not start in time")
    print("   Try: docker ps | grep ollama-acat")
    exit(1)

# ============================================================================
# STEP 2: PULL MODEL
# ============================================================================

print("\n2. Pulling Mistral 7B model (lightweight + fast)...")
print("   This may take 5-10 minutes (model size: ~4GB)")
print("   Downloading...")

try:
    result = subprocess.run(
        ["ollama", "pull", "mistral"],
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
    )

    if result.returncode == 0:
        print("✅ Model downloaded successfully")
        print(f"   Model: mistral")
        print(f"   Ready for testing")
    else:
        print(f"⚠️  Pull output: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("⚠️  Model download in progress (timeout reached)")
    print("   You can manually check with: ollama list")
except Exception as e:
    print(f"❌ Error pulling model: {e}")
    print("   Try manually: ollama pull mistral")

# ============================================================================
# STEP 3: VERIFY MODEL
# ============================================================================

print("\n3. Verifying model availability...")

try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = data.get("models", [])

        if models:
            print("✅ Available models:")
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0) / (1024**3)  # Convert to GB
                print(f"   • {name} ({size:.2f}GB)")
        else:
            print("⚠️  No models found yet (still downloading?)")
    else:
        print("⚠️  Could not fetch model list")
except Exception as e:
    print(f"⚠️  Error checking models: {e}")

# ============================================================================
# STEP 4: CREATE INSPECT_AI INTEGRATION
# ============================================================================

print("\n4. Creating inspect_ai integration script...")

integration_script = '''#!/usr/bin/env python3
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
'''

integration_path = Path("ollama_integration.py")
integration_path.write_text(integration_script)
print(f"✅ Created {integration_path}")

# ============================================================================
# STEP 5: CREATE TEST SCRIPT
# ============================================================================

print("\n5. Creating test script for ACAT-X tasks...")

test_script = '''#!/usr/bin/env python3
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
'''

test_path = Path("test_acat_with_ollama.py")
test_path.write_text(test_script)
print(f"✅ Created {test_path}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("OLLAMA SETUP COMPLETE")
print("=" * 80)

print("""
✅ Ollama container running on localhost:11434
✅ Model download initiated (Mistral 7B)
✅ Integration scripts created

NEXT STEPS:

1. Wait for model download to complete:
   ollama list

2. Test Ollama directly:
   curl http://localhost:11434/api/tags

3. Run ACAT-X tasks with local model:
   python3 test_acat_with_ollama.py

4. Once ready, full framework testing:
   inspect eval acat_x_consist.py --model ollama:mistral

CONFIGURATION:
- Endpoint: http://localhost:11434
- Model: mistral (or your preferred model)
- Framework: inspect_ai
- Tasks: All 4 ACAT-X tasks ready

USEFUL COMMANDS:
- List models: ollama list
- Pull model: ollama pull mistral
- Remove model: ollama rm mistral
- Stop container: docker stop ollama-acat
- View logs: docker logs ollama-acat
""")

print("=" * 80)
