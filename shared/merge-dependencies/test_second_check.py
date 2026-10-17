import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import second_check as tool


def text(data):
    return json.dumps(data, indent=2) + '\n'


class SecondCheckTests(unittest.TestCase):
    def setUp(self):
        self.data = {'packages': {'app': {'1': {}, '2': {}}}, 'roots': {'app': '*'}}
        self.text = text(self.data)

    def test_real_merge_incompatible(self):
        report = tool.demo()
        self.assertEqual(report['status'], 'unsatisfiable')
        self.assertTrue(report['review']['merge']['clean'])
        self.assertEqual(report['enumeration']['checked_assignments'], report['enumeration']['candidate_assignments'])
        self.assertGreater(report['enumeration']['checked_assignments'], 0)

    def test_resolved_checks_assignment(self):
        report = tool.check(self.text, self.text, self.text)
        self.assertEqual(report['status'], 'resolved')
        self.assertEqual(report['assignment_check']['status'], 'verified')
        self.assertEqual(tool.exit_code(report), 0)

    def test_both_budget_limits_remain_inconclusive(self):
        self.assertEqual(tool.demo(max_assignments=1)['status'], 'inconclusive')
        self.assertEqual(tool.demo(max_steps=1)['status'], 'inconclusive')
        self.assertEqual(tool.demo(max_steps=2)['status'], 'inconclusive')

    def test_text_conflict_skips_both_searches(self):
        with patch.object(tool.exhaustive, 'exhaustive', side_effect=AssertionError):
            report = tool.check('base\n', 'ours\n', 'theirs\n')
        self.assertEqual(report['status'], 'text_conflict')
        self.assertIsNone(report['enumeration'])

    def test_invalid_json_and_grammar(self):
        for data in ('not json', '{"roots":NaN}', '{"packages":{},"packages":{},"roots":{"a":"*"}}',
                     text({'packages': {}, 'roots': {'a': '^1'}})):
            with self.subTest(data=data):
                self.assertEqual(tool.check(data, data, data)['status'], 'invalid_catalog')

    def test_false_unsatisfiable_detected(self):
        fake = tool.first.check(self.text, self.text, self.text)
        fake['status'] = 'unsatisfiable'
        fake['dependencies'] = {'status': 'unsatisfiable'}
        with patch.object(tool.first, 'check', return_value=fake):
            result = tool.check(self.text, self.text, self.text)
        self.assertEqual(result['status'], 'disagreement')
        self.assertEqual(tool.exit_code(result), 4)

    def test_invalid_assignment_detected(self):
        fake = tool.first.check(self.text, self.text, self.text)
        fake['dependencies']['selected'] = {'app': '99'}
        with patch.object(tool.first, 'check', return_value=fake):
            result = tool.check(self.text, self.text, self.text)
        self.assertEqual(result['status'], 'disagreement')
        self.assertEqual(result['assignment_check']['status'], 'rejected')

    def test_enumerator_does_not_call_solver(self):
        with patch.object(tool.exhaustive.fmt, 'solve', side_effect=AssertionError), \
             patch.object(tool.exhaustive.fmt, 'accepts', side_effect=AssertionError):
            self.assertEqual(tool.exhaustive.exhaustive(self.data)['status'], 'resolved')

    def test_budget_validation(self):
        for budget in (0, -1, True, 1000001):
            for arg in ('max_steps', 'max_assignments'):
                with self.assertRaises(ValueError):
                    tool.check(self.text, self.text, self.text, **{arg: budget})

    def test_determinism_and_symmetry(self):
        original = tool.demo()
        texts = [tool.first.review.engine.read_text(tool.first.HERE/'examples'/(n+'.json'))
                 for n in ('base', 'ours', 'theirs')]
        swapped = tool.check(texts[0], texts[2], texts[1])
        self.assertEqual(original['enumeration'], swapped['enumeration'])
        self.assertEqual(original, tool.demo())

    def test_cli_input_preservation_and_relocation(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            folder = Path(tmp)/'portable'
            shutil.copytree(tool.first.HERE, folder, ignore=shutil.ignore_patterns('__pycache__'))
            script = folder/'second_check.py'
            command = [sys.executable, '-B', str(script)]
            before = {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            proc = subprocess.run(command+['demo'], capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['status'], 'unsatisfiable')
            files = [str(folder/'examples'/(n+'.json')) for n in ('base','ours','theirs')]
            for args, expected in [(['check',*files],1),
                                   (['check',*files,'--max-assignments','1'],3),
                                   (['check','../not-read','../not-read','../not-read'],2),
                                   (['demo','--max-steps','0'],2)]:
                proc = subprocess.run(command+args, capture_output=True)
                self.assertEqual(proc.returncode, expected, proc.stderr)
            after = {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
