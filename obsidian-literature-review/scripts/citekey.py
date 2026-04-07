#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Derive a citekey for a paper following the convention:

  - 1 author:    lastname-year                  (e.g. smith-2023)
  - 2+ authors:  firstauthor-lastauthor-year    (e.g. smith-jones-2023)

Names are lowercased and ASCII-folded; spaces and apostrophes become hyphens.
On collision with an existing PDF or index entry, suffix with -b, -c, -d ...

Usage:
  uv run citekey.py --authors '["Smith, J.", "Jones, A."]' --year 2023 \
                    --database "/path/to/References"

Outputs the resolved citekey to stdout.
"""

import sys
import json
import argparse
import unicodedata
import re
from pathlib import Path

import yaml


def fold_ascii(s: str) -> str:
    """Strip diacritics and non-ASCII to a plain ascii form."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c) and ord(c) < 128)


def last_name(author: str) -> str:
    """Extract surname from an author string in 'Last, First' or 'First Last' form."""
    author = author.strip()
    if not author:
        return ''
    if ',' in author:
        last = author.split(',', 1)[0]
    else:
        # 'First Middle Last' — take last token
        last = author.split()[-1] if author.split() else author
    last = fold_ascii(last).lower()
    # Remove anything that isn't a-z; collapse runs to single hyphen
    last = re.sub(r"[^a-z]+", '-', last).strip('-')
    return last


def derive_base(authors: list[str], year: int | str) -> str:
    """Build the base citekey (no collision suffix)."""
    if not authors:
        raise ValueError('at least one author required')
    first = last_name(authors[0])
    if not first:
        raise ValueError(f'could not extract surname from "{authors[0]}"')
    if len(authors) == 1:
        return f'{first}-{year}'
    last = last_name(authors[-1])
    if not last:
        raise ValueError(f'could not extract surname from "{authors[-1]}"')
    if last == first:
        return f'{first}-{year}'
    return f'{first}-{last}-{year}'


def collision_suffix(n: int) -> str:
    """0 -> '', 1 -> '-b', 2 -> '-c', ..."""
    if n == 0:
        return ''
    # 1->b, 2->c, ..., 25->z; beyond that just stack 'z' (extremely unlikely)
    return '-' + chr(ord('a') + n)


def existing_keys(db: Path) -> set[str]:
    """Collect all citekeys already in use in the database."""
    keys: set[str] = set()
    index_path = db / 'index.yaml'
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            for p in data.get('papers', []):
                k = p.get('id')
                if k:
                    keys.add(k)
        except Exception as e:
            print(f'Warning: could not parse index.yaml: {e}', file=sys.stderr)

    pdfs_dir = db / 'pdfs'
    if pdfs_dir.exists():
        for p in pdfs_dir.glob('*.pdf'):
            keys.add(p.stem)

    # Per-paper notes in flat layout
    for note in db.glob('*.md'):
        # Skip dashboards / theme files / leading-@ legacy notes
        name = note.stem
        if name.startswith('@') or name.startswith('_'):
            continue
        # Only treat names that look like citekeys
        if re.match(r'^[a-z]+(-[a-z]+)?-\d{4}[a-z]?$', name):
            keys.add(name)

    return keys


def resolve(authors: list[str], year: int | str, db: Path,
            doi: str = '') -> dict:
    """Resolve a non-colliding citekey, or return the existing key if this DOI
    is already in the database."""
    # If DOI matches an existing entry, reuse that citekey (idempotent add)
    if doi:
        index_path = db / 'index.yaml'
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                for p in data.get('papers', []):
                    if (p.get('doi') or '').lower() == doi.lower():
                        return {'citekey': p['id'], 'reused': True}
            except Exception:
                pass

    base = derive_base(authors, year)
    used = existing_keys(db)
    n = 0
    while True:
        candidate = base + collision_suffix(n)
        if candidate not in used:
            return {'citekey': candidate, 'reused': False, 'base': base, 'collisions': n}
        n += 1
        if n > 25:
            raise RuntimeError(f'too many collisions for base {base}')


def main():
    parser = argparse.ArgumentParser(description='Derive an obsidian-literature-review citekey')
    parser.add_argument('--authors', required=True, help='JSON list of author strings')
    parser.add_argument('--year', required=True, help='Publication year')
    parser.add_argument('--database', required=True, help='Path to References database root')
    parser.add_argument('--doi', default='', help='DOI (used to short-circuit if paper already in index)')
    parser.add_argument('--json', action='store_true', help='Output full JSON instead of just the citekey')
    args = parser.parse_args()

    authors = json.loads(args.authors)
    db = Path(args.database)
    result = resolve(authors, args.year, db, doi=args.doi)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result['citekey'])


if __name__ == '__main__':
    main()
