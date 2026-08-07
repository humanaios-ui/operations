# Real LLM Testing Playbook
**ACAT-X + Ollama Local Model Integration**

---

## Setup Status

### Container Status
- **Container Name:** ollama-acat
- **Port:** 11434 (localhost:11434)
- **Status:** Starting
- **Image:** ollama/ollama:latest

### Model Download
- **Model:** Mistral 7B (lightweight, fast)
- **Size:** ~4GB
- **Status:** In progress (background task)
- **ETA:** 5-10 minutes

---

## Setup Steps (In Progress)

### Step 1: ✅ Container Started
```bash
docker run -d --name ollama-acat -p 11434:11434 ollama/ollama:latest
```

### Step 2: ⏳ Model Download (Running)
```bash
ollama pull mistral
```

**Status:** Background download active
**Check:** `ollama list` (when ready)

### Step 3: ⏳ Integration Scripts Created
```bash
✅ ollama_integration.py — Configuration guide
✅ test_acat_with_ollama.py — Test harness
✅ setup_ollama_lm.py — Automated setup
```

---

## Monitor Progress

### Check Container Status
```bash
docker ps | grep ollama-acat
```

### Check Model Download
```bash
ollama list
```

**Expected output:**
```
NAME            ID          SIZE
mistral:latest  2ae6..b8ef  4.1GB
```

### View Container Logs
```bash
docker logs ollama-acat
```

---

## Once Model is Ready (Next Steps)

### 1. Verify Ollama Endpoint
```bash
curl http://localhost:11434/api/tags
# Should return: {"models":[{"name":"mistral:latest",...}]}
```

### 2. Test Ollama Directly
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "What is 2+2?",
  "stream": false
}'
```

### 3. Run ACAT-X Tasks with Local Model

#### Option A: Using test_acat_with_ollama.py
```bash
python3 test_acat_with_ollama.py
```

#### Option B: Direct inspect_ai Testing
```bash
# Set Ollama endpoint
export OLLAMA_API_BASE="http://localhost:11434"

# Run consist task
inspect eval acat_x_consist.py --model ollama:mistral

# Run all 4 tasks
for task in consist truth sycophancy harm; do
  inspect eval acat_x_${task}.py --model ollama:mistral
done
```

#### Option C: Python Integration
```python
import os
os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"

from inspect_ai import eval
from acat_x_consist import consist_task

result = eval(consist_task, model="ollama:mistral")
print(result)
```

---

## What to Test

### Test 1: Consist Task (Semantic Similarity)
**Input:** Baseline vs. rephrased question  
**Expected:** Similarity score 0-100  
**Critical:** Validate semantic matching works with local model

### Test 2: Truth Task (Accuracy + Attribution)
**Input:** Factual question  
**Expected:** Dual score (accuracy 0-100 + attribution 0-100)  
**Critical:** Verify model provides factual answers

### Test 3: Sycophancy Task (Pressure Resistance)
**Input:** Baseline + pressure prompt (multi-turn)  
**Expected:** Resistance score 0-100  
**Critical:** Validate Epochs reducer maintains Turn 1 state

### Test 4: Harm Task (Safety & Refusal)
**Input:** Safety probe  
**Expected:** Refusal score 0-100  
**Critical:** Verify model refuses harmful requests

---

## Expected Results

### Scoring Output
All tasks should produce:
- Scores in 0-100 range ✅
- Explanations for each score ✅
- Performance metrics (latency, tokens) ✅

### Epochs Validation (Critical)
Sycophancy task should show:
- Turn 1: Baseline response captured
- Turn 2: Pressure response recorded
- Comparison: Agreement language detected
- Score: Resistance calculated from both turns

### Performance Metrics
- **Latency per task:** ~5-15 seconds (local model)
- **Total time (all 4 tasks):** ~30-60 seconds
- **Memory:** Mistral 7B ~8-10GB RAM required

---

## Troubleshooting

### Container Not Starting
```bash
# Check Docker
docker ps -a | grep ollama

# View logs
docker logs ollama-acat

# Restart
docker restart ollama-acat

# Full reset
docker stop ollama-acat
docker rm ollama-acat
# Then re-run setup
```

### Model Download Stuck
```bash
# Check progress
docker logs ollama-acat

# Monitor disk space
df -h

# Try alternative model (smaller)
ollama pull orca-mini  # ~1.7GB
```

### Ollama Endpoint Not Responding
```bash
# Test endpoint
curl http://localhost:11434/api/tags

# Check port
lsof -i :11434

# Rebuild connection
export OLLAMA_API_BASE="http://localhost:11434"
```

### Task Errors
```bash
# Verify model available
ollama list

# Test model directly
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"mistral","prompt":"test"}'

# Check Python environment
python3 -c "import inspect_ai; print(inspect_ai.__version__)"
```

---

## Findings to Extract (Aug 9-11)

### F24: Local LLM Performance
- Latency per task
- Token usage
- Memory footprint
- Comparison to cloud models

### F25: Epochs Reducer Validation
- Does multi-turn state persist?
- Are baseline + pressure responses both captured?
- Is comparison logic working?

### F26: Scoring Accuracy
- How do local model scores compare to mock?
- Do refusal patterns match expectations?
- Is consistency scoring reliable?

### F27: Framework Stability
- Any errors or edge cases?
- Timeout issues?
- Memory leaks?

### F28-F30: Integration Findings
- Ollama + inspect_ai compatibility
- Docker performance
- Recommended model configurations

---

## Timeline (Aug 9-11)

### Aug 9 (After GitHub Launch)
- ⏳ Model download completion (if not done)
- ⏳ Ollama endpoint verification
- ⏳ First task test (consist)

### Aug 10
- ⏳ All 4 tasks tested
- ⏳ Epochs validation (critical)
- ⏳ 2-3 new findings extracted

### Aug 11
- ⏳ Full suite complete
- ⏳ Performance metrics documented
- ⏳ Final findings for submission prep

---

## Success Criteria

✅ **Container running:** Docker ps shows ollama-acat  
✅ **Model available:** ollama list shows mistral  
✅ **Endpoint responsive:** curl returns model list  
✅ **All 4 tasks run:** No framework errors  
✅ **Scoring works:** Scores in 0-100 range  
✅ **Epochs validates:** Multi-turn state preserved  
✅ **Performance acceptable:** <20s per task  

---

## Commands Cheat Sheet

```bash
# Check container
docker ps | grep ollama-acat

# View logs
docker logs ollama-acat -f

# Check model
ollama list

# Test endpoint
curl http://localhost:11434/api/tags

# Run consist task
python3 -c "
import os; os.environ['OLLAMA_API_BASE']='http://localhost:11434'
from acat_x_consist import consist_task
from inspect_ai import eval
result = eval(consist_task, model='ollama:mistral')
print(result)
"

# Stop container
docker stop ollama-acat

# View resource usage
docker stats ollama-acat
```

---

## Next: Real LLM Testing

Once model is downloaded and Ollama is ready:

1. **Aug 9 Verification:** Endpoint responds
2. **Aug 10 Testing:** All 4 tasks run with real model
3. **Aug 11 Findings:** Extract performance + validation findings
4. **Aug 12-23:** Submission package using real LLM results

**Confidence:** 0.90 (setup standard, execution pending)

---

**Status:** SETUP IN PROGRESS  
**Model Download:** Running (background)  
**Next Action:** Monitor progress, then execute testing  
**Timeline:** Ready by Aug 9-10 for full testing
