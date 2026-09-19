# Codex project integration

The root `AGENTS.md` is the authoritative project instruction file and is
already shared with Codex and other agents. Do not duplicate or override it
here. The `.agents/skills/` directory contains the repository's portable skill
copies; `.claude/` remains the source for Claude Code's original setup.

The hooks in `.codex/hooks.json` dispatch to the existing scripts under
`.claude/hooks/` without modifying them. Review new or changed project hooks
with Codex's `/hooks` command before enabling them.
