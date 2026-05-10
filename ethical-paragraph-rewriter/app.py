import json
import os
import re
from difflib import SequenceMatcher

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from openai import OpenAI

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency is declared in requirements.txt
    OpenAI = None

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

MAX_WORDS = 2000
TONES = ["academic", "simple", "professional", "casual"]
HIGH_SIMILARITY_THRESHOLD = 55
MODERATE_SIMILARITY_THRESHOLD = 35
SOURCE_HINT_PATTERN = re.compile(
    r"\b(according to|source|article|paper|study|research|journal|author|quote|doi|url|website|book)\b",
    re.IGNORECASE,
)
PHRASE_REPLACEMENTS = (
    (r"\bvery\b", ""),
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bthe reason why\b", "the reason"),
    (r"\ba lot of\b", "many"),
    (r"\bshows that\b", "indicates that"),
    (r"\bshow that\b", "indicate that"),
    (r"\bimportant\b", "significant"),
    (r"\bhelp\b", "support"),
    (r"\bhelps\b", "supports"),
    (r"\buse\b", "apply"),
    (r"\buses\b", "applies"),
    (r"\bmake\b", "create"),
    (r"\bmakes\b", "creates"),
    (r"\bchange\b", "shift"),
    (r"\bchanges\b", "shifts"),
    (r"\bget\b", "receive"),
    (r"\bgets\b", "receives"),
    (r"\bbig\b", "substantial"),
    (r"\bsmall\b", "limited"),
    (r"\bbad\b", "harmful"),
    (r"\bgood\b", "beneficial"),
    (r"\bneighborhoods\b", "communities"),
    (r"\bmore tree cover\b", "denser tree canopy"),
    (r"\boften stay cooler\b", "can remain cooler"),
    (r"\bheat waves\b", "periods of extreme heat"),
    (r"\bmay support\b", "can contribute to"),
    (r"\bbetter public health outcomes\b", "improved public health results"),
)
DEFAULT_OPENER = "A clearer revision is: "
TONE_OPENERS = {
    "academic": "A more academic phrasing is: ",
    "simple": "In simpler terms: ",
    "professional": "A professional revision would be: ",
    "casual": "A more conversational version is: ",
}


def count_words(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def normalize_spacing(text: str) -> str:
    paragraphs = [re.sub(r"[ \t]+", " ", part).strip() for part in re.split(r"\n\s*\n", text)]
    return "\n\n".join(part for part in paragraphs if part)


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def clean_sentence(sentence: str) -> str:
    cleaned = sentence.strip()
    for pattern, replacement in PHRASE_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def restructure_source_sentence(sentence: str) -> str:
    source_match = re.match(r"according to\s+([^,]+),\s*(.+)", sentence, flags=re.IGNORECASE)
    if source_match:
        source, claim = source_match.groups()
        claim = claim.strip()
        if not claim:
            return sentence
        return f"The cited source ({source.strip()}) indicates that {claim[0].lower()}{claim[1:]}"
    return sentence


def add_sentence_period(sentence: str) -> str:
    if sentence and sentence[-1] not in ".!?":
        return f"{sentence}."
    return sentence


def apply_local_tone_guidance(text: str, tone: str, target_audience: str) -> str:
    normalized = normalize_spacing(text)
    sentences = split_sentences(normalized)

    if not sentences:
        rewritten = normalized
    else:
        rewritten_sentences = []
        for index, sentence in enumerate(sentences):
            revised = clean_sentence(restructure_source_sentence(sentence))
            if index == 0:
                opener = TONE_OPENERS.get(tone, DEFAULT_OPENER)
                revised = opener + revised[0].lower() + revised[1:]
            elif index > 0 and tone == "academic":
                revised = re.sub(r"^Also,?\s+", "Additionally, ", revised, flags=re.IGNORECASE)
            elif index > 0 and tone == "simple":
                revised = re.sub(r"^Additionally,?\s+", "Also, ", revised, flags=re.IGNORECASE)
            rewritten_sentences.append(add_sentence_period(revised))
        rewritten = " ".join(rewritten_sentences)

    if target_audience:
        rewritten += f" For {target_audience.strip()}, the key idea is presented without adding new claims."
        for sentence in sentences:
            sentence = re.sub(r"\bvery\b", "", sentence, flags=re.IGNORECASE)
            sentence = re.sub(r"\s{2,}", " ", sentence).strip()
            rewritten_sentences.append(sentence)
        rewritten = " ".join(rewritten_sentences)

    prefix_by_tone = {
        "academic": "In academic terms, ",
        "simple": "Simply put, ",
        "professional": "From a professional perspective, ",
        "casual": "In everyday language, ",
    }

    if tone in prefix_by_tone and rewritten:
        rewritten = prefix_by_tone[tone] + rewritten[0].lower() + rewritten[1:]

    if target_audience:
        rewritten += f" This version is intended to be clear for {target_audience.strip()}."

    return rewritten


def local_rewrite(text: str, tone: str, target_audience: str, source_note: str) -> dict:
    rewritten = apply_local_tone_guidance(text, tone, target_audience)
    changes = [
        "Cleaned up extra spacing and line breaks.",
        "Reworked common wordy phrases into clearer alternatives.",
        "Added a transparent framing phrase so the draft reads as a revision, not a hidden copy.",
    ]

    if SOURCE_HINT_PATTERN.search(text):
        changes.append("Reframed source-led wording to keep attribution visible.")
    if tone:
        changes.append(f"Adjusted the opening for a {tone} tone.")
    if target_audience:
        changes.append("Added audience-aware wording guidance without introducing new source claims.")
        "Adjusted phrasing for a clearer, more readable flow.",
    ]

    if tone:
        changes.append(f"Added light {tone} tone guidance.")
    if target_audience:
        changes.append("Added audience-aware wording guidance.")
    if source_note:
        changes.append("Kept citation context visible for responsible attribution.")

    return {
        "rewritten_text": rewritten,
        "changes_made": changes,
        "citation_reminder": (
            "Paraphrasing does not remove the need for citation. If the ideas, data, "
            "or wording came from a source, cite that source in the format required by your instructor, "
            "publication, or organization."
        ),
    }


def openai_rewrite(text: str, tone: str, target_audience: str, source_note: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
    if not api_key or OpenAI is None:
        return None

    client = OpenAI(api_key=api_key)
    system_prompt = (
        "You are an ethical writing assistant. Rewrite the user's paragraph for clarity, flow, "
        "grammar, tone, and originality while preserving the original meaning. Do not provide help "
        "intended to defeat AI detectors, similarity checkers, plagiarism systems, or academic integrity "
        "review. Do not promise that the result will pass plagiarism or similarity screening. If the "
        "paragraph appears to be based on source material, remind the user to cite the source. Return "
        "only valid JSON with keys: rewritten_text, changes_made, citation_reminder."
        "review. If the paragraph appears to be based on source material, remind the user to cite the "
        "source. Return only valid JSON with keys: rewritten_text, changes_made, citation_reminder."
    )
    user_payload = {
        "paragraph": text,
        "desired_tone": tone or "not specified",
        "target_audience": target_audience or "not specified",
        "source_or_citation_note": source_note or "not specified",
    }

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    return {
        "rewritten_text": str(data.get("rewritten_text", "")).strip(),
        "changes_made": [str(item).strip() for item in data.get("changes_made", []) if str(item).strip()],
        "citation_reminder": str(data.get("citation_reminder", "")).strip(),
    }


def rewrite_paragraph(text: str, tone: str, target_audience: str, source_note: str) -> dict:
    try:
        result = openai_rewrite(text, tone, target_audience, source_note)
    except Exception:
        result = None

    if not result or not result.get("rewritten_text"):
        result = local_rewrite(text, tone, target_audience, source_note)

    if not result.get("changes_made"):
        result["changes_made"] = ["Revised wording for clarity while preserving the original meaning."]
    if not result.get("citation_reminder"):
        result["citation_reminder"] = "Paraphrasing does not remove the need for citation."

    return result


def similarity_percentage(original: str, rewritten: str) -> int:
    ratio = SequenceMatcher(None, original.lower().strip(), rewritten.lower().strip()).ratio()
    return round(ratio * 100)


def appears_source_based(text: str, source_note: str) -> bool:
    return bool(source_note.strip() or SOURCE_HINT_PATTERN.search(text))


def build_revision_advice(similarity: int, source_warning: bool) -> list[str]:
    advice = [
        "Review the rewrite yourself and replace any wording that still follows the source too closely.",
        "Use the result as a draft for learning and revision rather than as a guarantee of originality.",
    ]
    if similarity >= HIGH_SIMILARITY_THRESHOLD:
        advice.insert(0, "Similarity is still high, so make a deeper revision before submitting or publishing.")
    elif similarity >= MODERATE_SIMILARITY_THRESHOLD:
        advice.insert(0, "Similarity is moderate; check whether key phrases or sentence structure still mirror the original.")
    else:
        advice.insert(0, "Similarity is lower, but originality also depends on your ideas, structure, and citations.")
    if source_warning:
        advice.append("Add an in-text citation and full reference for any source ideas, facts, or wording you used.")
    return advice


@app.get("/")
def index():
    return render_template("index.html", tones=TONES)


@app.post("/rewrite")
def rewrite():
    paragraph = request.form.get("paragraph", "").strip()
    tone = request.form.get("tone", "").strip().lower()
    target_audience = request.form.get("target_audience", "").strip()
    source_note = request.form.get("source_note", "").strip()

    if not paragraph:
        flash("Please paste a paragraph before requesting an ethical rewrite.", "error")
        return redirect(url_for("index"))

    word_count = count_words(paragraph)
    if word_count > MAX_WORDS:
        flash(f"Please limit the paragraph to {MAX_WORDS:,} words. Your text has {word_count:,} words.", "error")
        return redirect(url_for("index"))

    if tone and tone not in TONES:
        flash("Please choose one of the listed tones.", "error")
        return redirect(url_for("index"))

    result = rewrite_paragraph(paragraph, tone, target_audience, source_note)
    similarity = similarity_percentage(paragraph, result["rewritten_text"])
    high_similarity = similarity >= HIGH_SIMILARITY_THRESHOLD
    moderate_similarity = MODERATE_SIMILARITY_THRESHOLD <= similarity < HIGH_SIMILARITY_THRESHOLD
    high_similarity = similarity >= 70
    source_warning = appears_source_based(paragraph, source_note)

    return render_template(
        "result.html",
        original_text=paragraph,
        rewritten_text=result["rewritten_text"],
        changes_made=result["changes_made"],
        citation_reminder=result["citation_reminder"],
        similarity=similarity,
        high_similarity=high_similarity,
        moderate_similarity=moderate_similarity,
        source_warning=source_warning,
        revision_advice=build_revision_advice(similarity, source_warning),
        source_warning=source_warning,
        tone=tone,
        target_audience=target_audience,
        source_note=source_note,
    )


if __name__ == "__main__":
    app.run(debug=True)
