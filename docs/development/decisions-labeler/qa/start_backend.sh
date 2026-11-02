#!/bin/bash
# QA backend on :8321. Caller may override JEV_BACKEND, DECISIONS_API_KEY, DECISIONS_MODEL,
# DECISIONS_RATE_PER_MIN, LABEL_FAKE_JEV_CROSS, OPENAI_API_KEY before calling.
# Usage: start_backend.sh LOGFILE
set -u
WT=/Users/baenaongunmandu/workspace/dcx/dcx_agent-decisions
Q=/private/tmp/claude-501/-Users-baenaongunmandu-workspace-dcx/06aa02a9-5566-4935-b7fa-573e14d6ec79/scratchpad/qa-data
export STORAGE=local LOCAL_DATA_DIR="$Q/data" LLM_BACKEND=fake EMBED_BACKEND=fake LABEL_GPT_BACKEND=fake \
  ENABLE_FIXTURE_CHANNEL=True FIXTURE_CORPUS_PATH="$Q/corpus.csv" AUTOCOMPLETE_BACKEND=fake \
  DECISIONS_BASE_URL=http://127.0.0.1:8399/v1 PYTHONDONTWRITEBYTECODE=1
export JEV_BACKEND="${JEV_BACKEND:-decisions}" OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export DECISIONS_API_KEY="${DECISIONS_API_KEY-qa-key-1,qa-key-2}"
cd "$WT/backend"
echo "JEV_BACKEND=$JEV_BACKEND DECISIONS_MODEL=${DECISIONS_MODEL:-default} keys_set=$([ -n "$DECISIONS_API_KEY" ] && echo yes || echo no) LABEL_FAKE_JEV_CROSS=${LABEL_FAKE_JEV_CROSS:-unset}" > "$1"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8321 >> "$1" 2>&1
