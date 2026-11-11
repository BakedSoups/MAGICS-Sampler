# Metaphor creation and triggers: experiment plan

## Concise rationale

We ask whether an LLM can construct a useful comparison for an unfamiliar combination of rules, revise that comparison when a rule changes, and identify where it misleads. Success is behavioral evidence of flexible metaphor construction. It does not prove consciousness, human-like understanding, an unseen training example, or a particular internal mechanism. Learned parameters and semantic generalization are compatible explanations; API answers cannot separate them directly.

We also ask when figurative comparisons appear without being requested: does explaining, summarizing, advising, or receiving more background change their frequency? Explicit metaphor requests provide a positive control. This separates ability to generate from spontaneous use.

## Existing evidence and coding correction

Historical audience experiments suggest topic and audience effects, but preserve only aggregate counts and excerpts. The eight surprise-party answers are a smoke test. Their judge inconsistently labels idioms and sometimes counts literal descriptions as analogies. Do not pool those labels with the new study.

Count a comparison only when it maps distinct domains. Count elaborations of one comparison once. Record conventional metaphorical expressions and idioms separately; their labels may overlap. Technical terms alone and literal category descriptions do not count as explicit comparisons. This is a study-specific comparison rubric, not MIPVU lexical annotation. A limitation response discussing an existing comparison is not spontaneous generation.

## Materials and hypotheses

Three invented systems combine storage and loss (nava), permission copying and expiration (selo), and unanimous approval (vemi). Their names and rule combinations are experimental constructions, not guarantees of absence from training. Rules and judge instructions are in JSON/Python for inspection before collection.

1. **Creation:** `experiments/metaphor_creation.json`: three systems × generate/adapt/limits = 9 cases. Adapt and limits receive the exact generation answer from the same model and trial. Adapt changes one rule while preserving the others. Hypothesis: successful mappings and appropriate revisions show sensitivity to relationships beyond repeating a fixed phrase. An inability to revise supports a limitation, not proof that all generation is memorization.
2. **Triggers:** `experiments/metaphor_triggers.json`: three systems × beginner explanation/summary/advice/explicit metaphor = 12 cases. All request 100–120 words. Hypothesis: purpose changes comparison presence; explicit requests should increase it. Beginner versus summary is the primary spontaneous-use contrast. Advice has no uniquely optimal strategy, so judge fidelity to rules rather than decision optimality.
3. **Context:** `experiments/metaphor_context.json`: three systems × 18 cases = 54 cases. Cross short/long background, relevant/unrelated subject matter, free/fixed answer length, and two passage variants; add two question-only baselines per system. Hypothesis: input length can affect visible answer length; compare metaphor counts and comparisons per 100 words to distinguish more text from greater figurative frequency. The relevant passages provide on-topic administrative detail, not additional explanatory rules. This tests topical background and added quantity, not the benefits of all useful context. Long passages also contain more examples; length cannot be separated from every content property. Short/long are approximately 100/1,000 background words, with actual prompt word counts and API input tokens saved.
4. **Calibration:** `experiments/metaphor_calibration.json` contains hand-specified positive/borderline examples for reviewing the rubric. It is a review resource, not a generation run. Inspect at least 20 initial answers and all judge/human disagreements before expanding. Revise the rubric before the confirmatory collection; keep pilot and final runs separate.

## Execution and cost scope

The new scripts preserve the original runner and reporting workflow. No paid calls are required for setup, dry runs, or reports. Models default to the existing project's `gpt-5` generator and `gpt-4.1` judge; account access has not been checked. Edit each experiment JSON to choose models. Record resolved model IDs and collection dates; aliases may change. Use dated model IDs when accessible. Do not interpret repeated trials as independent topics or model populations.

Pilot at five trials per case and one model: creation 45 answers, triggers 60, context 270; **375 generation calls plus 375 accepted judgments** across all sets. Run creation first, then triggers; run context after checking rubric quality. A one-trial smoke run of all sets is 75 answers. A larger study should expand independent systems/topics before simply multiplying repetitions. Add familiar topics in a separately labeled replication to assess generalization; this first pilot concerns invented systems.

Judging allows up to three attempts, with token usage saved per attempt. SDK transport retries and interrupted calls can add costs. Generation responses are saved before judging; reruns resume and reuse saved answers. A crash before saving a response can repeat a billed call. Use one process per output directory. Settings changes require a new folder. Jobs are shuffled with a recorded seed; dependent tasks run after their parent. Failures stop collection and leave completed work saved.

```bash
# Offline preview; no key required.
.venv/bin/python run_metaphor_study.py
.venv/bin/python run_metaphor_study.py --experiment experiments/metaphor_triggers.json
.venv/bin/python run_metaphor_study.py --experiment experiments/metaphor_context.json

# Billed, one-trial creation smoke test; reads OPENAI_API_KEY from environment.
.venv/bin/python run_metaphor_study.py --live --trials 1 --output runs/metaphor_creation_smoke
.venv/bin/python report_metaphor_study.py --run runs/metaphor_creation_smoke --output reports/metaphor_creation_smoke

# Billed pilot after calibration. Use a fresh folder if settings differ.
.venv/bin/python run_metaphor_study.py --live
.venv/bin/python run_metaphor_study.py --experiment experiments/metaphor_triggers.json --live
.venv/bin/python run_metaphor_study.py --experiment experiments/metaphor_context.json --live

# Offline reports; change --experiment to report each set.
.venv/bin/python report_metaphor_study.py
.venv/bin/python report_metaphor_study.py --experiment experiments/metaphor_triggers.json
.venv/bin/python report_metaphor_study.py --experiment experiments/metaphor_context.json
```

API usage follows [official OpenAI documentation](https://developers.openai.com/api/reference/python/resources/responses/methods/create). The API token cap includes reasoning where applicable; measure visible output words separately. Do not use the cap as an exact answer-length control. Do not ask the model to explain its internal process as evidence of mechanism.

## Measurements and charts

Save prompts, full answers, dependency answers, trial/model/response IDs, timestamps, and generation/judge token usage. Judge each distinct comparison for supported relationships and false implications, with verbatim evidence. Report comparison presence, count, comparisons per 100 words, supported links, false implications, length compliance, adaptation success, and specific limitation identification. A separate quality pie shows answers containing at least one comparison with two supported links and no annotated false implications. This preregistered pilot threshold operationalizes a meaningful mapping; it is not a definition of all meaningful metaphors. Automated relationship counts are annotations requiring review, not objective ground truth or an originality score.

Each report folder contains an HTML report, standalone SVG pie charts and scatter plots, `summary.json`, `metrics.csv`, `correlations.csv`, and `human_review.csv`. Pie charts show comparison presence or adaptation/limitation success by model and condition, with positive/judged/planned counts. They pool the three systems; inspect the system-level CSV, especially if cells are missing. Missing judgments never count as negative. Uncollected data show placeholders, never simulated findings.

Correlations include Pearson and Spearman with sample sizes: output words versus comparison count/supported links within model/system/condition; context input words versus output words/comparison frequency within model/system/relevance/answer-length/variant. No correlation is calculated from historical aggregate counts. Undefined correlations stay blank (JSON percentages use null where unobserved); constant variables or fewer than three observations cannot establish an association. Baseline-only strata have no input-length variation. These are exploratory descriptive associations; small cells, shared prompts, multiple comparisons, and two main length levels limit interpretation. No automatic significance claims or causal conclusions from r.

Primary analysis: compare within-system condition differences in presence rates and revision success; show each system and model separately before pooling. Compare long minus short within matched context variants and answer-length instructions. Check actual answer length/compliance alongside intended length. Keep noncompliant answers in the primary intention-to-instruct analysis; report compliant-only results as sensitivity analysis. Correlations supplement these contrasts and cannot replace them. For confirmatory work, preregister primary contrasts and add enough independent systems to estimate uncertainty by resampling systems, not individual repeated answers.

## Human review and conclusion rules

Review sheets omit model and condition labels and shuffle rows, although wording may reveal condition. Retain keys to join annotations with metrics. Human reviewers should assess at least 20 answers or 20% per experiment (whichever is larger, capped at available answers), balanced across conditions, plus borderline cases. Two independent readers should first annotate the same subset, compare agreement and confusion counts, and resolve rubric differences. Report generation never overwrites the edited review sheet; refreshed rows go to a separate file. Agreement calculations and adjudication are manual in this pilot.

A defensible positive conclusion is: “The model constructed comparisons that preserved relationships in unfamiliar scenarios and revised them when those relationships changed.” Trigger conclusions concern the tested instructions and systems only. Fluent wording, source-domain diversity, or a high metaphor rate alone do not establish meaningful construction. Familiar images can still support new mappings. API behavior alone cannot prove retrieval from training, human-like semantic experience, or the parameter-level mechanism.

## Executed pilot and followups

Collection is complete; see `results.md` and `hypothesis.json`. GPT-5 provided the nine-answer smoke test. Separate `_pilot.json` files specify GPT-4o and two trials per case: creation 18, triggers 24, context 108, and grounded followup 12 answers. The followup explicitly prohibits invented source behavior. A final `metaphor_relational_choice_pilot.json` adds 48 matched A/B choices, varying rule direction, option order, and neutral/misleading names. Total: 219 generated answers. No further API collection is running.

The choice probe measures explicitly requested relation discrimination, not generation. Its primary accuracy is computed directly from all 48 saved A/B choices. Forty-two optional metaphor judgments were also accepted; six failed exact-evidence validation and were not retried again because they are unnecessary for choice accuracy. Future choice runs skip the paid judge. Open-ended experiments have 171/171 accepted judgments. The unchanged-rule control remains untested.

Evaluator evidence and output-format instructions were repaired during collection. Accepted earlier labels remain available; they were not silently rewritten. Some failed judgments were retried across invocations; three attempts was the per-invocation cap. Raw returned attempts and usage remain saved, and `hypothesis.json` records the actual maximum per answer. Treat the entire run as an adaptive pilot. Revisions include response-only evidence, trusted validation feedback outside the data payload, and strict schemas for conditional labels.

Both stored project virtual environments had empty interpreter files. The working session environment is `/tmp/magics-study-env`; use `/tmp/magics-study-env/bin/python` in place of `.venv/bin/python` in the commands above. To recreate after `/tmp` is cleared, run `python3 -m venv /tmp/magics-study-env` and install `requirements.txt` with that interpreter.

Regenerate all collected reports and matched contrasts offline:

```bash
python3 summarize_metaphor_study.py
```

This writes a combined report index, model-specific charts/CSVs, findings JSON, and deterministic choice scores. `analyst_audit.json` contains a qualitative assistant review of 30 answers, not human validation. Human annotation and agreement statistics remain future work. An unchanged-rule control, harder relation probes, and more independently designed systems should precede a confirmatory claim.
