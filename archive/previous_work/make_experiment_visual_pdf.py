#!/usr/bin/env python3
"""Show each invented term, its supplied context, actual answers, and judge pie charts."""
import json
import math
from pathlib import Path
import shutil
import textwrap
from json_to_data_report import PDF

BASE=Path(__file__).resolve().parent
NAVY=(.06,.16,.25);TEAL=(0,.53,.49);BLUE=(.25,.47,.72);GRAY=(.36,.42,.48);LIGHT=(.94,.97,.97)


def main():
    data=json.loads((BASE/'data/metaphor_pilot.json').read_text())
    study=next(s for s in data['studies'] if s['study']=='creation_pilot')
    cases={c['id']:c for c in study['config']['cases']}
    records=study['records'];pdf=PDF()
    def text(text,x,y,width=65,size=11,leading=16):
        for line in textwrap.wrap(text,width=width):
            pdf.text(x,y,line,size,NAVY);y+=leading
        return y
    def header(title,subtitle,number):
        pdf.page();pdf.rect(0,0,842,8,TEAL)
        pdf.text(36,43,title,25,NAVY);pdf.text(36,65,subtitle,10,GRAY)
        pdf.rect(36,550,770,1,(.85,.89,.91))
        pdf.text(36,574,'Metaphor pilot | GPT-4o | Automated judge: GPT-4.1 | 11 November 2026',9,GRAY)
        pdf.text(780,574,str(number),9,GRAY)
    def multi_pie(x,y,labels):
        # Each item is an observed response, so equal wedges are appropriate here.
        colors=[TEAL,BLUE];start=-math.pi/2
        for i,label in enumerate(labels):
            stop=start+2*math.pi/len(labels)
            pts=[(x,595-y)]+[(x+36*math.cos(start+(stop-start)*k/60),595-y-36*math.sin(start+(stop-start)*k/60)) for k in range(61)]
            col=colors[i%2]
            pdf.commands.append(f'{col[0]} {col[1]} {col[2]} rg '+f'{pts[0][0]} {pts[0][1]} m '+' '.join(f'{a} {b} l' for a,b in pts[1:])+' h f')
            start=stop
    excerpts={
        'nava':[
            'Imagine a magical water reservoir where unused water represents saved time. Each day, one-tenth of the water mysteriously evaporates, simulating the natural decay of unused minutes. When someone wishes to give water to another, the transfer process causes half of it to spill, illustrating the inefficiency and loss inherent in moving stored time.',
            'Imagine time as sand in an hourglass, and a nava as a special container beside it. Unused sand from the hourglass falls into the nava, but each day, the sand sifts through a fine sieve, losing a tenth of its grains. When you share sand with others, the container has a leak, so only half of what you pour in reaches its destination.'
        ],
        'selo':[
            'Imagine a magical fruit tree where each fruit grants the ability to perform a specific task. Once picked, the fruit can only be consumed once. If you share your fruit with someone, it magically duplicates, but both fruits ripen a day faster, giving less time before they spoil.',
            'Imagine a magical tree, where each leaf grants a specific task permission. Plucking a leaf allows you to perform its task, but the leaf wilts immediately after use. If you decide to share a leaf with someone, the tree magically duplicates it, but both leaves fall off the tree a day sooner.'
        ],
        'vemi':[
            'Imagine a "Harmony Bell" system, where a bell hangs above a village representing unity. Every group in the village has a special melody they wish to play, and the bell rings only when each member\'s instrument is perfectly in tune. If a new musician joins, all instruments must be retuned.',
            'Imagine a chorus needing unanimous harmony to perform. Each singer represents a group member, and their collective approval signifies a successfully rehearsed melody. When a new singer joins, the entire chorus must rehearse anew to ensure every voice is in perfect synchrony before performing.'
        ]}
    names={'nava':['Water reservoir','Sand / hourglass'],'selo':['Fruit tree','Tree / leaves'],'vemi':['Harmony Bell','Chorus']}
    caveats={'nava':'The rates are stipulated in the imagery; this does not show that real reservoirs or hourglasses behave that way.',
             'selo':'Both answers use tree imagery and magical copying. Rule matching is distinct from real-world plausibility.',
             'vemi':'Both answers use musical coordination. Their related imagery does not demonstrate diverse source domains.'}
    for number,term in enumerate(['nava','selo','vemi'],1):
        initial=sorted([r for r in records if r['case_id']==term+'/generate'],key=lambda r:r['trial'])
        revised=[r for r in records if r['case_id']==term+'/adapt']
        case=cases[term+'/generate'];change=cases[term+'/adapt']['changed_rule']
        header('We invented a term: '+term.upper(),'Supplied context -> model answers -> judge results | Two initial answers and two revisions',number)
        pdf.rect(36,83,770,87,LIGHT);pdf.text(48,102,'CONTEXT GIVEN TO THE MODEL',11,TEAL)
        for i,rule in enumerate(case['reference_rules']):pdf.text(48,123+18*i,rule,11,NAVY)
        pdf.text(36,192,'Request: "Create one metaphor to explain this system, and explain the relationships it captures."',11,NAVY)
        pdf.text(36,209,'Requested answer length: 100-120 words. Below: verbatim excerpts from trial 1 and trial 2.',9,GRAY)
        for i,r in enumerate(initial):
            excerpt=excerpts[term][i];assert excerpt in r['response'],(term,i)
            x=36+396*i;pdf.text(x,236,'ANSWER '+str(r['trial'])+'  |  '+names[term][i],12,TEAL)
            text('"'+excerpt+'"',x,256,width=60,size=10,leading=14)
        y=382
        pdf.text(36,y,'PIE CHARTS OF THE OBSERVED ANSWERS',12,TEAL)
        centers=[155,420,685]
        multi_pie(centers[0],432,names[term])
        pdf.text(42,490,'Which comparisons appeared?',11,NAVY)
        for i,label in enumerate(names[term]):
            pdf.rect(45+123*i,501,7,7,[TEAL,BLUE][i]);pdf.text(56+123*i,508,label+' 1/2',8,NAVY)
        passed=sum(any(len(c['supported_links'])>=2 and not c['false_implications'] for c in r['judgment']['comparisons']) for r in initial)
        adapted=sum(r['judgment']['adaptation_success'] is True for r in revised)
        for x,label,count,n in [(centers[1],'Initial rule mapping',passed,len(initial)),(centers[2],'Revised rule followed',adapted,len(revised))]:
            # Scale the existing vector pie to align with the answer-distribution pie.
            pdf.commands.append(f'q 1.565 0 0 1.565 {-0.565*x} {-0.565*(595-432)} cm')
            pdf.pie(x,432,100*count/n);pdf.commands.append('Q')
            pdf.text(x-57,490,label,11,NAVY);pdf.text(x-43,510,f'{count}/{n} judged pass ({100*count/n:.0f}%)',10,TEAL)
        pdf.text(36,533,'Small n=2 per test. Accuracy = automated rubric pass, not independent human verification.',9,GRAY)
        # Save term-specific change/context for the final methods page, keeping charts directly below answers.
    header('What changed - and what we propose next','The pies report rule matching; they do not establish conscious understanding or training novelty.',4)
    pdf.text(36,100,'The revision test changed one rule',15,TEAL)
    y=124
    for term in ['nava','selo','vemi']:
        pdf.text(36,y,term.upper(),11,TEAL)
        y=text(cases[term+'/adapt']['changed_rule'],110,y,width=103,size=10,leading=15)+14
    pdf.text(36,263,'Why the 100% pies need qualification',15,TEAL)
    y=286
    for term in ['nava','selo','vemi']:
        y=text(term.upper()+': '+caveats[term],36,y,width=126,size=10,leading=15)+7
    pdf.text(36,371,'Proposed next experiment - not collected',15,TEAL)
    pdf.rect(36,389,232,52,LIGHT);pdf.rect(305,389,232,52,LIGHT);pdf.rect(574,389,232,52,LIGHT)
    text('12 systems x 2 trials x 2 source conditions',48,410,width=31,size=11,leading=16)
    text('48 initial comparisons; each gets 3 independent followups',317,410,width=32,size=11,leading=16)
    text('192 total answers; two independent human readers',586,410,width=32,size=11,leading=16)
    pdf.text(278,420,'>',18,TEAL);pdf.text(547,420,'>',18,TEAL)
    y=text('Followups: a relevant rule change, no rule change, or an irrelevant background change. Compare selective revision while scoring target fidelity and source plausibility separately.',36,468,width=124,size=11,leading=16)
    text('Data: data/metaphor_pilot.json (creation_pilot). Judge concerns: analyst_audit.json. These six initial answers are a subset of the full 219-answer pilot; no new API collection was performed.',36,522,width=133,size=9,leading=13)
    target=BASE/'reports/metaphor_findings_and_proposal.pdf'
    original=BASE/'reports/metaphor_findings_and_proposal_overview.pdf'
    if target.exists() and not original.exists():shutil.copy2(target,original)
    pdf.save(target);print(target)


if __name__=='__main__':main()
