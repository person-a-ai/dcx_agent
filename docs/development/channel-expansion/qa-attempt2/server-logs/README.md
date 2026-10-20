# Server logs (captured by the controller)

The servers run outside the QA sandbox in the controller's Terminal tabs, so their stdout is not a file.
The controller copied what exists on disk and notes the rest here (2026-10-20).

## QA-NEG-003 environment (frontend :3002 → backend :8002, QA_THREADS_MODE=blocked)

- Worker logs copied from the session collection (scf649933bbbc4b2eaeb0d8e9679cd740/collections/c1):
  - neg003-worker-list.log (1 line), neg003-worker-detail.log (0 lines). Neither contains "threads.com".
- Live data directory (read-only for QA): /private/tmp/claude-501/-Users-yunho--claude-spares-spare-d69SsJ/9251127c-9663-4223-85bb-09f9c61d81cd/scratchpad/qa-data-neg003
  - queue: crawl/scf649933bbbc4b2eaeb0d8e9679cd740/collections/c1/queue.sqlite (urls.status / urls.last_error per source)
  - report: crawl/scf649933bbbc4b2eaeb0d8e9679cd740/collections/c1/report.json, worker_state.json
- Backend stdout (uvicorn access log) is in the controller's Terminal tab "QA env neg003". The controller reviewed it at
  capture time: only local API calls from the browser/seed (POST /context, /keywords/.../manual, PUT /crawl/.../config,
  /crawl/.../list, /detail, /finish-partial, GET status/session); the access log never records outbound requests.
- In this environment the worker loads the QA hook (DCX_TEST_ADAPTER_MODULE=channel_expansion_qa), whose Threads fake raises
  AdapterBlocked in detail without any network request; crawl tests also forbid sockets.

## QA-REG-001 environment (added by the controller)

- frontend http://localhost:3003 (NEXT_PUBLIC_INTERNAL_TOOLS=true so the development sample channel row is visible)
  → backend http://localhost:8003 (FIXTURE_CORPUS_PATH = /private/tmp/claude-501/-Users-yunho--claude-spares-spare-d69SsJ/9251127c-9663-4223-85bb-09f9c61d81cd/scratchpad/aircon_qa.csv, 2,000 synthetic rows from
  backend/tests/fixtures/make_corpus.py; otherwise the same env as main). The QA plan's section 8 omitted these two settings;
  the scenario's assertions are unchanged.
