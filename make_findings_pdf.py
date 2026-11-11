#!/usr/bin/env python3
"""Build the concise findings/proposal PDF from saved pilot summaries; no API calls."""
import csv
import json
from pathlib import Path
import textwrap
from json_to_data_report import PDF

BASE=Path(__file__).resolve().parent
NAVY=(.06,.16,.25)
TEAL=(0,.53,.49)
GRAY=(.34,.40,.46)


def main():
    findings=json.loads((BASE/'reports/metaphor_findings/findings.json').read_text())
    studies=findings['studies']
    contrasts=list(csv.DictReader((BASE/'reports/metaphor_findings/contrasts.csv').open()))
    def context(instruction, side):
        return float(next(r for r in contrasts if r['stratum']=='ALL/'+instruction and r['metric']=='output_words')[side+'_value'])
    pdf=PDF()
    def page(title, subtitle, number):
        pdf.page()
        pdf.rect(0,0,842,8,TEAL)
        pdf.text(36,44,title,25,NAVY)
        pdf.text(36,65,subtitle,10,GRAY)
        pdf.rect(36,553,770,1,(.85,.89,.91))
        pdf.text(36,574,'Metaphor pilot | Findings and proposed study | 11 November 2026',9,GRAY)
        pdf.text(776,574,str(number),9,GRAY)
    def paragraph(text,y,width=116,x=36,size=11,leading=17):
        for line in textwrap.wrap(text,width=width):
            pdf.text(x,y,line,size,NAVY)
            y+=leading
        return y+8
    def heading(text,y):
        pdf.text(36,y,text,15,TEAL)
        return y+24

    page('Do LLMs create meaningful metaphors?', 'Pilot findings and a proposed test of grounded, relationship-sensitive construction',1)
    y=paragraph('The pilot supports flexible construction and relationship-sensitive selection in these tasks. It does not establish the internal mechanism, consciousness, or that a comparison was absent from training.',98)
    pdf.rect(36,149,770,52,(.94,.97,.97))
    pdf.text(52,171,'219 generated answers',16,TEAL)
    pdf.text(52,190,'171 open-ended answers with automated judgments + 48 directly scored A/B choices',11,NAVY)
    pdf.text(36,229,'What triggers a comparison?  GPT-4o, six answers per condition',15,TEAL)
    triggers=studies['triggers_pilot']['conditions']
    for i,(key,label) in enumerate([('beginner','Beginner explanation'),('summary','Rule summary'),('advice','Practical advice'),('explicit','Explicit request')]):
        group=triggers[key];count=group['comparison_presence'];n=group['n'];x=112+198*i
        pdf.pie(x,280,100*count/n)
        pdf.text(x-65,325,label,11,NAVY)
        pdf.text(x-30,345,f'{count}/{n} replies',12,TEAL)
    pdf.text(36,372,'Teal = comparison present; gray = absent. Automated labels; small exploratory sample.',9,GRAY)
    y=heading('More input did not consistently mean more output',408)
    for instruction,label,yy in [('fixed','Requested 100-120 words',442),('free','No answer-length instruction',482)]:
        short=context(instruction,'right');long=context(instruction,'left')
        pdf.text(36,yy,label,11,NAVY)
        pdf.text(278,yy,f'Short background: {short:.2f} words',11,NAVY)
        pdf.text(550,yy,f'Long background: {long:.2f} words',11,TEAL)
    pdf.text(36,520,'Each mean uses 24 answers; approximate background lengths: 100 versus 1,000 words.',9,GRAY)

    page('What the evidence establishes', 'Generation, revision, relational choice, and the limits of automated evaluation',2)
    y=heading('Construction and revision',101)
    y=paragraph('GPT-4o produced comparisons in 6/6 explicit-generation answers. Its 6/6 baseline revisions and 6/6 constrained-source revisions were judged to follow the requested rule change. GPT-5 provided a separate nine-answer smoke test, including 3/3 successful revisions. These unequal samples do not support a model ranking.',y)
    y=heading('Relationship-sensitive selection: 48/48 correct',y+6)
    y=paragraph('The final A/B probe reversed the target relation and option order and used neutral or misleading system names. GPT-4o selected the relation-matching option in 24/24 neutral-name and 24/24 misleading-name answers. Accuracy is scored directly from the choices, without an LLM judge. This was a simple, explicitly guided selection task, not spontaneous generation.',y)
    y=heading('The crucial qualification: inventing a matching source',y+6)
    y=paragraph('Some metaphors reproduce target rules by inventing magical copying or precisely tuned source behavior. One answer retained fruit that "magically splits into two identical fruits" despite a no-magic instruction. Editing such a world coherently differs from deriving a useful mapping from an ordinary source process.',y)
    y=heading('Evaluation limits',y+6)
    y=paragraph('The assistant audit of 30 answers found over-crediting of self-critiques and confusion between acknowledged analogy limits and false claims. Some critiques assumed facts absent from the rules. Quality and limitation-success percentages are not validated estimates. There was no independent human annotation; judge instructions and output formats changed during this adaptive pilot.',y)
    paragraph('Context correlations generally contain only four observations per stratum and have mixed signs. They are descriptive, not evidence of an internal causal mechanism. The pilot has only three invented systems; source novelty and generalization remain unresolved.',y, size=10,leading=15)

    def compact_heading(text,y):
        pdf.text(36,y,text,14,TEAL)
        return y+21
    def compact_paragraph(text,y):
        return paragraph(text,y,width=126,size=10.5,leading=15)

    page('Proposed idea: test grounded construction', 'A new, frozen experiment; proposed only - no additional API calls have been run',3)
    y=compact_heading('Research question and hypothesis',99)
    y=compact_paragraph('Can a model preserve useful relationships in a familiar source domain, selectively revise a comparison when a target rule changes, and retain the mapping when the rules stay the same? The hypothesis is that genuine flexibility appears as selective relational change, not merely fluent rewording.',y)
    y=compact_heading('Matched design',y+4)
    y=compact_paragraph('Use 12 independently designed systems, one dated model version, and two trials. Generate each comparison under two source conditions: unrestricted imagery versus an ordinary familiar process with acknowledged limitations. For each initial answer, independently present three followups: a relevant rule change, no rule change, or an irrelevant background change.',y)
    pdf.rect(36,y-2,770,43,(.94,.97,.97))
    pdf.text(48,y+15,'48 initial answers + 144 matched followups = 192 proposed generated answers',12,TEAL)
    y+=61
    y=compact_heading('Separate the outcomes',y)
    y=compact_paragraph('Two independent human readers should score target-rule fidelity, plausible source behavior, unsupported implications, and selective revision. Acknowledge a mapping gap without counting it as an asserted falsehood. Blind readers to model and condition where possible; report agreement and adjudicate disagreements before treating labels as gold data.',y)
    y=compact_heading('Analysis and trigger replication',y+4)
    y=compact_paragraph('Freeze prompts, rubric, primary contrasts, and stopping rules before collection. Compare relevant changes with both controls within systems. Estimate uncertainty over systems, not repeated answers. Replicate on a second model only after calibration. A separate optional trigger study can repeat beginner, summary, and advice prompts at a fixed requested length.',y)
    y=compact_heading('What a positive result would mean',y+4)
    compact_paragraph('A defensible claim is: "The model constructed and selectively revised grounded cross-domain mappings in unfamiliar scenarios." This still cannot distinguish all possible parameter-level explanations or establish conscious meaning. Learned parameters and semantic generalization are compatible, not competing alternatives.',y)

    page('Methods and audit trail', 'Local data sources, model versions, interpretation, and reproducibility',4)
    y=heading('Collected studies',100)
    for name,label in [('creation_smoke','GPT-5 creation smoke'),('creation_pilot','GPT-4o creation and revision'),('triggers_pilot','GPT-4o trigger pilot'),('context_pilot','GPT-4o context pilot'),('grounded_followup_pilot','GPT-4o familiar-source followup'),('relational_choice_pilot','GPT-4o relational-choice probe')]:
        s=studies[name]
        pdf.text(36,y,label,11,NAVY)
        pdf.text(470,y,f'{s["saved_answers"]} generated answers',11,TEAL)
        y+=24
    y=paragraph('Resolved generator versions: gpt-5-2025-08-07 and gpt-4o-2024-08-06. Automated judge: gpt-4.1. Original target systems cover stored-time loss, permission copying and expiry, and group approval. The selection probe also varies growth/loss, all/any approval, and single/reusable permission relationships.',y+6)
    y=heading('Read the evidence',y+4)
    for text in ['data/metaphor_pilot.json - full deduplicated answers, accepted judgments, and returned judge attempts',
                 'hypothesis.json - predictions, followup registration, outcomes, and collection decisions',
                 'analyst_audit.json - assistant review tied to answer keys; not independent human validation',
                 'reports/metaphor_findings/index.html - charts, matched contrasts, and per-study reports',
                 'reports/metaphor_context_pilot/correlations.csv - exploratory Pearson and Spearman coefficients']:
        y=paragraph(text,y,width=120,size=10,leading=14)
    paragraph('All 48 A/B choices have deterministic scores. Forty-two optional metaphor judgments for those choices were accepted; six failed validation and are unnecessary for choice accuracy. Tracked usage: 570,709 tokens across 219 generation responses and 375 returned judge attempts. Collection is stopped; the proposed 192-answer study has not been run.',y+5,size=10,leading=15)
    output=BASE/'reports/metaphor_findings_and_proposal.pdf'
    output.parent.mkdir(exist_ok=True)
    pdf.save(output)
    print(output)


if __name__=='__main__':
    main()
