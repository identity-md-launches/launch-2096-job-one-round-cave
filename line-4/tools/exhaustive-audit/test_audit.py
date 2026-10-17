import copy
import importlib.util
from pathlib import Path
import random
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class ExhaustiveTests(unittest.TestCase):
    def catalog(self):
        return {'packages': {'app': {'1': {'dep': '==1'}, '2': {'dep': '==2'}},
                             'dep': {'1': {}, '2': {}}}, 'roots': {'app': '*'}}

    def test_abandoned_release_dependencies(self):
        data = {'packages': {'app': {'1': {'missing': '*'}, '2': {}}}, 'roots': {'app': '*'}}
        self.assertEqual(a.exhaustive(data)['selected'], {'app': '2'})

    def test_unreachable_empty_package(self):
        data = self.catalog()
        data['packages']['unused'] = {}
        self.assertEqual(a.exhaustive(data)['status'], 'resolved')

    def test_missing_root_and_impossible_constraint(self):
        for data in ({'packages': {}, 'roots': {'missing': '*'}},
                     {'packages': {'a': {'1': {}}}, 'roots': {'a': '>2'}}):
            result = a.exhaustive(data, 1)
            self.assertEqual(result['status'], 'unsatisfiable')
            self.assertEqual(result['checked_assignments'], 0)

    def test_cycles(self):
        data = {'packages': {'a': {'1': {'b': '*'}}, 'b': {'1': {'a': '==1'}}}, 'roots': {'a': '*'}}
        self.assertEqual(a.exhaustive(data)['selected'], {'a': '1', 'b': '1'})
        data['packages']['b']['1']['a'] = '==2'
        self.assertEqual(a.exhaustive(data)['status'], 'unsatisfiable')

    def test_numeric_comparisons(self):
        for op, yes in [('==', True), ('!=', False), ('<', False), ('>', False), ('<=', True), ('>=', True)]:
            self.assertEqual(a.matches('2', op + '2.0.0'), yes)
        self.assertTrue(a.matches('10', '>2,<11,!=3'))

    def test_budget_exact_completion(self):
        data = {'packages': {'a': {'1': {'b': '==2'}}, 'b': {'1': {}}}, 'roots': {'a': '*'}}
        self.assertEqual(a.exhaustive(data, 1)['status'], 'inconclusive')
        self.assertEqual(a.exhaustive(data, 2)['status'], 'unsatisfiable')

    def test_budget_before_later_solution(self):
        data = self.catalog()
        self.assertEqual(a.exhaustive(data, 1)['status'], 'inconclusive')
        self.assertEqual(a.exhaustive(data, 2)['status'], 'resolved')

    def test_invalid_budgets_and_catalogs(self):
        for value in (True, 0, -1, 1000001, 2.5):
            with self.assertRaises(a.Invalid):
                a.exhaustive(self.catalog(), value)
        with self.assertRaises(a.Invalid):
            a.exhaustive({'packages': {}, 'roots': {}})

    def test_no_original_solver_or_accepts_called(self):
        old_solve, old_accepts = a.fmt.solve, a.fmt.accepts
        def forbidden(*args):
            raise AssertionError('original search/predicate called')
        try:
            a.fmt.solve = a.fmt.accepts = forbidden
            self.assertEqual(a.exhaustive(self.catalog())['status'], 'resolved')
            self.assertEqual(a.audit(self.catalog(), {'status': 'unsatisfiable'})['status'], 'rejected')
        finally:
            a.fmt.solve, a.fmt.accepts = old_solve, old_accepts

    def test_audit_forged_assignments(self):
        for selected in ({}, {'app': '1'}, {'app': '1', 'dep': '2'},
                         {'app': '2', 'dep': '2', 'unused': '1'}):
            with self.assertRaises(a.Invalid):
                a.audit(self.catalog(), {'status': 'resolved', 'selected': selected})
        self.assertEqual(a.audit(self.catalog(), {'status': 'resolved', 'selected': {'app': '1', 'dep': '1'}})['status'], 'verified')

    def test_unsat_report_and_inconclusive(self):
        data = self.catalog()
        data['roots']['dep'] = '>2'
        self.assertEqual(a.audit(data, {'status': 'unsatisfiable'})['status'], 'verified')
        self.assertEqual(a.audit(self.catalog(), {'status': 'unsatisfiable'}, 1)['status'], 'inconclusive')

    def test_immutable_and_deterministic(self):
        data = self.catalog()
        before = copy.deepcopy(data)
        self.assertEqual(a.exhaustive(data), a.exhaustive(data))
        self.assertEqual(data, before)

    def test_seeded_solver_crosscheck(self):
        rng = random.Random(2304)
        for i in range(500):
            packages = {}
            for p in 'abc':
                packages[p] = {v: {q: rng.choice(['*', '==1', '==2', '>2'])
                                   for q in 'abcx' if rng.random() < .18}
                               for v in ['1', '2'] if rng.random() < .8}
            data = {'packages': packages, 'roots': {p: rng.choice(['*', '==1', '==2'])
                                                    for p in 'abc' if rng.random() < .5} or {'a': '*'}}
            result = a.exhaustive(data)
            self.assertEqual(result['status'], a.fmt.solve(data)['status'], (i, data))
            if result['status'] == 'resolved':
                self.assertIsNotNone(a.assignment(packages, data['roots'], result['selected']))

    def test_real_demo_and_cli(self):
        path = a.ENGINE.parent.parent / 'conflict-core/examples/requests-conflict.json'
        result = a.exhaustive(a.fmt.load(path))
        self.assertEqual(result['status'], 'unsatisfiable')
        for args, expected in [(['demo'], 0), (['demo', '--max-assignments', '1'], 3),
                               ([str(path)], 1), (['demo', '--max-assignments', '0'], 2)]:
            process = subprocess.run([sys.executable, '-B', str(Path(a.__file__)), *args], capture_output=True, text=True)
            self.assertEqual(process.returncode, expected, process.stdout + process.stderr)


if __name__ == '__main__':
    unittest.main()
