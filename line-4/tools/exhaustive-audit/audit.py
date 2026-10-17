#!/usr/bin/env python3
"""Bounded Cartesian compatibility checks, independent of the resolver search."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parent.parent / 'offline-resolver' / 'resolve.py'
if not ENGINE.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('catalog_format', ENGINE)
fmt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmt)
Invalid = fmt.Invalid


def matches(release, constraint):
    # Share input grammar only; do not call accepts() or solve().
    value = fmt.version(release)
    for op, bound in fmt.constraint(constraint):
        comparison = (value > bound) - (value < bound)
        if not {'==': comparison == 0, '!=': comparison != 0,
                '>': comparison > 0, '<': comparison < 0,
                '>=': comparison >= 0, '<=': comparison <= 0}[op]:
            return False
    return True


def assignment(packages, roots, selected):
    """Return only the reachable closure, or None for a violated edge."""
    todo = list(roots.items())
    reached = set()
    while todo:
        package, constraint = todo.pop()
        release = selected.get(package)
        if not isinstance(release, str) or release not in packages.get(package, {}) or not matches(release, constraint):
            return None
        if package not in reached:
            reached.add(package)
            todo.extend(packages[package][release].items())
    return {p: selected[p] for p in sorted(reached)}


def exhaustive(data, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise Invalid('max_assignments must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    # Include every dependency of every potentially reachable release. This is
    # an overapproximation; it cannot omit a package from a valid solution.
    possible, todo = set(), list(roots)
    while todo:
        p = todo.pop()
        if p in possible:
            continue
        possible.add(p)
        for deps in packages.get(p, {}).values():
            todo.extend(q for q in deps if q not in possible)
    names = sorted(possible)
    domains = []
    total = 1
    for p in names:
        versions = sorted(packages.get(p, {}), key=fmt.version)
        # Roots are mandatory; nonroots can be absent in some branches.
        domain = [v for v in versions if matches(v, roots[p])] if p in roots else [None] + versions
        domains.append(domain)
        total *= len(domain)
    base = {'method': 'exhaustive-cartesian-v1', 'candidate_assignments': total,
            'max_assignments': max_assignments, 'possible_packages': names}
    checked = 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            return dict(base, status='inconclusive', checked_assignments=checked,
                        reason='assignment budget exhausted')
        checked += 1
        selected = assignment(packages, roots, dict(zip(names, values)))
        if selected is not None:
            return dict(base, status='resolved', checked_assignments=checked, selected=selected)
    return dict(base, status='unsatisfiable', checked_assignments=checked)


def audit(data, report, max_assignments=10000):
    packages, roots = fmt.validate(data)
    if not isinstance(report, dict) or report.get('status') not in ('resolved', 'unsatisfiable'):
        raise Invalid('report must claim resolved or unsatisfiable')
    if report['status'] == 'resolved':
        chosen = report.get('selected')
        if not isinstance(chosen, dict):
            raise Invalid('missing selected versions')
        projected = assignment(packages, roots, chosen)
        if projected is None or projected != chosen:
            raise Invalid('invalid or unreachable selected versions')
        return {'status': 'verified', 'claim': 'resolved', 'selected': projected}
    # This checks the original catalog, never trusts a supplied core, digest,
    # representative failed branch, or solver search count.
    result = exhaustive(data, max_assignments)
    if result['status'] == 'resolved':
        return {'status': 'rejected', 'reason': 'catalog has a solution', 'counterexample': result}
    if result['status'] == 'inconclusive':
        return result
    return {'status': 'verified', 'claim': 'unsatisfiable', 'exhaustion': result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace JSON, or demo for stored real Requests conflict')
    parser.add_argument('--report', help='optional resolver/core report to check against the entire catalog')
    parser.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        path = ENGINE.parent.parent / 'conflict-core/examples/requests-conflict.json' if args.catalog == 'demo' else args.catalog
        data = fmt.load(path)
        result = (audit(data, fmt.load(args.report), args.max_assignments) if args.report
                  else exhaustive(data, args.max_assignments))
        code = {'resolved': 0, 'verified': 0, 'unsatisfiable': 1,
                'rejected': 1, 'inconclusive': 3}[result['status']]
        if args.catalog == 'demo' and not args.report and result['status'] == 'unsatisfiable':
            result = {'status': 'verified', 'demonstration': result}
            code = 0
    except (Invalid, OSError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
