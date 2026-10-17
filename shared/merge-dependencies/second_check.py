#!/usr/bin/env python3
"""Review a catalog merge and compare two bounded compatibility searches."""
import argparse
import json
import sys

import check_merge as first
import exhaustive


def check(base, ours, theirs, max_steps=10000, max_assignments=10000):
    first.core.budget(max_steps)
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise ValueError('assignment budget must be an integer from 1 to 1000000')
    merged = first.check(base, ours, theirs, max_steps)
    result = {'format': 'dependency-merge-second-check/v1',
              'status': merged['status'], 'review': merged,
              'enumeration': None, 'assignment_check': None,
              'limits': [
                  'Only finite catalog compatibility is compared; no edits are applied.',
                  'The searches differ but share the numeric catalog parser and grammar.',
                  'Core minimality, diagnostics, publisher trust and installability are not independently checked.',
                  'Budgets limit search work, not elapsed time; incomplete work is inconclusive.']}
    if merged['status'] in ('text_conflict', 'invalid_catalog'):
        return result
    data = first.parse(merged['merge']['merged'])
    other = exhaustive.exhaustive(data, max_assignments)
    result['enumeration'] = other
    claim = merged['dependencies']
    if claim['status'] == 'resolved':
        try:
            result['assignment_check'] = exhaustive.audit(data, claim, max_assignments)
        except ValueError:
            result['assignment_check'] = {'status': 'rejected', 'reason': 'invalid solver assignment'}
            result['status'] = 'disagreement'
            return result
    decided = {'resolved', 'unsatisfiable'}
    if claim['status'] in decided and other['status'] in decided and claim['status'] != other['status']:
        result['status'] = 'disagreement'
    elif merged['status'] not in decided or other['status'] not in decided:
        result['status'] = 'inconclusive'
    else:
        result['status'] = other['status']
    return result


def demo(max_steps=10000, max_assignments=10000):
    texts = [first.review.engine.read_text(first.HERE/'examples'/(n+'.json'))
             for n in ('base', 'ours', 'theirs')]
    return check(*texts, max_steps=max_steps, max_assignments=max_assignments)


def exit_code(result):
    return {'resolved': 0, 'unsatisfiable': 1, 'text_conflict': 1,
            'invalid_catalog': 2, 'inconclusive': 3, 'disagreement': 4}[result['status']]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        p = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                p.add_argument(branch)
        p.add_argument('--max-steps', type=int, default=10000)
        p.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo(args.max_steps, args.max_assignments)
        else:
            texts = [first.review.engine.read_text(p) for p in (args.base, args.ours, args.theirs)]
            result = check(*texts, max_steps=args.max_steps, max_assignments=args.max_assignments)
        code = exit_code(result)
        if args.command == 'demo' and result['status'] == 'unsatisfiable':
            code = 0
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid', 'error': 'Invalid workspace inputs or budgets.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
