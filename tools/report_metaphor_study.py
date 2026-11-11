#!/usr/bin/env python3
"""Create offline SVG charts, CSV correlations, human-review sheets, and an HTML report."""
import argparse
from collections import defaultdict
import csv
import html
import json
import math
from pathlib import Path
import random
import re
from statistics import mean

BASE = Path(__file__).resolve().parent


def pearson(xs, ys):
    if len(xs) < 3:
        return None
    dx = [x-mean(xs) for x in xs]
    dy = [y-mean(ys) for y in ys]
    denominator = math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return sum(x*y for x, y in zip(dx, dy))/denominator if denominator else None


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0]*len(values)
    start = 0
    while start < len(order):
        end = start+1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for i in order[start:end]:
            result[i] = (start+end-1)/2+1
        start = end
    return result


def correlation(rows, x, y):
    xs, ys = [r[x] for r in rows], [r[y] for r in rows]
    return dict(n=len(rows), pearson=pearson(xs, ys), spearman=pearson(ranks(xs), ranks(ys)))


def write_csv(path, rows, fields):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def svg(title, body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="620" height="340" viewBox="0 0 620 340"><rect width="620" height="340" fill="white"/><g font-family="sans-serif" fill="#16324f"><text x="20" y="28" font-size="16">'+html.escape(title)+'</text>'+body+'</g></svg>'


def pie(title, yes, total):
    if not total:
        return svg(title, '<text x="30" y="120">No judged data yet</text>')
    fraction = yes/total
    body = '<circle cx="145" cy="175" r="95" fill="#e1e7ed"/>'
    if yes == total:
        body += '<circle cx="145" cy="175" r="95" fill="#009e91"/>'
    elif yes:
        angle = 2*math.pi*fraction-math.pi/2
        x, y = 145+95*math.cos(angle), 175+95*math.sin(angle)
        body += f'<path d="M145 175 L145 80 A95 95 0 {int(fraction>.5)} 1 {x} {y} Z" fill="#009e91"/>'
    body += f'<text x="270" y="150">Present / success: {yes}/{total} ({100*fraction:.1f}%)</text><text x="270" y="180">Absent / unsuccessful: {total-yes}/{total}</text>'
    return svg(title, body)


def scatter(rows, x, y, title):
    if not rows:
        return svg(title, '<text x="30" y="120">No judged data yet</text>')
    xmin, xmax = min(r[x] for r in rows), max(r[x] for r in rows)
    ymin, ymax = min(r[y] for r in rows), max(r[y] for r in rows)
    body = '<path d="M65 50 V280 H590" stroke="#16324f" fill="none"/>'
    for r in rows:
        px = 65+510*(r[x]-xmin)/(xmax-xmin or 1)
        py = 280-210*(r[y]-ymin)/(ymax-ymin or 1)
        body += f'<circle cx="{px}" cy="{py}" r="4" opacity=".45" fill="#009e91"><title>{r[x]}, {r[y]}</title></circle>'
    body += f'<text x="65" y="305">{html.escape(x)}: {xmin:g} to {xmax:g}</text><text x="65" y="325">{html.escape(y)}: {ymin:g} to {ymax:g}; n={len(rows)}</text>'
    return svg(title, body)


def choice_label(answer):
    first = answer.strip().splitlines()[0].strip().strip('*').strip() if answer.strip() else ''
    match = re.fullmatch(r'([AB])[.)]?', first)
    return match.group(1) if match else None


def report(experiment, run, output):
    cfg = json.loads(experiment.read_text())
    if (run/'config.json').exists():
        cfg = json.loads((run/'config.json').read_text())
    cases = {c['id']: c for c in cfg['cases']}
    records = {}
    if (run/'records.jsonl').exists():
        for line in (run/'records.jsonl').read_text().splitlines():
            r = json.loads(line)
            records[r['key']] = r
    output.mkdir(parents=True, exist_ok=True)
    rows, review = [], []
    for r in records.values():
        c = cases.get(r['case_id'])
        if c is None or r['model'] not in cfg['models']:
            continue
        review.append(dict(key=r['key'], prompt=r['prompt'], response=r['response'],
                           human_comparisons='', human_supported_links='', human_false_implications='',
                           human_adaptation_success='', human_limitation_success='', notes=''))
        j = r.get('judgment')
        if j is None:
            continue
        words = len(r['response'].split())
        comparisons = j['comparisons']
        rows.append(dict(key=r['key'], model=r['model'], resolved_model=r['resolved_model'],
            system=c['system'], condition=c['condition'], trial=r['trial'],
            relevance=c.get('relevance', ''), answer_length=c.get('answer_length','fixed'), variant=c.get('variant',''),
            input_words=len(r['prompt'].split()), output_words=words,
            choice_correct=(choice_label(r['response']) == c['expected_choice']) if c.get('expected_choice') and choice_label(r['response']) else None,
            input_tokens=r.get('usage',{}).get('input_tokens'), comparisons=len(comparisons),
            meaningful_mapping=any(len(x['supported_links']) >= 2 and not x['false_implications'] for x in comparisons),
            comparisons_per_100_words=100*len(comparisons)/words if words else 0,
            supported_links=sum(len(x['supported_links']) for x in comparisons),
            false_implications=sum(len(x['false_implications']) for x in comparisons),
            adaptation_success=j['adaptation_success'], limitation_success=j['limitation_success'],
            length_compliant=c.get('requested_min_words',100) <= words <= c.get('requested_max_words',120) if c.get('answer_length','fixed') == 'fixed' else None))
    fields=['key','model','resolved_model','system','condition','trial','relevance','answer_length','variant','input_words','input_tokens','output_words','comparisons','comparisons_per_100_words','meaningful_mapping','supported_links','false_implications','adaptation_success','limitation_success','length_compliant','choice_correct']
    write_csv(output/'metrics.csv', rows, fields)
    random.Random(42).shuffle(review)
    review_path = output/'human_review.csv'
    # Human edits are never overwritten by report regeneration.
    if not review_path.exists():
        write_csv(review_path, review, ['key','prompt','response','human_comparisons','human_supported_links','human_false_implications','human_adaptation_success','human_limitation_success','notes'])
    else:
        write_csv(output/'human_review_fresh.csv', review, ['key','prompt','response','human_comparisons','human_supported_links','human_false_implications','human_adaptation_success','human_limitation_success','notes'])
    groups = defaultdict(list)
    for r in rows:
        groups[(r['model'],r['condition'])].append(r)
    planned_groups = sorted({(m,c['condition']) for m in cfg['models'] for c in cfg['cases']})
    charts, summary = [], []
    for index, (model, condition) in enumerate(planned_groups):
        group = groups[(model, condition)]
        metric = 'choice_correct' if condition=='mapping_choice' else 'adaptation_success' if condition=='adapt' else 'limitation_success' if condition=='limits' else 'comparisons'
        yes = sum(bool(r[metric]) for r in group)
        expected = sum(c['condition']==condition for c in cfg['cases'])*cfg['trials']
        title=f'{model} | {condition} | {metric}'
        name=f'pie_{index:03}.svg'
        (output/name).write_text(pie(title,yes,len(group)))
        charts.append(f'<figure><img src="{name}" alt="{html.escape(title)}"><figcaption>{len(group)}/{expected} planned judgments. Systems pooled; inspect metrics.csv.</figcaption></figure>')
        summary.append(dict(model=model,condition=condition,metric=metric,positive=yes,judged=len(group),planned=expected,percentage=100*yes/len(group) if group else None))
    # Operational quality indicator, distinct from mere figurative presence.
    for index, (model, condition) in enumerate(planned_groups):
        if condition in ('adapt', 'limits', 'mapping_choice'):
            continue
        group = groups[(model, condition)]
        yes = sum(r['meaningful_mapping'] for r in group)
        name = f'mapping_{index:03}.svg'
        title = f'{model} | {condition} | meaningful mapping'
        (output/name).write_text(pie(title, yes, len(group)))
        charts.append(f'<figure><img src="{name}" alt="{html.escape(title)}"><figcaption>At least one comparison with two supported links and no annotated false implications. Operational threshold; requires human review.</figcaption></figure>')
    correlations=[]
    # Within-condition correlations avoid pooling fundamentally different prompt purposes.
    for x,y,keys in [('output_words','comparisons',['model','system','condition']),
                     ('output_words','supported_links',['model','system','condition']),
                     ('input_words','output_words',['model','system','relevance','answer_length','variant']),
                     ('input_words','comparisons_per_100_words',['model','system','relevance','answer_length','variant'])]:
        strata=defaultdict(list)
        for r in rows:
            if x=='input_words' and not r['relevance']:
                continue  # Creation/adaptation includes earlier generated text: not a randomized length manipulation.
            strata[tuple(r[k] for k in keys)].append(r)
        for values, group in sorted(strata.items()):
            stats=correlation(group,x,y)
            correlations.append(dict(stratum=json.dumps(dict(zip(keys,values))),x=x,y=y,**stats))
            if stats['pearson'] is not None:
                name=f'scatter_{len(correlations):04}.svg'
                (output/name).write_text(scatter(group,x,y,f'Exploratory r={stats["pearson"]:.3f}; n={len(group)}'))
                charts.append(f'<details><summary>{html.escape(str(values))}: {x} vs {y}</summary><img src="{name}" alt="Correlation scatter plot"></details>')
    write_csv(output/'correlations.csv', correlations,['stratum','x','y','n','pearson','spearman'])
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Metaphor study</title><style>body{font:16px sans-serif;max-width:1000px;margin:32px auto;color:#16324f}img{max-width:100%}figure{margin:24px 0}figcaption{font-size:14px}</style><h1>Metaphor study</h1><p>'+f'{len(rows)} judged answers; {len(records)} saved response records.'+'</p><p>Automated judgments, pending human validation. Gray means absent or unsuccessful; missing judgments are excluded. Correlations are exploratory associations, not causal mechanisms; repeated trials share prompts. Null correlations mean insufficient data or no variation. No significance or population claims.</p><p><a href="metrics.csv">Metrics</a> · <a href="correlations.csv">Correlations</a> · <a href="human_review.csv">Blind human review sheet</a></p>'+''.join(charts))
    return rows, correlations


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',default='experiments/metaphor_creation.json')
    p.add_argument('--run')
    p.add_argument('--output')
    a=p.parse_args()
    stem=Path(a.experiment).stem
    out=BASE/(a.output or 'reports/'+stem)
    rows, correlations=report(BASE/a.experiment,BASE/(a.run or 'runs/'+stem),out)
    print(f'{out}/index.html: {len(rows)} judged answers, {len(correlations)} correlation rows')


if __name__=='__main__':
    main()
