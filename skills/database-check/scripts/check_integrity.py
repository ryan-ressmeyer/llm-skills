#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Check integrity of the literature database.
Validates folder structure, index.yaml consistency, references.bib sync,
and related papers files.
"""

import sys
import re
import json
import argparse
from pathlib import Path

import yaml


ID_PATTERN = re.compile(r'^[a-z]+-[a-z]+-\d{4}[a-z]?$|^[a-z]+-\d{4}[a-z]?$')
QLMRI_SECTIONS = ['Citation', 'Questions', 'Logic', 'Methods', 'Results', 'Inferences']


def resolve_paths(paper: dict, db: Path) -> dict:
    """Resolve filesystem paths for a paper entry.

    Reads explicit `pdf_path`, `summary_path`, `note_path`, `graph_dir` fields
    from the entry when present. Falls back to the legacy nested layout
    (`<id>/<id>.pdf`, `<id>/<id>-summary.md`, `<id>/`) when fields are absent.
    """
    pid = paper.get('id', '')
    nested_dir = db / pid

    pdf_field = paper.get('pdf_path')
    summary_field = paper.get('summary_path')
    note_field = paper.get('note_path')
    graph_field = paper.get('graph_dir')

    pdf = (db / pdf_field) if pdf_field else (nested_dir / f'{pid}.pdf')
    summary = (db / summary_field) if summary_field else (nested_dir / f'{pid}-summary.md')
    note = (db / note_field) if note_field else None
    graph_dir = (db / graph_field) if graph_field else nested_dir

    return {
        'id': pid,
        'pdf': pdf,
        'summary': summary,
        'note': note,
        'graph_dir': graph_dir,
        'is_flat': bool(pdf_field or note_field or summary_field or graph_field),
    }


class IntegrityChecker:
    """Check literature database integrity."""

    def __init__(self, db_path: str, verbose: bool = False):
        self.db = Path(db_path)
        self.verbose = verbose
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.auto_fixable: list[dict] = []
        self.index_data: dict = {}
        self.papers: list[dict] = []

    def run(self) -> dict:
        """Run all integrity checks and return report."""
        if not self.db.exists():
            self.errors.append({
                'type': 'missing_database',
                'message': f'Database directory not found: {self.db}',
                'path': str(self.db),
            })
            return self._report()

        self._load_index()
        self._check_folders()
        self._check_index_entries()
        self._check_flags()
        self._check_themes()
        self._check_bibtex()
        self._check_related_files()
        self._check_duplicates()
        self._check_summaries()

        return self._report()

    def _load_index(self):
        index_path = self.db / 'index.yaml'
        if not index_path.exists():
            self.warnings.append({
                'type': 'missing_index',
                'message': 'index.yaml not found — database may be empty',
                'path': str(index_path),
            })
            return
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                self.index_data = yaml.safe_load(f) or {}
            self.papers = self.index_data.get('papers', [])
        except Exception as e:
            self.errors.append({
                'type': 'invalid_index',
                'message': f'Could not parse index.yaml: {e}',
                'path': str(index_path),
            })

    def _check_folders(self):
        """Check legacy nested-layout folders. Skips flat-layout artifacts (pdfs/, etc.)."""
        # Folders that exist for layout reasons, not as per-paper directories
        skip = {'themes', 'pdfs', 'graph'}
        # Build a set of nested-layout dirs that are actually referenced via the
        # entry's `graph_dir` (which defaults to <id>/ in the nested layout).
        # We won't flag those, since flat-layout entries may use sibling dirs.
        index_ids = {p.get('id') for p in self.papers}
        # Index of explicitly-flat IDs — their nested folder absence is fine
        flat_ids = {p.get('id') for p in self.papers
                    if any(k in p for k in ('pdf_path', 'note_path', 'summary_path', 'graph_dir'))}

        for item in sorted(self.db.iterdir()):
            if not item.is_dir():
                continue
            if item.name in skip or item.name.startswith('.'):
                continue
            folder_id = item.name

            # Check naming convention
            if not ID_PATTERN.match(folder_id):
                # Not a per-paper folder — ignore (likely user organization)
                continue

            # Check for expected files (nested layout)
            pdf = item / f'{folder_id}.pdf'
            summary = item / f'{folder_id}-summary.md'
            if not pdf.exists() and not summary.exists():
                self.warnings.append({
                    'type': 'empty_folder',
                    'message': f'Folder "{folder_id}" has no PDF or summary',
                    'path': str(item),
                })

            # Check for corresponding index entry
            if folder_id not in index_ids:
                self.errors.append({
                    'type': 'orphaned_folder',
                    'message': f'Folder "{folder_id}" has no entry in index.yaml',
                    'path': str(item),
                })

    def _check_index_entries(self):
        """Check that resolved paths for each entry exist."""
        for paper in self.papers:
            paths = resolve_paths(paper, self.db)
            pid = paths['id']
            # In nested layout, the per-paper folder must exist as the anchor.
            # In flat layout, we instead require the note (if declared) or pdf to exist.
            if paths['is_flat']:
                if paths['note'] is not None and not paths['note'].exists():
                    self.errors.append({
                        'type': 'missing_note',
                        'message': f'Index entry "{pid}" declares note_path but file is missing',
                        'path': str(paths['note']),
                    })
            else:
                folder = self.db / pid
                if not folder.exists():
                    self.errors.append({
                        'type': 'missing_folder',
                        'message': f'Index entry "{pid}" has no corresponding folder',
                        'path': str(folder),
                    })

    def _check_flags(self):
        """Check has_pdf and has_summary flags match reality."""
        for paper in self.papers:
            paths = resolve_paths(paper, self.db)
            pid = paths['id']

            pdf_exists = paths['pdf'].exists()
            summary_exists = paths['summary'].exists()
            has_pdf = paper.get('has_pdf', False)
            has_summary = paper.get('has_summary', False)
            folder = paths['pdf'].parent

            if has_pdf != pdf_exists:
                self.warnings.append({
                    'type': 'flag_mismatch',
                    'message': f'{pid}: has_pdf={has_pdf} but PDF {"exists" if pdf_exists else "missing"}',
                    'path': str(folder),
                })
                self.auto_fixable.append({
                    'type': 'fix_has_pdf',
                    'description': f'Set has_pdf={pdf_exists} for {pid}',
                    'paper_id': pid,
                    'field': 'has_pdf',
                    'value': pdf_exists,
                })

            if has_summary != summary_exists:
                self.warnings.append({
                    'type': 'flag_mismatch',
                    'message': f'{pid}: has_summary={has_summary} but summary {"exists" if summary_exists else "missing"}',
                    'path': str(folder),
                })
                self.auto_fixable.append({
                    'type': 'fix_has_summary',
                    'description': f'Set has_summary={summary_exists} for {pid}',
                    'paper_id': pid,
                    'field': 'has_summary',
                    'value': summary_exists,
                })

    def _check_themes(self):
        """Check theme documents exist and are non-empty."""
        themes_dir = self.db / 'themes'
        if not themes_dir.exists():
            return
        for theme_file in themes_dir.glob('*.md'):
            if theme_file.stat().st_size == 0:
                self.warnings.append({
                    'type': 'empty_theme_file',
                    'message': f'Theme file {theme_file.name} is empty',
                    'path': str(theme_file),
                })

    def _check_bibtex(self):
        """Check references.bib has entries for all papers."""
        bib_path = self.db / 'references.bib'
        if not bib_path.exists():
            if self.papers:
                self.warnings.append({
                    'type': 'missing_bibtex',
                    'message': 'references.bib not found',
                    'path': str(bib_path),
                })
            return

        content = bib_path.read_text(encoding='utf-8')
        # Extract citation keys from bibtex
        bib_keys = set(re.findall(r'@\w+\s*\{([^,]+),', content))

        for paper in self.papers:
            pid = paper.get('id', '')
            if pid and pid not in bib_keys:
                self.warnings.append({
                    'type': 'missing_bib_entry',
                    'message': f'No BibTeX entry for "{pid}" in references.bib',
                    'path': str(bib_path),
                })

    def _check_related_files(self):
        """Check structure of related papers YAML files."""
        for paper in self.papers:
            paths = resolve_paths(paper, self.db)
            pid = paths['id']
            folder = paths['graph_dir']
            if not folder.exists():
                continue

            for fname, key in [('references.yaml', 'references'),
                               ('cited-by.yaml', 'cited_by'),
                               ('related.yaml', 'related')]:
                fpath = folder / fname
                if not fpath.exists():
                    continue
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if data is None:
                        continue
                    if not isinstance(data, dict) or key not in data:
                        self.warnings.append({
                            'type': 'invalid_related_file',
                            'message': f'{pid}/{fname}: expected top-level key "{key}"',
                            'path': str(fpath),
                        })
                except Exception as e:
                    self.warnings.append({
                        'type': 'unparseable_yaml',
                        'message': f'{pid}/{fname}: {e}',
                        'path': str(fpath),
                    })

    def _check_duplicates(self):
        """Check for duplicate DOIs in index."""
        dois = {}
        for paper in self.papers:
            doi = paper.get('doi', '')
            if doi:
                doi_lower = doi.lower()
                if doi_lower in dois:
                    self.errors.append({
                        'type': 'duplicate_doi',
                        'message': f'DOI "{doi}" appears in both "{dois[doi_lower]}" and "{paper.get("id")}"',
                        'path': str(self.db / 'index.yaml'),
                    })
                else:
                    dois[doi_lower] = paper.get('id', '')

    def _check_summaries(self):
        """Check summary files follow QLMRI structure."""
        for paper in self.papers:
            paths = resolve_paths(paper, self.db)
            pid = paths['id']
            summary_path = paths['summary']
            if not summary_path.exists():
                continue
            try:
                content = summary_path.read_text(encoding='utf-8')
                for section in QLMRI_SECTIONS:
                    if f'## {section}' not in content:
                        self.warnings.append({
                            'type': 'missing_qlmri_section',
                            'message': f'{pid}: summary missing "## {section}" section',
                            'path': str(summary_path),
                        })
            except Exception as e:
                self.warnings.append({
                    'type': 'unreadable_summary',
                    'message': f'{pid}: could not read summary: {e}',
                    'path': str(summary_path),
                })

    def apply_fixes(self):
        """Apply auto-fixable issues."""
        if not self.auto_fixable:
            return
        index_path = self.db / 'index.yaml'
        if not index_path.exists():
            return
        for fix in self.auto_fixable:
            pid = fix.get('paper_id')
            field = fix.get('field')
            value = fix.get('value')
            for paper in self.papers:
                if paper.get('id') == pid:
                    paper[field] = value
                    print(f'Fixed: {pid}.{field} = {value}', file=sys.stderr)

        self.index_data['papers'] = self.papers
        with open(index_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.index_data, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False, width=120)
        print(f'Applied {len(self.auto_fixable)} fixes to index.yaml', file=sys.stderr)

    def _report(self) -> dict:
        papers_with_pdf = sum(1 for p in self.papers if p.get('has_pdf'))
        papers_with_summary = sum(1 for p in self.papers if p.get('has_summary'))
        themes_dir = self.db / 'themes'
        total_themes = len(list(themes_dir.glob('*.md'))) if themes_dir.exists() else 0

        return {
            'stats': {
                'total_papers': len(self.papers),
                'papers_with_pdf': papers_with_pdf,
                'papers_with_summary': papers_with_summary,
                'total_themes': total_themes,
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'auto_fixable': len(self.auto_fixable),
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'auto_fixable': self.auto_fixable,
        }


def main():
    parser = argparse.ArgumentParser(
        description='Check literature database integrity',
        epilog='Example: uv run check_integrity.py references/ --verbose',
    )
    parser.add_argument('database', nargs='?', default='references/', help='Database path (default: references/)')
    parser.add_argument('--fix', action='store_true', help='Auto-fix trivial issues')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-o', '--output', help='Save report to JSON file')
    args = parser.parse_args()

    checker = IntegrityChecker(args.database, verbose=args.verbose)
    report = checker.run()

    if args.fix and report['auto_fixable']:
        checker.apply_fixes()
        # Re-run to get updated report
        checker2 = IntegrityChecker(args.database, verbose=args.verbose)
        report = checker2.run()

    output = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'Report saved to {args.output}', file=sys.stderr)
    else:
        print(output)

    # Summary to stderr
    s = report['stats']
    print(f'\nDatabase: {args.database}', file=sys.stderr)
    print(f'Papers: {s["total_papers"]} ({s["papers_with_pdf"]} with PDF, {s["papers_with_summary"]} with summary)', file=sys.stderr)
    print(f'Themes: {s["total_themes"]}', file=sys.stderr)
    print(f'Issues: {s["errors"]} errors, {s["warnings"]} warnings', file=sys.stderr)
    if s['auto_fixable'] and not args.fix:
        print(f'{s["auto_fixable"]} issues can be auto-fixed with --fix', file=sys.stderr)


if __name__ == '__main__':
    main()
