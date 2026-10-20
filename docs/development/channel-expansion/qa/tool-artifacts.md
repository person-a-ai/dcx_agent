# Tool-managed artifacts outside QA directory

- `/Users/yunho/Documents/dcx_agent-channels-build/.playwright-mcp/console-2026-10-20T13-35-08-291Z.log`
- `/Users/yunho/Documents/dcx_agent-channels-build/.playwright-mcp/page-2026-10-20T13-35-10-197Z.yml`

Playwright MCP automatically wrote its snapshot/console files here. The isolated Chrome profile/cache is tool-managed; its path was not exposed. QA explicitly wrote only qa/ and qa.json. Test API/UI operations created data in the controller-provided stores as intended by the plan.
