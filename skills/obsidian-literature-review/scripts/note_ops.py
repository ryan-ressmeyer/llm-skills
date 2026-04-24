#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Create and update Obsidian citekey notes for the obsidian-literature-review skill.

A citekey note is a flat-layout per-paper note named `<citekey>.md` in the
References/ folder of the vault. It carries YAML frontmatter, an embed of the
PDF, a `## QLMRI summary` section that the paper-summarize flow can fill in
later, and a `## Connections` section.

Subcommands:

  create   Create a new citekey note (errors if it already exists unless --force)
  set-summary
           Replace (or insert) the body of the `## QLMRI summary` section with
           content from --content or --content-file
  set-status
           Update the `status` field in the note's frontmatter
"""

import sys
import json
import argparse
import re
from pathlib import Path
from datetime import date

import yaml


# ---------- frontmatter helpers ----------

FM_RE = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    body = text[m.end():]
    return fm, body


def join_frontmatter(fm: dict, body: str) -> str:
    yml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120).strip()
    return f'---\n{yml}\n---\n\n{body.lstrip()}'


# ---------- create ----------

def cmd_create(args):
    note_path = Path(args.note_path)
    if note_path.exists() and not args.force:
        print(f'Error: {note_path} already exists (use --force to overwrite)', file=sys.stderr)
        sys.exit(1)

    authors = json.loads(args.authors) if args.authors else []
    subject = json.loads(args.subject) if args.subject else []
    tags = json.loads(args.tags) if args.tags else []

    fm = {
        'type': 'reference',
        'citekey': args.citekey,
        'title': args.title,
        'authors': authors,
        'year': int(args.year) if args.year else None,
        'venue': args.venue or None,
        'doi': args.doi or None,
        'pdf': args.pdf_rel or None,
        'subject': subject,
        'tags': tags,
        'status': args.status or 'unread',
        'date_added': str(date.today()),
    }
    # Strip None / empty
    fm = {k: v for k, v in fm.items() if v not in (None, '', [])}

    # Header
    if len(authors) == 1:
        byline = authors[0].split(',')[0].strip() if ',' in authors[0] else authors[0].split()[-1]
    elif len(authors) >= 2:
        first = authors[0].split(',')[0].strip() if ',' in authors[0] else authors[0].split()[-1]
        last = authors[-1].split(',')[0].strip() if ',' in authors[-1] else authors[-1].split()[-1]
        byline = f'{first} & {last}' if len(authors) == 2 else f'{first} et al.'
    else:
        byline = ''

    header = f'# {byline} {args.year} — {args.title}'.strip()

    pdf_section = f'## PDF\n![[{args.pdf_rel}]]\n' if args.pdf_rel else ''

    body = (
        f'{header}\n\n'
        f'## QLMRI summary\n'
        f'*Not yet summarized.*\n\n'
        f'{pdf_section}'
    )

    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(join_frontmatter(fm, body), encoding='utf-8')
    print(f'Created note: {note_path}', file=sys.stderr)


# ---------- summary section ops ----------

SECTION_RE_TMPL = r'(^## {section}\b.*?$)(.*?)(?=^## |\Z)'


def replace_section(text: str, section: str, new_body: str) -> str:
    """Replace the body of `## <section>` with new_body. If the section does
    not exist, append it at the end of the document."""
    pattern = re.compile(SECTION_RE_TMPL.format(section=re.escape(section)),
                         re.DOTALL | re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda m: f'{m.group(1)}\n{new_body.rstrip()}\n\n', text)
    # Append
    suffix = '' if text.endswith('\n') else '\n'
    return f'{text}{suffix}\n## {section}\n{new_body.rstrip()}\n'


def cmd_set_summary(args):
    note_path = Path(args.note_path)
    if not note_path.exists():
        print(f'Error: {note_path} does not exist', file=sys.stderr)
        sys.exit(1)

    if args.content_file:
        content = Path(args.content_file).read_text(encoding='utf-8')
    else:
        content = args.content or ''

    text = note_path.read_text(encoding='utf-8')
    fm, body = split_frontmatter(text)
    new_body = replace_section(body, args.section, content)

    if args.mark_summarized:
        fm['status'] = 'summarized'

    note_path.write_text(join_frontmatter(fm, new_body), encoding='utf-8')
    print(f'Updated section "## {args.section}" in {note_path}', file=sys.stderr)


def cmd_set_status(args):
    note_path = Path(args.note_path)
    if not note_path.exists():
        print(f'Error: {note_path} does not exist', file=sys.stderr)
        sys.exit(1)
    text = note_path.read_text(encoding='utf-8')
    fm, body = split_frontmatter(text)
    fm['status'] = args.status
    note_path.write_text(join_frontmatter(fm, body), encoding='utf-8')
    print(f'Set status={args.status} on {note_path}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Create and update Obsidian citekey notes')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_create = sub.add_parser('create', help='Create a new citekey note')
    p_create.add_argument('--note-path', required=True, help='Absolute path to <citekey>.md to create')
    p_create.add_argument('--citekey', required=True)
    p_create.add_argument('--title', required=True)
    p_create.add_argument('--authors', required=True, help='JSON list of author strings')
    p_create.add_argument('--year', required=True)
    p_create.add_argument('--venue', default='')
    p_create.add_argument('--doi', default='')
    p_create.add_argument('--pdf-rel', default='', help='PDF path relative to the note file (for the embed)')
    p_create.add_argument('--subject', default='', help='JSON list of subject/species strings')
    p_create.add_argument('--tags', default='', help='JSON list of tag strings')
    p_create.add_argument('--status', default='unread', choices=['unread', 'read', 'summarized', 'key-paper'])
    p_create.add_argument('--force', action='store_true')
    p_create.set_defaults(func=cmd_create)

    p_sum = sub.add_parser('set-summary', help='Replace the body of a section in the note')
    p_sum.add_argument('--note-path', required=True)
    p_sum.add_argument('--section', default='QLMRI summary', help='Section heading text (without "## ")')
    p_sum.add_argument('--content', help='Section content (markdown)')
    p_sum.add_argument('--content-file', help='File containing section content (markdown)')
    p_sum.add_argument('--mark-summarized', action='store_true', help='Also set frontmatter status=summarized')
    p_sum.set_defaults(func=cmd_set_summary)

    p_st = sub.add_parser('set-status', help='Update frontmatter status')
    p_st.add_argument('--note-path', required=True)
    p_st.add_argument('--status', required=True, choices=['unread', 'read', 'summarized', 'key-paper'])
    p_st.set_defaults(func=cmd_set_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
