# Codex compatibility layer

This directory adapts the repository's existing Claude Code setup without
changing `.claude/`.

| Claude source | Codex surface |
|:--|:--|
| `.claude/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` |
| `.claude/agents/mutation-tester.md` | `.codex/agents/mutation-tester.toml` |
| `.claude/agents/preflight-runner.md` | `.codex/agents/preflight-runner.toml` |
| `.claude/settings.json` hooks | `.codex/hooks.json` via `hooks/dispatch.py` |
| `.mcp.json` Playwright server | `[mcp_servers.playwright]` in `config.toml` |

The dispatcher invokes the original hook scripts under `.claude/hooks/`, so
there is one policy implementation to maintain. Codex's `/hooks` command must
mark the project hooks trusted before they execute. Claude's local permission
allowlist in `.claude/settings.local.json` has no direct project-level Codex
equivalent; branch and privacy policy remain enforced by the migrated hooks.
