#!/usr/bin/env python3
"""Export a pinned, reproduced clean tree review to a new workspace directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'review-recheck' / 'recheck.py'
SPEC = importlib.util.spec_from_file_location('export_recheck', SOURCE)
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Refused(ValueError):
    """A valid review is stale, altered or conflicted."""


def destination(path, inputs):
    candidate = Path(path)
    if '..' in candidate.parts:
        raise ValueError('output must not contain parent traversal')
    parent = r.tree.workspace_directory(candidate.parent)
    target = parent / candidate.name
    if not candidate.name or candidate.name in ('.', '..'):
        raise ValueError('output must name a new directory')
    if target.exists() or target.is_symlink():
        raise ValueError('output already exists')
    for source in inputs:
        if target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError('output must be separate from all input trees')
    return target


def export(packet_path, inputs, output, expected_sha256):
    """No input writes; output creation begins only after complete verification."""
    if expected_sha256 is None:
        raise ValueError('an independently retained packet SHA-256 is required')
    saved, digest = r.load_packet(packet_path, expected_sha256)
    sources = [r.tree.workspace_directory(p) for p in inputs]
    target = destination(output, sources)
    current = r.tree.from_directories(sources)
    check = r.compare(saved, current)
    if not check['matches']:
        raise Refused('review does not reproduce: ' + check['status'])
    if not current['clean']:
        raise Refused('conflicted reviews cannot be exported')
    # Export only recomputed candidates, never untrusted saved paths or content.
    files = {}
    deleted = []
    for entry in current['files']:
        name = entry['path']
        parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or not parts.parts:
            raise ValueError('invalid candidate path')
        if entry['candidate'] is None:
            if entry['status'] != 'deleted':
                raise ValueError('non-deletion has no candidate')
            deleted.append(name)
        else:
            data = entry['candidate'].encode('utf-8')
            if hashlib.sha256(data).hexdigest() != entry['candidate_sha256']:
                raise ValueError('candidate fingerprint mismatch')
            files[name] = data
    # Assumes a stable trusted workspace: no concurrent filesystem replacement.
    # mkdir is exclusive; do not clean up a directory we did not create.
    target.mkdir()
    try:
        for name, data in sorted(files.items()):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(data)
        exported = r.tree.snapshot(target, [0])
        if exported['files'] != {p: b.decode('utf-8') for p, b in files.items()}:
            raise ValueError('export verification failed')
        receipt = {
            'schema': 'candidate-export/v1', 'packet_sha256': digest,
            'review_matches': True, 'clean': True,
            'output': target.relative_to(Path.cwd().resolve()).as_posix(),
            'manifest': r.tree.manifest(exported),
            'files': {p: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
                      for p, b in sorted(files.items())},
            'omitted_deletions': deleted,
            'limits': [
                'Candidate only: not approval or semantic correctness.',
                'Inputs and output parent must stay stable during the operation.',
                'No atomic filesystem snapshot or crash-safe publication.',
                'No permissions, renames, binary files or empty-directory merge.',
                'Packet hash must be retained independently; it is not author identity.',
                'An interrupted process may leave an incomplete output directory.']}
    except BaseException:
        shutil.rmtree(target)
        raise
    return receipt


def demo():
    # In-memory demo also works in a read-only checkout; real filesystem tests
    # below exercise the actual exporter with independently pinned packets.
    report = r.tree.demo(False)
    files = {e['path']: e['candidate'] for e in report['files']
             if e['candidate'] is not None}
    return {'schema': 'candidate-export-demo/v1', 'clean': report['clean'],
            'candidates': files,
            'omitted_deletions': [e['path'] for e in report['files']
                                  if e['status'] == 'deleted'],
            'note': 'Preview only; no files written. Run tests for filesystem export.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='PACKET BASE OURS THEIRS OUTPUT')
    parser.add_argument('--expected-sha256')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    if args.demo and (args.paths or args.expected_sha256) or not args.demo and (
            len(args.paths) != 5 or not args.expected_sha256):
        parser.error('use --demo or PACKET BASE OURS THEIRS OUTPUT --expected-sha256 HASH')
    try:
        result = demo() if args.demo else export(
            args.paths[0], args.paths[1:4], args.paths[4], args.expected_sha256)
    except Refused as error:
        print('candidate-export: ' + ascii(str(error)), file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print('candidate-export: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
