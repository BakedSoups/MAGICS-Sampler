# Run or review the experiment

The two files to open are [input.json](../input.json) and [findings.pdf](../findings.pdf).

[Answers and original judge outputs](data/lru_lrm_context_results.json) are preserved with separate manual-review fields. Set `manual_review.status` to `reviewed` and a boolean `manual_review.overrides.explanatory_comparison` to correct presence. Original judge outputs remain unchanged. Factual accuracy is separate.

From the project root:

```bash
# Offline: regenerate the PDF, charts, and review export.
python3 tools/report_cache_context.py

# Offline: preview the configured API run.
python3 tools/run_metaphor_study.py

# Billed: collect/resume the configured run (requires OpenAI SDK and OPENAI_API_KEY).
python3 tools/run_metaphor_study.py --live --workers 4
```

Install dependencies from `tools/requirements.txt` into a working virtual environment for live collection. Existing completed answers are reused. If you change experimental settings, choose a fresh output folder using `--output runs/<new-name>`.

`runs/` contains the original response and judge-attempt logs. `reports/` contains the detailed HTML, CSV, and SVG outputs. The other Python files are shared dependencies; use the commands above as entry points.
