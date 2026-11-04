import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json_to_data_report as report


class ReportTests(unittest.TestCase):
    def test_historical_counts_and_pdf(self):
        datasets, failures = report.discover_reports()
        self.assertFalse(failures)
        historical = [d for d in datasets if 'historical' in d['subtitle']]
        self.assertEqual(len(historical), 2)
        self.assertEqual(sorted(sum(c['count'] for c in d['cells'].values()) for d in historical), [35, 157])
        self.assertTrue(all(sum(c['total'] for c in d['cells'].values()) == 320 for d in historical))
        pdf = report.PDF()
        for dataset in historical:
            report.render_report(pdf, dataset)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.pdf'
            pdf.save(path)
            content = path.read_bytes()
            start = int(content.rsplit(b'startxref\n', 1)[1].splitlines()[0])
            self.assertEqual(content[start:start+4], b'xref')
            self.assertEqual(len(pdf.pages), 4)

    def test_run_uses_latest_record_and_keeps_missing_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'runs' / 'sample'
            folder.mkdir(parents=True)
            cfg = dict(models=['test', 'missing'], cases=[dict(id='a', prompt='Question?', task='language_detection')], trials=1, judge_model='judge')
            (folder / 'config.json').write_text(json.dumps(cfg))
            initial = dict(key='one', model='test', case_id='a')
            final = {**initial, 'judgment': dict(idiom=True, metaphor_or_analogy=False, idiom_evidence=['spilled the beans'], rationale='Idiom')}
            (folder / 'records.jsonl').write_text('\n'.join(json.dumps(r) for r in [initial, final]))
            with patch.object(report, 'BASE_DIRECTORY', root):
                datasets = report.load_run(folder)
            self.assertEqual(len(datasets), 2)
            idiom = datasets[0]['cells']
            self.assertEqual(idiom[('test', 'a')]['total'], 1)
            self.assertEqual(idiom[('test', 'a')]['count'], 1)
            self.assertEqual(idiom[('missing', 'a')]['total'], 0)
