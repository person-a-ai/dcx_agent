# Overall FAIL — final worktree integrity blocked

17/17 individual browser/API scenarios passed. The requested frozen-commit acceptance cannot be granted because HEAD and source fingerprint changed externally during the run. See [integrity-check.json](integrity-check.json).

Tested initial HEAD: `6955ba0256d60043b1410871a3f56445e578c6b2`. Runtime: `01a158f9-b73b-7e50-a138-7e141d487784`. Browser: headed isolated Chrome via Playwright MCP.

| ID | Observed result | Evidence |
|---|---|---|
| QA-E2E-001 | PASS | [report](QA-E2E-001.md) |
| QA-E2E-002 | PASS | [report](QA-E2E-002.md) |
| QA-E2E-003 | PASS | [report](QA-E2E-003.md) |
| QA-E2E-004 | PASS | [report](QA-E2E-004.md) |
| QA-E2E-005 | PASS | [report](QA-E2E-005.md) |
| QA-E2E-006 | PASS | [report](QA-E2E-006.md) |
| QA-NEG-001 | PASS | [report](QA-NEG-001.md) |
| QA-NEG-002 | PASS | [report](QA-NEG-002.md) |
| QA-NEG-003 | PASS | [report](QA-NEG-003.md) |
| QA-NEG-004 | PASS | [report](QA-NEG-004.md) |
| QA-EDGE-001 | PASS | [report](QA-EDGE-001.md) |
| QA-EDGE-002 | PASS | [report](QA-EDGE-002.md) |
| QA-EDGE-003 | PASS | [report](QA-EDGE-003.md) |
| QA-EDGE-004 | PASS | [report](QA-EDGE-004.md) |
| QA-REG-001 | PASS | [report](QA-REG-001.md) |
| QA-REG-002 | PASS | [report](QA-REG-002.md) |
| QA-REG-003 | PASS | [report](QA-REG-003.md) |

No product/Git writes, server starts/stops, staging, commits, or harness complete/decide by this worker. Automatic Playwright artifacts outside qa/: `.playwright-mcp/page-2026-10-20T11-02-58-898Z.yml` and `.playwright-mcp/console-2026-10-20T11-02-43-413Z.log`, copied into qa/.
