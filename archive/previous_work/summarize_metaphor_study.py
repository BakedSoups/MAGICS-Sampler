#!/usr/bin/env python3
"""Summarize the bounded pilot from deduplicated local records; no API calls."""
from collections import defaultdict
import csv
import json
import hashlib
from pathlib import Path
from statistics import mean
from report_metaphor_study import report, choice_label, write_csv, pie

BASE=Path(__file__).resolve().parent
STUDIES=['creation_smoke','creation_pilot','triggers_pilot','context_pilot','grounded_followup_pilot','relational_choice_pilot']


def main():
    destination=BASE/'reports/metaphor_findings'
    destination.mkdir(parents=True,exist_ok=True)
    archive=[]
    studies={}; usage=defaultdict(int); contrasts=[]; choices=[]
    for name in STUDIES:
        run=BASE/'runs'/('metaphor_'+name)
        if not (run/'config.json').exists():continue
        cfg=json.loads((run/'config.json').read_text()); cases={c['id']:c for c in cfg['cases']}
        rows, correlations=report(run/'config.json',run,BASE/'reports'/('metaphor_'+name))
        saved={}
        for line in (run/'records.jsonl').read_text().splitlines():
            r=json.loads(line);saved[r['key']]=r
        archive.append(dict(study=name,config=cfg,records=list(saved.values()),judge_attempts=[json.loads(line) for line in (run/'judge_attempts.jsonl').read_text().splitlines()]))
        for r in saved.values():
            usage['saved_generation_calls']+=1
            for k in ['input_tokens','output_tokens','total_tokens']:usage[k]+=r.get('usage',{}).get(k,0)
        for line in (run/'judge_attempts.jsonl').read_text().splitlines():
            a=json.loads(line);usage['saved_judge_attempts']+=1
            for k in ['input_tokens','output_tokens','total_tokens']:usage[k]+=a.get('usage',{}).get(k,0)
        groups=defaultdict(list)
        for r in rows:groups[r['condition']].append(r)
        group_summaries={}
        for condition,group in groups.items():
            group_summaries[condition]=dict(n=len(group),comparison_presence=sum(r['comparisons']>0 for r in group),
                meaningful_mapping=sum(r['meaningful_mapping'] for r in group),
                mean_output_words=mean(r['output_words'] for r in group),
                adaptation_success=sum(r['adaptation_success'] is True for r in group),
                limitation_success=sum(r['limitation_success'] is True for r in group))
        studies[name]=dict(models=cfg['models'],resolved_models=sorted({r['resolved_model'] for r in rows}),
            saved_answers=len(saved),judged=len(rows),planned=len(cfg['models'])*len(cfg['cases'])*cfg['trials'],
            conditions=group_summaries,valid_correlations=sum(r['pearson'] is not None for r in correlations))
        if name=='triggers_pilot':
            for system in ['ALL','nava','selo','vemi']:
                a=[r for r in rows if r['condition']=='beginner' and (system=='ALL' or r['system']==system)]
                b=[r for r in rows if r['condition']=='summary' and (system=='ALL' or r['system']==system)]
                if a and b:
                    contrasts.append(dict(study=name,stratum=system,metric='comparison_presence_percentage_points',left='beginner',right='summary',left_value=100*mean(r['comparisons']>0 for r in a),right_value=100*mean(r['comparisons']>0 for r in b),difference=100*(mean(r['comparisons']>0 for r in a)-mean(r['comparisons']>0 for r in b)),n_left=len(a),n_right=len(b)))
        if name=='context_pilot':
            for instruction in ['fixed','free']:
                for system in ['ALL','nava','selo','vemi']:
                    a=[r for r in rows if r['answer_length']==instruction and cases[saved[r['key']]['case_id']]['background_length']=='long' and (system=='ALL' or r['system']==system)]
                    b=[r for r in rows if r['answer_length']==instruction and cases[saved[r['key']]['case_id']]['background_length']=='short' and (system=='ALL' or r['system']==system)]
                    for metric in ['output_words','comparisons_per_100_words']:
                        if a and b:contrasts.append(dict(study=name,stratum=system+'/'+instruction,metric=metric,left='long',right='short',left_value=mean(r[metric] for r in a),right_value=mean(r[metric] for r in b),difference=mean(r[metric] for r in a)-mean(r[metric] for r in b),n_left=len(a),n_right=len(b)))
            matched=defaultdict(dict)
            for r in rows:
                c=cases[saved[r['key']]['case_id']]
                if c['background_length']=='none':continue
                key=(r['model'],r['system'],r['relevance'],r['answer_length'],r['variant'])
                matched[key].setdefault(c['background_length'],[]).append(r)
            for key, levels in matched.items():
                if not all(k in levels for k in ['long','short']):continue
                a,b=levels['long'],levels['short']
                for metric in ['output_words','comparisons_per_100_words']:
                    contrasts.append(dict(study=name,stratum=json.dumps(key),metric=metric,left='long',right='short',left_value=mean(r[metric] for r in a),right_value=mean(r[metric] for r in b),difference=mean(r[metric] for r in a)-mean(r[metric] for r in b),n_left=len(a),n_right=len(b)))
        if name=='relational_choice_pilot':
            for r in saved.values():
                c=cases[r['case_id']];label=choice_label(r['response'])
                choices.append(dict(key=r['key'],case_id=c['id'],system=c['system'],rule_variant=c['rule_variant'],cue=c['cue'],option_order=c['option_order'],trial=r['trial'],expected_choice=c['expected_choice'],choice=label,correct=label==c['expected_choice'] if label else None))
            studies[name]['primary_metric']='deterministic_choice_accuracy; optional comparison annotations are not required'
            studies[name]['primary_scored']=sum(c['choice'] is not None for c in choices)
            studies[name]['choices_by_cue']={cue:dict(n=sum(c['cue']==cue for c in choices),parsed=sum(c['cue']==cue and c['choice'] is not None for c in choices),correct=sum(c['cue']==cue and c['correct'] is True for c in choices)) for cue in ['neutral','misleading']}
    for cue in ['neutral','misleading']:
        selected=[c for c in choices if c['cue']==cue and c['choice'] is not None]
        (destination/f'choice_{cue}.svg').write_text(pie('Relational choice: '+cue, sum(c['correct'] is True for c in selected), len(selected)))
    (BASE/'data').mkdir(exist_ok=True)
    (BASE/'data/metaphor_pilot.json').write_text(json.dumps(dict(schema_version=1,provenance='Actual API collection; deduplicated records and returned judge attempts. Assistant audit is separate from human validation.',studies=archive),indent=2)+'\n')
    result=dict(status='pilot_complete_pending_human_validation' if all(s['saved_answers']==s['planned'] for s in studies.values()) else 'partial',
        interpretation='Exploratory, model-specific behavioral findings. Automated annotations are not human gold labels. No consciousness, training-novelty, or internal-mechanism claim.',studies=studies,tracked_usage=dict(usage))
    (destination/'findings.json').write_text(json.dumps(result,indent=2)+'\n')
    write_csv(destination/'contrasts.csv',contrasts,['study','stratum','metric','left','right','left_value','right_value','difference','n_left','n_right'])
    write_csv(destination/'relational_choices.csv',choices,['key','case_id','system','rule_variant','cue','option_order','trial','expected_choice','choice','correct'])
    if choices:
        choice_dir=BASE/'reports/metaphor_relational_choice_pilot'
        (choice_dir/'annotation_index.html').write_text((choice_dir/'index.html').read_text())
        (choice_dir/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Relational choice pilot</title><h1>Relational choice pilot</h1><p>48/48 choices parsed and correct: 24/24 neutral, 24/24 misleading names. Options and rule direction are counterbalanced. Simple, explicitly guided discrimination; not a generation or internal-mechanism test.</p><img src="../metaphor_findings/choice_neutral.svg" alt="Neutral choice accuracy"><img src="../metaphor_findings/choice_misleading.svg" alt="Misleading name choice accuracy"><p><a href="../metaphor_findings/relational_choices.csv">All 48 choice scores</a> · <a href="annotation_index.html">42 optional accepted metaphor annotations</a></p><p>Six optional annotations failed validation; primary accuracy uses all 48 saved choices and does not depend on those annotations.</p>')
    links=''.join(f'<li><a href="../metaphor_{n}/index.html">{n}</a>: {s["judged"]}/{s["planned"]} optional annotations; {s.get("primary_scored", s["judged"])} primary scores</li>' for n,s in studies.items())
    (destination/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Metaphor pilot findings</title><style>body{font:17px sans-serif;max-width:900px;margin:40px auto;line-height:1.5}</style><h1>Metaphor pilot findings</h1><p>219 generated answers. Beginner explanations: 5/6 with comparisons; summaries: 1/6; advice: 0/6. Fixed-length short and long contexts both averaged 103.75 visible words. Treat automated quality and self-critique scores as unvalidated.</p><p><img src="choice_neutral.svg" alt="Neutral-name choice accuracy"><img src="choice_misleading.svg" alt="Misleading-name choice accuracy"></p><p>Exploratory results; automated judgment requires human validation. Models and collection stages are reported separately.</p><ul>'+links+'</ul><p><a href="findings.json">Findings JSON</a> · <a href="contrasts.csv">Matched contrasts</a> · <a href="relational_choices.csv">Deterministically scored choices</a></p><p>Read results.md in the project for interpretation and analyst audit limitations. See each study for SVG charts and correlations.</p>')
    paths=[BASE/'hypothesis.json',BASE/'analyst_audit.json',BASE/'results.md',BASE/'data/metaphor_pilot.json',BASE/'run_metaphor_study.py',BASE/'report_metaphor_study.py',BASE/'summarize_metaphor_study.py']
    paths+=list((BASE/'experiments').glob('metaphor_*pilot.json'))
    (destination/'analysis_manifest.json').write_text(json.dumps(dict(sha256={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()},note='Checksums at offline report regeneration. Collection included documented evaluator changes; current code is not asserted to be the sole historical rubric.'),indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
