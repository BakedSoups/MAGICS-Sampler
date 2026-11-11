# Idiom experiment

- [Input JSON](input.json)
- [Findings PDF](findings.pdf)
- Additional inputs: [comprehension](comprehension.json), [usage](usage.json)

The saved surprise-party run has eight answers, one per model/audience cell. It is a smoke test, not a model ranking. Other idiom input sets are preserved but have no collected results here.

From the project root, regenerate the PDF offline with `python3 idiom/tools/report.py`.

`tools/run_experiment.py` runs the idiom input using the OpenAI API and honors its JSON settings. Live requests require the SDK and OPENAI_API_KEY and may incur costs; completed saved judgments are reused. Choose a new output directory in that script when changing settings.
