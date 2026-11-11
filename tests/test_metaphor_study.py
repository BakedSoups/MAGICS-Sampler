import json
from pathlib import Path
import tempfile
import unittest
from run_metaphor_study import schedule, validate, judge_format
from report_metaphor_study import pearson, ranks, report, choice_label


class MetaphorStudyTests(unittest.TestCase):
    def test_design_and_dependencies(self):
        for name, count in [('creation',9),('triggers',12),('context',54)]:
            cfg=json.loads(Path(f'experiments/metaphor_{name}.json').read_text())
            self.assertEqual(len(cfg['cases']), count)
            done=set()
            for model, case, trial in schedule(cfg):
                if case.get('depends_on'):
                    self.assertIn((model,case['depends_on'],trial),done)
                done.add((model,case['id'],trial))
            self.assertEqual(len(done),count*5)
        with self.assertRaises(ValueError):
            schedule(dict(models=['m'],trials=1,random_seed=1,cases=[dict(id='x',depends_on='missing')]))

    def test_evidence_and_conditional_scores(self):
        value=dict(comparisons=[dict(evidence='leaking tank',source_domain='container',supported_links=['loss'],false_implications=[])],conventional_metaphor_evidence=[],idiom_evidence=[],adaptation_success=None,limitation_success=None,rationale='Maps loss')
        validate(value,dict(condition='generate'),'A leaking tank')
        with self.assertRaises(ValueError):
            validate(value,dict(condition='generate'),'Plain answer')
        with self.assertRaises(ValueError):
            validate(value,dict(condition='adapt'),'A leaking tank')

    def test_conditional_schema_and_deterministic_choices(self):
        for condition, kind in [('generate','null'),('adapt','boolean'),('limits','null')]:
            schema=judge_format(dict(condition=condition))
            self.assertTrue(schema['strict'])
            self.assertEqual(schema['schema']['properties']['adaptation_success']['type'],kind)
        self.assertEqual(choice_label('A\nBecause this preserves the relation.'),'A')
        self.assertEqual(choice_label('**B**\nExplanation.'),'B')
        self.assertIsNone(choice_label('I think A is correct.'))
        self.assertIsNone(choice_label(''))

    def test_correlations_and_ties(self):
        self.assertAlmostEqual(pearson([1,2,3],[3,2,1]),-1)
        self.assertIsNone(pearson([1,1,1],[1,2,3]))
        self.assertIsNone(pearson([1,2],[2,3]))
        self.assertEqual(ranks([2,1,2]),[2.5,1,2.5])

    def test_report_deduplicates_excludes_missing_and_preserves_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); run=root/'run'; run.mkdir(); out=root/'out'
            cfg=dict(models=['m'],trials=2,cases=[dict(id='a',system='nava',condition='generate')])
            experiment=root/'experiment.json'; experiment.write_text(json.dumps(cfg))
            r=dict(key='one',model='m',resolved_model='m-dated',case_id='a',trial=1,prompt='rules',response='A tank',judgment=dict(comparisons=[],adaptation_success=None,limitation_success=None))
            pending=dict(r,key='two',trial=2); del pending['judgment']
            (run/'records.jsonl').write_text('\n'.join(json.dumps(x) for x in [r,r,pending]))
            rows,_=report(experiment,run,out)
            self.assertEqual(len(rows),1)
            self.assertEqual(json.loads((out/'summary.json').read_text())[0]['judged'],1)
            (out/'human_review.csv').write_text('human annotation')
            report(experiment,run,out)
            self.assertEqual((out/'human_review.csv').read_text(),'human annotation')
            self.assertTrue((out/'human_review_fresh.csv').exists())
