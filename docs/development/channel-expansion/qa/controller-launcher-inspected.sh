#!/bin/zsh
# Start one browser-QA environment (backend + frontend) for channel-expansion.
# Usage: qa_env.sh <name> <backend_port> <frontend_port> [KEY=VALUE ...]
set -e
WT=/Users/yunho/Documents/dcx_agent-channels-build
SP=${0:A:h}
name=$1; bport=$2; fport=$3; shift 3
data=$SP/qa-data-$name
rm -rf "$data"; mkdir -p "$data"
if [[ $name == main ]]; then
  fe=$WT/frontend
else
  fe=$SP/fe-$name
  rm -rf "$fe"; mkdir -p "$fe"
  rsync -a --exclude node_modules --exclude .next "$WT/frontend/" "$fe/"
  ln -s "$WT/frontend/node_modules" "$fe/node_modules"
fi
export STORAGE=local LOCAL_DATA_DIR=$data EMBED_BACKEND=fake ENABLE_FIXTURE_CHANNEL=true \
  REAL_CHANNELS_ENABLED=true CORS_ORIGINS=http://localhost:$fport \
  DCX_TEST_ADAPTER_MODULE=channel_expansion_qa PYTHONPATH=$WT/backend/tests/qa_hooks:$WT/backend
for kv in "$@"; do export "$kv"; done
unset VOYAGE_API_KEY
echo "env=$name backend=:$bport frontend=:$fport data=$data extra=$*"
(cd $WT/backend && exec $WT/backend/.venv/bin/python -m uvicorn app.main:app --port $bport) &
bpid=$!
trap "kill $bpid 2>/dev/null" EXIT INT TERM
bundler=(); [[ $name != main ]] && bundler=(--webpack)
cd "$fe" && NEXT_PUBLIC_API_URL=http://localhost:$bport npx next dev -p $fport "${bundler[@]}"
