# HumanAIOS forecasting bot (main.py v2.3) — runs one pass and exits (asyncio.run(...),
# no serve loop), unlike resource-miner/ACAT's long-running HTTP services. Already
# deployed on Railway (railway.toml: `python main.py --mode test_questions`).
#
# Build context is this directory (tools/Metaculus/) — self-contained, no ../ dependency.
#
#   docker build -t metaculus-bot .
#
# Azure counterpart is a Container Apps JOB (infra/metaculus-job.bicep), not a Container
# App — a batch/run-to-completion workload, not an always-on ingress service.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./main.py

# Verified from this file's own code: SUPABASE_URL, SUPABASE_KEY (os.getenv calls in
# main.py). NOT verified here — main.py imports GeneralLlm/MetaculusClient from the
# third-party forecasting-tools package, which reads its own provider keys internally;
# this repo never names them directly. Standard ecosystem convention (confirm against
# forecasting-tools' own docs before relying on it): ANTHROPIC_API_KEY (forecast model,
# "anthropic/claude-haiku-4-5"), GROQ_API_KEY (researcher model, "groq/openai/gpt-oss-120b"
# — note this contradicts this file's own header docstring, which still says
# "gemini-2.0-flash (research)"; the code, not the comment, is what actually runs),
# OPENAI_API_KEY (parser/summarizer, gpt-4o-mini), and a Metaculus API token (commonly
# METACULUS_TOKEN for this package). See infra/metaculus-job.bicep for where each lands.
RUN useradd --no-create-home --shell /usr/sbin/nologin appuser
USER appuser

ENTRYPOINT ["python3", "main.py"]
CMD ["--mode", "test_questions"]
