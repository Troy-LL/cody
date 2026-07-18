# `.codex/skills/`

Agent skills for this repo. Each subdirectory is one skill with a `SKILL.md` (YAML
frontmatter `name` + `description`) that Cursor/Codex agents auto-discover and can invoke.
Skills placed here are tracked in git, so they travel with the repo and are available in
every local checkout and cloud-agent session (see [`docs/team/SDD-ETIQUETTE.md`](../../docs/team/SDD-ETIQUETTE.md)
— do **not** gitignore `.codex/`).

## Skill families

### OpenSpec (spec-driven workflow, `openspec` CLI)
- `openspec-propose`, `openspec-apply-change`, `openspec-update-change`,
  `openspec-sync-specs`, `openspec-archive-change`, `openspec-explore`

### Figma (vendored from the `cursor-public` Figma plugin)
- `figma-use`, `figma-use-figjam`, `figma-use-slides`, `figma-use-motion`
- `figma-design-to-code`, `figma-generate-design`, `figma-generate-library`
- `figma-generate-diagram`, `figma-implement-motion`, `figma-code-connect`
- `figma-create-new-file`, `figma-swiftui`

### Workflow (vendored from the `cursor-public` plugin)
- `generate-project-plan`, `video-interaction-mapper`

## Why these are vendored

The Figma and workflow skills originally load from an ephemeral Cursor plugin cache
(`~/.cursor/plugins/cache/...`), which is not part of the repo and is not guaranteed to be
present in a fresh cloud-agent VM. Copying them here makes them local, version-controlled,
and reliably invocable. The Figma skills additionally require the Figma MCP server /
plugin to be connected at runtime to actually execute their tool calls; the skill files
themselves (instructions + reference docs) work offline.
