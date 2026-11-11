# Metaphor pilot findings

**The models constructed and revised comparisons, and GPT-4o selected comparisons according to stated relationships. This supports flexible metaphor-related behavior in these tasks. It does not establish how that behavior is implemented internally.**

Collected 219 answers: nine GPT-5 smoke answers and 210 GPT-4o pilot answers. Resolved models were `gpt-5-2025-08-07` and `gpt-4o-2024-08-06`. The 171 open-ended answers have accepted automated judgments; all 48 final comparison choices are scored directly from their A/B responses. No model ranking is warranted.

| Question | Observed result | Interpretation |
|---|---|---|
| Can it construct a comparison? | GPT-4o: 6/6 explicitly requested generations contained comparisons | Ability under explicit instruction; some source worlds are invented to match the rules |
| Can it revise one? | GPT-4o: 6/6 baseline revisions and 6/6 constrained-source revisions judged successful; GPT-5 smoke: 3/3 | Tracks an explicitly supplied rule change; no unchanged-rule control was collected |
| What triggers spontaneous comparisons? | GPT-4o beginner explanations: 5/6; summaries: 1/6; advice: 0/6; explicit requests: 6/6 | Purpose mattered in this small three-system pilot |
| Does more input mean more output? | Fixed-length answers: short and long background both averaged **103.75 words**; unrestricted: **235.21 → 203.38 words** | The universal “more input = more output regardless of instructions” claim fails on these observations |
| Do choices follow relationships despite misleading names? | **48/48 correct**, including 24/24 misleading-name trials and reversed option order | Relationship-sensitive discrimination on an explicitly guided, simple test; not spontaneous creation |

The short/long context means each use 24 answers per output-instruction condition, balanced over three systems, two background topics, and two wording variants. Short and long background contained approximately 100 and 1,000 words. Background relevance was topical/administrative rather than additional explanatory information. Length and added content are not completely separable. Word counts split on whitespace, including Markdown tokens.

**The main qualification is source grounding.** The model sometimes invents magical copying or precisely tuned physical behavior to reproduce a target rule. Even when explicitly forbidden, one constrained generation says fruit “magically splits into two identical fruits.” A successful revision can therefore reflect coherent editing of an invented world, rather than inference from an ordinary source process. Other answers acknowledge useful limits or switch to a better-fitting source—for example, moving from melting ice to interest-bearing savings when storage changes from loss to growth.

**The judge needs human validation.** An assistant audit of 30 baseline/followup answers found over-crediting of self-critiques, confusion between an acknowledged limitation and a false implication, and a `['None']` placeholder counted as a false implication. Some critiques also assumed facts absent from the rules, such as end-of-day loss. Do not use the reported “meaningful mapping” or limitation-success percentages as validated quality estimates. The audit is not independent human annotation. Judge formatting, evidence instructions, and conditional schemas changed during the pilot; this is adaptive exploration, not a frozen confirmatory study.

Correlations and scatter plots are saved within each study. Context input-length correlations generally have only four observations per stratum; their signs vary. They are descriptive checks, not evidence of a causal internal mechanism. Raw evidence, matched contrasts, and model-specific counts are more informative here.

See [hypothesis.json](hypothesis.json) for outcomes and decisions, [analyst_audit.json](analyst_audit.json) for concerns tied to answer keys, and [the report index](reports/metaphor_findings/index.html) for pie charts, scatter plots, correlations, and data. Tracked usage totals **570,709 tokens across 219 saved generation responses and 375 returned judge attempts**; this is not a dollar bill and excludes any unsuccessful requests without returned usage. Collection is stopped. The next substantive step is independent annotation and a new, frozen replication with more systems and an unchanged-rule control.
