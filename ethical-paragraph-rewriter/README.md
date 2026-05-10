# Ethical Paragraph Rewriter

A Python Flask web app that helps users rewrite paragraphs for clarity, grammar, tone, and originality while encouraging proper citation and responsible writing practices.

The app does **not** claim to defeat AI detectors, plagiarism checkers, or academic integrity systems. It is designed as a writing-assistance and learning tool.

## Features

- Homepage with a paragraph textarea.
- Optional desired tone: academic, simple, professional, or casual.
- Optional target-audience field.
- Optional source/citation note field.
- Ethical rewrite result with:
  - Rewritten paragraph.
  - Bullet list of major changes.
  - Similarity percentage using Python `difflib`.
  - Practical guidance when similarity remains high or a checker may still flag overlap.
  - Warning when the paragraph appears to rely on source material.
  - Citation reminder explaining that paraphrasing still requires attribution.
- Optional OpenAI API integration via `OPENAI_API_KEY`.
- Local fallback rewrite when no API key is present.
- No permanent storage of user text by this app.

## Project structure

```text
ethical-paragraph-rewriter/
  app.py
  requirements.txt
  .env.example
  README.md
  templates/
    base.html
    index.html
    result.html
  static/
    style.css
```

## Requirements

- Python 3.11+
- Flask
- Jinja2 templates
- python-dotenv
- OpenAI Python SDK for optional API-assisted rewrites

## Setup

From the project directory:

```bash
cd ethical-paragraph-rewriter
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `python3.11` is not available on your system, use another Python 3.11+ executable, such as `python3`.

## Environment variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

To enable OpenAI-assisted rewriting, edit `.env` and add your key:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
FLASK_SECRET_KEY=replace-with-a-random-secret
```

If `OPENAI_API_KEY` is empty or unavailable, the app uses a local rewrite helper that cleans spacing, restructures source-led openings, replaces common wordy phrases, and provides citation guidance. The local helper is intentionally conservative and cannot guarantee that a similarity or plagiarism checker will consider the result sufficiently original.
If `OPENAI_API_KEY` is empty or unavailable, the app uses a basic local rewrite placeholder that improves spacing, lightly adjusts phrasing, and provides citation guidance.

## Run locally

```bash
flask --app app run --debug
```

Then open the local URL shown in your terminal, usually:

```text
http://127.0.0.1:5000
```

## Example

### Example input

```text
According to a recent article about urban trees, neighborhoods with more tree cover often stay cooler during heat waves and may support better public health outcomes.
```

Desired tone: `academic`

Source/citation note:

```text
Based on an article about urban tree canopy and heat waves.
```

### Example output

```text
A more academic phrasing is: the cited source (a recent article about urban trees) indicates that communities with denser tree canopy can remain cooler during periods of extreme heat and can contribute to improved public health results.
In academic terms, according to a recent article about urban trees, neighborhoods with more tree cover often stay cooler during heat waves and may support better public health outcomes.
```

Major changes may include:

- Cleaned up extra spacing and line breaks.
- Reworked common wordy phrases into clearer alternatives.
- Adjusted the opening for an academic tone.
- Kept citation context visible for responsible attribution.

The result page also shows a similarity percentage, gives practical next steps if a similarity checker still flags overlap, and reminds you to cite the original source when the ideas, data, or wording come from another author.

## Academic integrity disclaimer

Use this app to improve your writing and understand revision choices. It cannot guarantee that a plagiarism or similarity checker will clear a passage. You remain responsible for complying with your institution, publisher, or workplace rules. Paraphrasing does not remove the need for citation when you rely on another author’s ideas, evidence, structure, or wording. When relevant, include the author, title, URL or DOI, publication details, and access date in the required citation style.
- Adjusted phrasing for a clearer, more readable flow.
- Added light academic tone guidance.
- Kept citation context visible for responsible attribution.

The result page also shows a similarity percentage and reminds you to cite the original source when the ideas, data, or wording come from another author.

## Academic integrity disclaimer

Use this app to improve your writing and understand revision choices. You remain responsible for complying with your institution, publisher, or workplace rules. Paraphrasing does not remove the need for citation when you rely on another author’s ideas, evidence, structure, or wording. When relevant, include the author, title, URL or DOI, publication details, and access date in the required citation style.
