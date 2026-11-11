#!/usr/bin/env python3
"""Create a PDF report from saved experiment JSON, using only Python's standard library."""
import json
import math
from pathlib import Path
import textwrap

# Run without flags: python json_to_data_report.py
# Scan result files, not experiment definitions (which contain no findings).
SOURCE_DIRECTORIES = ['data', 'runs']
REPORT_DIRECTORY = 'reports'
BASE_DIRECTORY = Path(__file__).resolve().parent


class PDF:
    """Small vector PDF writer; built-in Helvetica keeps dependencies unnecessary."""
    def __init__(self):
        self.pages = []
        self.commands = []

    def page(self):
        self.commands = []
        self.pages.append(self.commands)

    def text(self, x, y, value, size=10, color=(0.03, 0.13, 0.23)):
        value = str(value).translate(str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-', '…': '...'}))
        value = value.encode('cp1252', errors='replace').decode('cp1252')
        value = value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        self.commands.append(f'BT /F1 {size} Tf {color[0]} {color[1]} {color[2]} rg 1 0 0 1 {x} {595-y} Tm ({value}) Tj ET')

    def rect(self, x, y, w, h, color):
        self.commands.append(f'{color[0]} {color[1]} {color[2]} rg {x} {595-y-h} {w} {h} re f')

    def pie(self, x, y, percent):
        # Filled polygon with 120 segments, rather than a raster image.
        for color, fraction in [((0.84, 0.88, 0.92), 1), ((0, 0.62, 0.58), percent / 100)]:
            if fraction <= 0:
                continue
            points = [(x, 595-y)]
            steps = max(1, math.ceil(fraction * 120))
            for i in range(steps + 1):
                angle = math.pi/2 - 2*math.pi*fraction*i/steps
                points.append((x+23*math.cos(angle), 595-y+23*math.sin(angle)))
            self.commands.append(f'{color[0]} {color[1]} {color[2]} rg ' + f'{points[0][0]} {points[0][1]} m ' + ' '.join(f'{px} {py} l' for px, py in points[1:]) + ' h f')

    def save(self, path):
        objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
        page_ids = []
        for commands in self.pages:
            stream = '\n'.join(commands).encode('cp1252')
            page_id = len(objects) + 1
            page_ids.append(page_id)
            objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R >> >> /Contents {page_id+1} 0 R >>'.encode())
            objects.append(f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'\nendstream')
        objects[1] = f'<< /Type /Pages /Kids [{" ".join(f"{n} 0 R" for n in page_ids)}] /Count {len(page_ids)} >>'.encode()
        output = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = [0]
        for number, obj in enumerate(objects, 1):
            offsets.append(len(output))
            output.extend(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
        start = len(output)
        output.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
        for offset in offsets[1:]:
            output.extend(f'{offset:010d} 00000 n \n'.encode())
        output.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
        path.write_bytes(output)


def load_run(folder):
    cfg = json.loads((folder / 'config.json').read_text())
    records = {}
    source = folder / 'records.jsonl'
    if source.exists():
        for line in source.read_text().splitlines():
            row = json.loads(line)
            records[row['key']] = row
    tasks = {case['task'] for case in cfg['cases']}
    metrics = []
    if 'language_detection' in tasks:
        metrics += ['idiom', 'metaphor_or_analogy']
    if 'idiom_comprehension' in tasks:
        metrics += ['correct_kind', 'correct_meaning']
    reports = []
    for metric in metrics:
        task = 'idiom_comprehension' if metric.startswith('correct_') else 'language_detection'
        cases = [c for c in cfg['cases'] if c['task'] == task]
        cells = {}
        for model in cfg['models']:
            for case in cases:
                rows = [r for r in records.values() if r['model'] == model and r['case_id'] == case['id']]
                judged = [r for r in rows if type(r.get('judgment', {}).get(metric)) is bool]
                positive = [r for r in judged if r['judgment'][metric]]
                example = 'None detected.' if judged else 'Missing or failed trials.'
                if positive:
                    evidence_key = 'idiom_evidence' if metric == 'idiom' else 'metaphor_evidence'
                    evidence = positive[0]['judgment'].get(evidence_key, [])
                    example = ' / '.join(evidence) if evidence else positive[0]['judgment']['rationale']
                cells[(model, case['id'])] = dict(count=len(positive), total=len(judged), example=example,
                    detail=f'{len(positive)}/{len(judged)} judged | {len(rows)}/{cfg["trials"]} responses')
        reports.append(dict(name=folder.name+'_'+metric, title=folder.name.replace('_', ' '), metric=metric,
            subtitle=f'{cfg["trials"]} planned responses per cell | judge: {cfg["judge_model"]}',
            models=cfg['models'], cases=cases, cells=cells,
            footer='Automated judgments; percentages use judged responses only. Missing results are not counted as negatives.',
            source=str(folder.relative_to(BASE_DIRECTORY))+'/records.jsonl'))
    return reports


def load_observed(path, data):
    reports = []
    for experiment in data['experiments']:
        cases = [dict(id=audience, prompt=prompt) for audience, prompt in experiment['prompts'].items()]
        cells = {}
        for r in experiment['results']:
            count, total = r['metaphor_or_analogy_count'], r['total_responses']
            cells[(r['model'], r['audience'])] = dict(count=count, total=total,
                example=r.get('example_excerpt') or 'None detected.', detail=f'{count}/{total} responses')
        reports.append(dict(name=path.stem+'_'+experiment['id'], title=experiment['title'], metric='metaphor_or_analogy',
            subtitle=f'{experiment["total_responses"]} responses | historical screenshot findings',
            models=data['models'], cases=cases, cells=cells,
            footer='Screenshot transcription: aggregate counts and displayed excerpts only. Original full responses and judge settings unavailable.',
            source=str(path.relative_to(BASE_DIRECTORY))))
    return reports


def discover_reports():
    reports, failures = [], []
    seen_runs = set()
    for directory in SOURCE_DIRECTORIES:
        root = BASE_DIRECTORY / directory
        if not root.exists():
            continue
        for path in sorted(root.rglob('*.json')):
            try:
                data = json.loads(path.read_text())
                if isinstance(data, dict) and 'experiments' in data and 'trials_per_model_per_prompt' in data:
                    reports.extend(load_observed(path, data))
                elif path.name == 'config.json' and isinstance(data, dict) and 'cases' in data and 'models' in data:
                    if path.parent not in seen_runs:
                        reports.extend(load_run(path.parent))
                        seen_runs.add(path.parent)
                # summary.json duplicates records; errors and prompt-only configs aren't findings.
            except (ValueError, KeyError, TypeError, OSError) as exc:
                failures.append(f'{path.relative_to(BASE_DIRECTORY)}: {exc}')
    return reports, failures


def render_report(pdf, report):
    models, cases = report['models'], report['cases']
    if not models or not cases:
        raise ValueError('Report needs models and cases')
    for ci in range(0, len(cases), 4):
        for mi in range(0, len(models), 3):
            pdf.page()
            title = report['title'] + ' / ' + report['metric'].replace('_', ' ')
            pdf.text(24, 30, title[:100], 18)
            pdf.text(24, 48, report['subtitle'], 9)
            shown_cases = cases[ci:ci+4]
            width = 198
            for col, case in enumerate(shown_cases):
                x = 24 + col*width
                pdf.text(x, 69, case['id'].split('/')[-1].replace('_', ' '), 11, (0, .62, .58))
                lines = textwrap.wrap(case['prompt'], width=36)
                for li, line in enumerate(lines[:5]):
                    if li == 4 and len(lines) > 5:
                        line = line[:32] + '...'
                    pdf.text(x, 84+li*10, line, 8)
            for row_index, model in enumerate(models[mi:mi+3]):
                y = 150 + row_index*132
                pdf.text(24, y, model, 15)
                for col, case in enumerate(shown_cases):
                    x = 24+col*width
                    pdf.rect(x, y+9, width-8, 103, (.96, .97, .98))
                    cell = report['cells'].get((model, case['id']), dict(count=0, total=0, detail='No results', example='Missing or failed trials.'))
                    if cell['total']:
                        percent = 100*cell['count']/cell['total']
                        pdf.pie(x+33, y+43, percent)
                        pdf.text(x+12, y+82, f'{percent:g}%', 17, (0, .62, .58))
                    else:
                        pdf.text(x+12, y+50, 'No judgments', 9)
                    pdf.text(x+9, y+101, cell['detail'], 7)
                    pdf.text(x+68, y+26, 'Example / evidence', 8, (0, .62, .58))
                    lines = textwrap.wrap(cell['example'], width=23)
                    for li, line in enumerate(lines[:6]):
                        if li == 5 and len(lines) > 6:
                            line = line[:19] + '...'
                        pdf.text(x+68, y+39+li*9, line, 8)
            pdf.text(24, 573, report['footer'], 8)
            pdf.text(24, 585, f'Source: {report["source"]} | Page {len(pdf.pages)}', 7)


def main():
    reports, failures = discover_reports()
    if not reports:
        raise SystemExit('No supported findings found. ' + '; '.join(failures))
    destination = BASE_DIRECTORY / REPORT_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)
    combined = PDF()
    for index, report in enumerate(reports, 1):
        pdf = PDF()
        render_report(pdf, report)
        # Prefix keeps files unique even when run directories share names.
        path = destination / f'{index:02d}_{report["name"]}.pdf'
        pdf.save(path)
        render_report(combined, report)
        print(f'Saved {path}')
    combined.save(destination / 'all_findings.pdf')
    print(f'Saved {destination / "all_findings.pdf"} ({len(combined.pages)} pages)')
    if failures:
        raise SystemExit('Some sources could not be read:\n' + '\n'.join(failures))


if __name__ == '__main__':
    main()
