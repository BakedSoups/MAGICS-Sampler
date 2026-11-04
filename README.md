# Figurative language experiments

Run from this directory with your virtual environment activated and
OPENAI_API_KEY exported in your shell:

```bash
source venv/bin/activate
python run_experiment.py
python json_to_data_report.py
```

No command-line flags are needed. Edit settings at the top of each script.

In `run_experiment.py`, `MODELS` is the list of models to test. Defaults are
`gpt-5` and `gpt-4o`, which succeeded in the user's run. The original `o3-mini`
and `gpt-4.1-nano` IDs were rejected by the API. `EXPERIMENT` selects the question
file, `TRIALS` sets repetitions per question/model (1 for a smoke test, 20 for
the full experiment), and `JUDGE_MODEL` selects the evaluator. `DRY_RUN = True`
prints planned calls without making requests. Live runs incur response and
judge costs; invalid judgments may trigger up to two extra judge calls.

The default question is “My friend accidentally revealed a surprise party.
How would you describe what happened?” It tests spontaneous idiom usage in
four audience versions without explicitly asking for an idiom.

`python json_to_data_report.py` automatically scans `data/` and `runs/` for
supported findings. It generates individual PDFs for each experiment and metric,
plus `reports/all_findings.pdf` containing everything. Experiment definitions
without results are skipped; run summaries aren't counted again alongside raw
records. Both idiom and metaphor metrics are included for language runs, and
both correctness metrics for comprehension runs. No flags, API key, or extra
packages are needed. Edit `SOURCE_DIRECTORIES` or `REPORT_DIRECTORY` at the top
of the report script to change destinations.

The historical screenshot findings live in:

- `runs/metaphors_based_on_role/random_forest.json`
- `runs/metaphors_based_on_role/water_temperature.json`

These retain counts, prompts, excerpts, model IDs, and provenance needed to
recreate the previous findings as PDFs. They contain 32 cells and 640 total
responses. The report reproduces their findings in the current report layout;
the original full answers and judge settings were not supplied.

Reports deduplicate raw records by key, calculate percentages from judged
responses only, and show missing cells. Long prompts and excerpts are shortened
for display. Built-in Helvetica supports Western European text; unsupported
characters are replaced with question marks.

## Data and resuming

Each run folder contains:

- `config.json`: effective run settings.
- `records.jsonl`: append-only response and judgment records, including full
  answers, timestamps, response IDs, resolved models, and token usage for saved
  responses and accepted judgments. Corrective judge attempts can add usage
  beyond the accepted judgment's recorded usage.
- `summary.json`: per-model/per-question counts and percentages.
- `errors.jsonl`: failed attempts, stage, and error details.

Rerun `python run_experiment.py` to resume. Completed judgments are skipped;
saved answers awaiting judgment are reused. Model list changes are allowed in
the same folder; summaries include only selected models. Old records remain
available. If you change prompts, trials, or other evaluation settings, choose
a new `OUTPUT_DIRECTORY`. Run only one process per output directory. A crash
between an API call and its local save can still repeat a billed call.

The evaluator scores metaphors/analogies and idioms separately and requires
verbatim evidence. Automated labels may be wrong; inspect borderline cases.
One response per cell gives only 0% or 100%, not a reliable model ranking.

## Experiment files

- `experiments/idiom_surprise_party.json`: default idiom usage question.
- `experiments/metaphors.json`: original random forest and water questions.
- `experiments/idiom_usage.json`: same original questions, scored for idioms too.
- `experiments/idiom_comprehension.json`: ten contextual idiom/literal cases,
  with separate judgments for meaning and expression type. References are
  supplied only to the judge. This is an exploratory English starter set.

Install dependencies if needed with `python -m pip install -r requirements.txt`.
API implementation follows the official OpenAI quickstart:
https://developers.openai.com/api/docs/quickstart
