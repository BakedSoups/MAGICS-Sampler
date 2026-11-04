import json
from pathlib import Path
import unittest
from run_experiment import summarize, validate_judgment
from run_experiment import judge_response
from types import SimpleNamespace
from unittest.mock import Mock


class ExperimentTests(unittest.TestCase):
    def test_judge_retries_invalid_evidence(self):
        valid = dict(metaphor_or_analogy=False, idiom=True, metaphor_evidence=[], idiom_evidence=['spilled the beans'], rationale='Idiomatic disclosure')
        invalid = {**valid, 'idiom_evidence': ['spill the beans']}
        client = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=[SimpleNamespace(status='completed', output_text=json.dumps(v)) for v in [invalid, valid]])))
        _, result = judge_response(client, {'judge_model': 'test', 'max_output_tokens': 100}, {'task': 'language_detection'}, 'She spilled the beans.')
        self.assertEqual(result, valid)
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertIn('correction', json.loads(client.responses.create.call_args.kwargs['input']))

    def test_screenshot_totals(self):
        data = {'experiments': [json.loads((Path('runs/metaphors_based_on_role') / name).read_text())['experiments'][0] for name in ['random_forest.json', 'water_temperature.json']]}
        for experiment, expected in zip(data['experiments'], [[9, 80, 61, 7], [0, 35, 0, 0]]):
            self.assertEqual(sum(r['total_responses'] for r in experiment['results']), 320)
            self.assertEqual([s['metaphor_or_analogy_count'] for s in experiment['summary']], expected)
            for i, audience in enumerate(experiment['prompts']):
                cells = [r for r in experiment['results'] if r['audience'] == audience]
                self.assertEqual(sum(r['metaphor_or_analogy_count'] for r in cells), expected[i])
                for cell in cells:
                    self.assertEqual(cell['percentage'], cell['metaphor_or_analogy_count'] * 5)

    def test_judge_cannot_invent_evidence(self):
        judgment = dict(metaphor_or_analogy=False, idiom=True, metaphor_evidence=[], idiom_evidence=['spill the beans'], rationale='Conventional idiom')
        self.assertEqual(validate_judgment(judgment, {'task': 'language_detection'}, 'Please spill the beans.'), judgment)
        with self.assertRaises(ValueError):
            validate_judgment(judgment, {'task': 'language_detection'}, 'Plain literal answer.')

    def test_unjudged_responses_are_excluded_from_percentage(self):
        rows = [dict(model='test', case_id='a', task='idiom_comprehension'), dict(model='test', case_id='a', task='idiom_comprehension', judgment=dict(correct_kind=True, correct_meaning=False))]
        summary = summarize(rows)[0]
        self.assertEqual(summary['responses'], 2)
        self.assertEqual(summary['judged'], 1)
        self.assertEqual(summary['metrics']['correct_kind']['percentage'], 100)
        self.assertEqual(summary['metrics']['correct_meaning']['percentage'], 0)


if __name__ == '__main__':
    unittest.main()
