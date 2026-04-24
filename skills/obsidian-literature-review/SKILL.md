---
name: obsidian-literature-review
description: Use when building or maintaining the literature database that lives inside Ryan's Obsidian vault — adding papers (DOI/PMID/arxiv/PDF), summarizing them as citekey notes with embedded PDFs, searching, and checking integrity. Vault-aware variant of literature-review.
---

# Obsidian Literature Review

## Overview

This is the vault-aware orchestrator for managing the master literature
database that lives inside Ryan's Obsidian vault. It is the same workflow as
`literature-review`, but with a flat, Obsidian-native layout: one citekey note
per paper at the top of `References/`, PDFs embedded from a sibling `pdfs/`
folder, and citation graph yaml files in a sibling `graph/` folder.

The methodology (QLMRI summarization, citation graph exploration, theme
synthesis) is unchanged. This skill differs from `literature-review` only in
**file layout**, not in process. It calls the same shared scripts under
`citation-fetch/`, `pdf-retrieve/`, `paper-summarize/`, `database-check/`, and
`database-search/`, passing them explicit `--*-path` arguments so they place
files in the vault layout instead of the default nested layout.

## When to Use

- User wants to add a paper to the master vault library (DOI/PMID/arxiv/PDF)
- User wants to summarize a paper that is already in the vault library
- User asks questions about papers in the vault library
- User wants to explore citation graph for a vault paper
- User asks to check integrity of the vault library
- User asks to search the vault library

For per-project, manuscript-specific reference databases, use the original
`literature-review` skill instead — it defaults to the nested
`references/<id>/<id>.pdf` layout that those projects already use.

## Vault Layout

```
<vault>/References/
├── index.yaml                       # master metadata, citekey-keyed
├── references.bib                   # generated from index.yaml
├── pdfs/
│   ├── smith-jones-2023.pdf
│   ├── smith-2023.pdf
│   └── smith-jones-2023-b.pdf       # collision suffix
├── graph/
│   └── smith-jones-2023/
│       ├── references.yaml
│       ├── cited-by.yaml
│       └── related.yaml
├── smith-jones-2023.md              # one citekey note per paper (flat)
├── smith-2023.md
└── @oldStylePlugin2020.md           # legacy Citations-plugin notes (left untouched)
```

**Database root:** `~/Documents/Ryan's Vault/References/` (the user's primary
vault). If the working directory is different, ask the user before assuming.

**Citekey convention:**
- 1 author: `lastname-year` (e.g. `smith-2023`)
- 2+ authors: `firstauthor-lastauthor-year` (e.g. `smith-jones-2023`)
- Lowercased, ASCII-folded, hyphens for compound surnames
- Collision suffix: `-b`, `-c`, `-d`, ...

Use `scripts/citekey.py` to derive citekeys — it handles ASCII folding and
collision detection against `index.yaml` and `pdfs/` automatically, and is
idempotent on DOI (re-adding the same DOI returns the existing citekey).

**Coexistence with legacy notes:** the existing `@authorTitleYear.md` notes
created by the Citations plugin live alongside new citekey notes. Do not touch
them. Migration will happen separately.

## Core Loop

Same as `literature-review`:

```
User provides topic / paper / question
  → Route to appropriate mode
  → Execute sub-skills with vault paths
  → Present results for review
  → Surface candidates for next papers
  → User decides next step
  → Repeat
```

## Modes

### Discovery Mode

Same as `literature-review`. Use `citation-fetch` to search:
```bash
uv run ~/.claude/skills/citation-fetch/scripts/fetch_metadata.py --query "search terms" --limit 10
```

### Processing Mode

**Trigger:** user provides a DOI, PMID, arxiv ID, or PDF path and asks to add it.

Set up shell variables to keep the commands legible:
```bash
DB="$HOME/Documents/Ryan's Vault/References"
```

**Step 1 — Fetch metadata:**
```bash
uv run ~/.claude/skills/citation-fetch/scripts/fetch_metadata.py --doi 10.xxx/yyy
```
From the result, extract: title, authors (list), year, venue, doi, bibtex.

**Step 2 — Derive citekey:**
```bash
uv run ~/.claude/skills/obsidian-literature-review/scripts/citekey.py \
  --authors '["Smith, J.", "Jones, A."]' \
  --year 2023 \
  --doi 10.xxx/yyy \
  --database "$DB" \
  --json
```
If `reused: true`, the paper is already in the database — switch to update mode
or stop. Otherwise use the returned `citekey`.

**Step 3 — Fetch PDF directly into the vault:**
```bash
uv run ~/.claude/skills/pdf-retrieve/scripts/find_open_access.py \
  --doi 10.xxx/yyy \
  --output-path "$DB/pdfs/<citekey>.pdf"
```
If exit code is non-zero, no open-access PDF was found — ask the user to drop
the PDF at `$DB/pdfs/<citekey>.pdf` themselves before continuing.

**Step 4 — Fetch citation graph into the vault graph dir:**
```bash
uv run ~/.claude/skills/citation-fetch/scripts/fetch_citation_graph.py \
  --doi 10.xxx/yyy \
  --paper-id <citekey> \
  --output-dir "$DB/graph/<citekey>/" \
  --database-path "$DB"
```

**Step 5 — Create the citekey note:**
```bash
uv run ~/.claude/skills/obsidian-literature-review/scripts/note_ops.py create \
  --note-path "$DB/<citekey>.md" \
  --citekey <citekey> \
  --title "Paper title" \
  --authors '["Smith, J.", "Jones, A."]' \
  --year 2023 \
  --venue "J Neurosci" \
  --doi 10.xxx/yyy \
  --pdf-rel "pdfs/<citekey>.pdf" \
  --subject '["macaque"]' \
  --status unread
```

**Step 6 — Update index.yaml with the entry and explicit paths:**
```bash
uv run ~/.claude/skills/paper-summarize/scripts/update_index.py \
  --database "$DB" \
  --id <citekey> \
  --title "Paper title" \
  --authors '["Smith, J.", "Jones, A."]' \
  --year 2023 \
  --journal "J Neurosci" \
  --doi 10.xxx/yyy \
  --subject '["macaque"]' \
  --status to-read \
  --has-pdf true \
  --has-summary false \
  --pdf-path "pdfs/<citekey>.pdf" \
  --note-path "<citekey>.md" \
  --summary-path "<citekey>.md" \
  --graph-dir "graph/<citekey>"
```
The `--*-path` flags tell `database-check` and `database-search` where to look
for this entry's files instead of using the legacy nested-layout fallback.
`summary-path` equals `note-path` because the QLMRI summary lives inside the
note in this layout.

**Step 7 — Update references.bib:**
```bash
uv run ~/.claude/skills/paper-summarize/scripts/update_bibtex.py \
  --database "$DB" \
  --id <citekey> \
  --entry '@article{<citekey>, ...}'
```

**Step 8 — Surface next papers** from the citation graph (same as
`literature-review`).

### Summarization Mode

**Trigger:** user asks to summarize a paper that already has a citekey note.

1. Read the PDF at `$DB/pdfs/<citekey>.pdf` using Claude's native PDF reading.
2. Write the QLMRI sections following the template in `paper-summarize`'s
   SKILL.md (Citation, Subject/Preparation, Questions, Logic, Methods, Results,
   Inferences, Key Figures). Save them to a temp file or compose inline.
3. Replace the note's `## QLMRI summary` section and mark the paper summarized:
   ```bash
   uv run ~/.claude/skills/obsidian-literature-review/scripts/note_ops.py set-summary \
     --note-path "$DB/<citekey>.md" \
     --content-file /tmp/qlmri.md \
     --mark-summarized
   ```
4. Update the index entry to reflect summarized status:
   ```bash
   uv run ~/.claude/skills/paper-summarize/scripts/update_index.py \
     --database "$DB" --id <citekey> \
     --status summarized --has-summary true
   ```
5. Present the summary to the user, then surface next papers from the citation
   graph as in Processing Mode step 8.

### Question / Search Mode

```bash
uv run ~/.claude/skills/database-search/scripts/search_database.py "query" \
  --database "$DB"
```
The search script honors the `summary_path` and `graph_dir` fields in
`index.yaml` automatically — no extra flags needed.

### Maintenance Mode

```bash
uv run ~/.claude/skills/database-check/scripts/check_integrity.py "$DB" --verbose
```
The check script reads each entry's `pdf_path` / `note_path` / `summary_path` /
`graph_dir` fields with nested-layout fallback, so vault-layout entries and any
remaining legacy entries are both verified correctly.

## Session Awareness

At the start of a vault-library session, run `database-check` (or just read
`index.yaml`) and tell the user how many papers, how many summarized, how many
missing PDFs.

## Key Behaviors

- **One paper at a time.** Same as `literature-review`.
- **Always surface candidates** from the citation graph after each addition.
- **Never touch legacy `@*.md` notes** unless the user explicitly asks for
  migration.
- **Always pass explicit `--*-path` flags** to `update_index.py` for new
  vault-layout entries — without them the entry will be checked under the
  nested-layout fallback and `database-check` will report false errors.
- **Idempotent on DOI.** `citekey.py` short-circuits if the DOI is already in
  the index, so re-adding the same paper is safe.
- **Citation graph candidates** are read from `$DB/graph/<citekey>/*.yaml` —
  the search script's `--cited-by`, `--cites`, `--related-to` flags work the
  same as in `literature-review`.

## Sub-Skill Reference

| Sub-Skill / Script | Purpose | Vault-specific args |
|---|---|---|
| `citation-fetch/fetch_metadata.py` | Metadata + bibtex | (none — layout-agnostic) |
| `citation-fetch/fetch_citation_graph.py` | Citation graph yaml files | `--output-dir "$DB/graph/<citekey>/"` |
| `pdf-retrieve/find_open_access.py` | Find + download PDF | `--output-path "$DB/pdfs/<citekey>.pdf"` |
| `obsidian-literature-review/citekey.py` | Derive vault citekey | `--database "$DB"` |
| `obsidian-literature-review/note_ops.py` | Create/update citekey note | `--note-path "$DB/<citekey>.md"` |
| `paper-summarize/update_index.py` | Index entry | `--pdf-path`, `--note-path`, `--summary-path`, `--graph-dir` |
| `paper-summarize/update_bibtex.py` | references.bib | (none — layout-agnostic) |
| `database-check/check_integrity.py` | Integrity (reads paths from entries) | (none — auto) |
| `database-search/search_database.py` | Search (reads paths from entries) | (none — auto) |
