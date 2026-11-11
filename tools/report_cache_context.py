#!/usr/bin/env python3
"""Export inspectable cache-study answers and model/policy-specific charts. No API calls."""
from collections import defaultdict
import csv
import html
import json
from pathlib import Path
from statistics import mean
import textwrap
from json_to_data_report import PDF
from report_metaphor_study import pie

BASE=Path(__file__).resolve().parent


def main():
    run=BASE/'runs/lru_lrm_context_comparison'
    cfg=json.loads((run/'config.json').read_text())
    cases={c['id']:c for c in cfg['cases']}
    saved={}
    path=run/'records.jsonl'
    if path.exists():
        for line in path.read_text().splitlines():
            row=json.loads(line);saved[row['key']]=row
    export=BASE/'data/lru_lrm_context_results.json'
    previous={}
    if export.exists():
        previous={r['key']:r for r in json.loads(export.read_text())['results']}
    results=[]
    for r in sorted(saved.values(),key=lambda r:(r['model'],r['case_id'],r['trial'])):
        c=cases[r['case_id']]
        old=previous.get(r['key'],{})
        results.append(dict(key=r['key'],model=r['model'],resolved_model=r['resolved_model'],case_id=r['case_id'],policy=c['policy'],audience=c['audience'],context_condition=c['context_condition'],trial=r['trial'],prompt=r['prompt'],response=r['response'],reference_rules=c['reference_rules'],judge_output=r.get('judgment'),judge_model=r.get('judge_model'),response_id=r['response_id'],timestamp=r['timestamp'],usage=r.get('usage'),manual_review=old.get('manual_review',dict(status='pending',overrides={},factual_accuracy=None,notes='')),assistant_factual_audit=old.get('assistant_factual_audit',None),assistant_judge_audit=old.get('assistant_judge_audit',None)))
    attempts=[]
    if (run/'judge_attempts.jsonl').exists():
        attempts=[json.loads(line) for line in (run/'judge_attempts.jsonl').read_text().splitlines()]
    tracked_usage={key:sum(r.get('usage',{}).get(key,0) for r in results)+sum(a.get('usage',{}).get(key,0) for a in attempts) for key in ['input_tokens','output_tokens','total_tokens']}
    collection=dict(planned_answers=len(cfg['models'])*len(cfg['cases'])*cfg['trials'],saved_answers=len(results),accepted_judgments=sum(r['judge_output'] is not None for r in results),returned_judge_attempts=len(attempts),tracked_usage=tracked_usage,resolved_models=sorted({r['resolved_model'] for r in results}),interpretation='No browsing. LRM training absence is unverified. Whole-answer factual accuracy has not been systematically scored.')
    artifact=dict(schema_version=1,collection_summary=collection,experiment=cfg,review_instructions='Inspect response beside judge_output. Preserve judge_output. Set manual_review.status to reviewed and overrides.explanatory_comparison to true/false to correct presence; rerun this report to apply those reviewed presence overrides. factual_accuracy and notes are manual annotations, not automatic scores. Assistant audit is not independent human review.',results=results,judge_attempts=attempts)
    export.parent.mkdir(exist_ok=True);export.write_text(json.dumps(artifact,indent=2,ensure_ascii=False)+'\n')
    output=BASE/'reports/lru_lrm_context_comparison';output.mkdir(parents=True,exist_ok=True)
    groups=defaultdict(list)
    for r in results:groups[(r['model'],r['policy'],r['context_condition'],r['audience'])].append(r)
    summary=[];html_charts=[];pdf=PDF()
    for model in cfg['models']:
        for policy in ['lru','lrm']:
            pdf.page();pdf.rect(0,0,842,8,(0,.53,.49))
            pdf.text(36,44,f'{model} | {policy.upper()} | Spontaneous comparisons',22)
            pdf.text(36,67,'No generation prompt requests metaphor. Teal = present; gray = absent. Unvalidated judge labels; inspect flagged cases before interpreting rates.',10)
            y=103
            pdf.text(36,y,'Supplied excerpt in the with-excerpt conditions:',12,(0,.53,.49));y+=21
            for line in textwrap.wrap(cfg['policy_specs'][policy]['excerpt'],width=119):
                pdf.text(36,y,line,10);y+=15
            pdf.text(36,205,'Without-excerpt conditions receive only the topic, audience, and requested 120-150 word length.',10)
            slots=[('with_excerpt','age_10'),('without_excerpt','age_10'),('with_excerpt','graduate'),('without_excerpt','graduate')]
            for i,(context,audience) in enumerate(slots):
                rows=groups[(model,policy,context,audience)]
                judged=[];overrides=0
                for r in rows:
                    manual=r['manual_review'];override=manual.get('overrides',{}).get('explanatory_comparison')
                    if manual.get('status')=='reviewed' and type(override) is bool:
                        judged.append(override);overrides+=1
                    elif r['judge_output'] is not None:
                        judged.append(bool(r['judge_output']['comparisons']))
                yes=sum(judged);n=len(judged)
                label=f'{context.replace("_"," ")} / {audience.replace("_"," ")}'
                summary.append(dict(model=model,policy=policy,context_condition=context,audience=audience,saved=len(rows),judged=n,comparison_present=yes,percentage=100*yes/n if n else None,planned=cfg['trials'],reviewed_presence_overrides=overrides,mean_output_words=mean(len(r['response'].split()) for r in rows) if rows else None,length_compliant=sum(120<=len(r['response'].split())<=150 for r in rows)))
                filename=f'{model}_{policy}_{context}_{audience}.svg'
                (output/filename).write_text(pie(f'{model} | {policy.upper()} | {label}',yes,n))
                html_charts.append(f'<figure><img src="{filename}" alt="{html.escape(label)}"><figcaption>{len(rows)}/{cfg["trials"]} answers saved; {n} scored; {overrides} manual overrides.</figcaption></figure>')
                x=230+390*(i%2);yy=270+150*(i//2)
                pdf.text(x-130,yy-23,label,12,(0,.53,.49))
                if n:
                    pdf.pie(x-85,yy+17,100*yes/n)
                    pdf.text(x-40,yy+18,f'{yes}/{n} ({100*yes/n:.0f}%)',18)
                else:pdf.text(x-100,yy+18,'No accepted judgments yet',11)
                pdf.text(x-128,yy+67,f'{len(rows)}/{cfg["trials"]} saved; n={n}; overrides={overrides}',10)
            pdf.text(36,531,'Unvalidated judge counts only; likely false positives are flagged in the review JSON. Not factual accuracy.',10)
            pdf.text(36,572,'Raw answers and judge output: tools/data/lru_lrm_context_results.json',9)
    pdf.save(output/'findings.pdf')
    pdf.save(BASE.parent/'findings.pdf')
    with (output/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'collection_summary.json').write_text(json.dumps(collection,indent=2)+'\n')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>LRU / LRM context study</title><style>body{font:16px sans-serif;max-width:1000px;margin:30px auto}img{max-width:100%}pre{white-space:pre-wrap;background:#eef5f5;padding:18px}summary{cursor:pointer;padding:10px}</style><h1>LRU / LRM context study</h1><p><strong>Audit warning: judge-cited evidence in several graduate answers is literal CS description or same-domain comparison. Pie charts show original, unvalidated judge counts, not established metaphor rates.</strong></p><p>Comparison presence is distinct from factual accuracy. LRM is a recent feature, not established absence from training. Missing judgments are excluded. Only reviewed presence overrides are automatically applied.</p><p><a href="findings.pdf">PDF charts</a> · <a href="summary.csv">Summary CSV</a> · <a href="../../data/lru_lrm_context_results.json">Editable review JSON</a></p>'+''.join(html_charts)+'<h2>Answers and judge outputs</h2>'+''.join('<details><summary>'+html.escape(f'{r["model"]} | {r["case_id"]} | trial {r["trial"]}')+'</summary><h3>Answer</h3><pre>'+html.escape(r['response'])+'</pre><h3>Judge output</h3><pre>'+html.escape(json.dumps(r['judge_output'],indent=2,ensure_ascii=False))+'</pre><h3>Assistant audit flags (not human review)</h3><pre>'+html.escape(json.dumps(dict(factual=r['assistant_factual_audit'],judge=r['assistant_judge_audit']),indent=2,ensure_ascii=False))+'</pre></details>' for r in results))
    print(f'{len(results)} saved answers; {sum(r["judge_output"] is not None for r in results)} accepted judgments. Export: {export}')


if __name__=='__main__':main()
