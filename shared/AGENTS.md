# Agent Context — Ryan Ressmeyer

Global context loaded by both pi and Claude Code at startup. Keep this small; skills carry workflow detail.

## Who

Ryan Ressmeyer — solo visual neuroscience researcher. Work spans experiment code, data analysis, literature review, manuscript writing, and scientific figures.

## Toolset preferences

- **Python:** always via `uv run`. Never bare `python`, `python3`, or `pip`. Project code uses `pyproject.toml` + `.venv`; standalone scripts use PEP 723 inline metadata. See the `python-environment` skill.
- **Git:** commit messages are a single line. No body, no bullets, no Co-Authored-By trailers. See the `git-commits` skill.
- **Editor:** Neovim. Terminal-first workflow.
- **Obsidian** is the primary knowledge store — vault-aware skills (`obsidian-*`) exist for vault operations.

## How to find capability

Agent skills live in `~/.agents/skills/` (pi) and `~/.claude/skills/` (Claude Code), both symlinked from `~/code/agent-config/skills/`. Invoke relevant skills before acting — the `skills-prelude` skill enforces this.

Common starting points:
- Building or extending a paper database → `literature-review`, `paper-summarize`, `pdf-retrieve`
- Writing a manuscript → `manuscript-planning`, `literature-writer`, `manuscript-review`, `style-guide`
- Any multi-step code task → `designing-plans` → `writing-plans` → `executing-plans`
- Bug or unexpected behavior → `systematic-debugging` before proposing fixes
- Before claiming work complete → `verification-before-completion`

## Working norms

- Investigate before proposing fixes. Root cause over symptom-patching.
- TDD by default for code: failing test → minimal implementation → refactor.
- No success claims without fresh verification output.
- Ask for clarification when requirements are ambiguous — do not guess and proceed.
- Keep responses concise. Prefer showing work (commands, file paths, diffs) over narrating it.
