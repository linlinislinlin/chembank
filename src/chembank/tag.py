"""AI auto-tagging constrained to the syllabus vocabulary."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chembank.export_md import write_question_markdown
from chembank.syllabus import (
    DEFAULT_SYLLABUS,
    as_only_codes,
    flatten_codes,
    flatten_learning_outcomes,
    list_codes,
    parent_code_for_lo,
    validate_learning_outcomes,
    load_syllabus,
    resolve_titles,
)

ALLOWED_SKILLS = {
    "recall",
    "explain",
    "calculate",
    "data-analysis",
    "practical",
    "compare",
    "evaluate",
    "draw",
}
ALLOWED_QUESTION_TYPES = {"mcq", "structured", "extended", "practical", "data"}

# Stem-first mock rules (pattern, codes, skills). Order = priority.
# Prefer what the stem *asks*; avoid option-keyword steal and reagent over-tag.
# Tag the assessed skill (command word + calculation), NOT decorative chemical context.
_MOCK_STEM_RULES: list[tuple[re.Pattern[str], list[str], list[str]]] = [
    # Energetics FIRST — before isotope / Period 3 oxide lists / kinetics Ea steal
    (
        re.compile(
            r"\b(hess(?:'?s)?\s+law|energy cycle|"
            r"enthalpy change of formation|enthalpy of formation|"
            r"reaction pathway diagram|reaction profile|"
            r"calculate.{0,40}enthalpy|bond energ(?:y|ies))\b",
            re.I | re.S,
        ),
        ["5.1", "5.2"],
        ["calculate"],
    ),
    (
        re.compile(r"\b(enthalpy|hess|ΔH|∆H|delta H)\b", re.I),
        ["5.1", "5.2"],
        ["calculate"],
    ),
    # Kinetics asks (after energetics so pathway+ΔH/Ea → 5.1)
    (
        re.compile(r"\b(boltzmann|molecular energy|number of molecules)\b", re.I),
        ["8.2"],
        ["explain", "recall"],
    ),
    (
        re.compile(r"\b(heat exchanger|haber process)\b", re.I),
        ["8.1", "12.1"],
        ["explain"],
    ),
    (
        re.compile(r"\b(catalysts?)\b", re.I),
        ["8.3", "8.1"],
        ["explain", "recall"],
    ),
    (
        re.compile(r"\b(rate of reaction|activation energy)\b", re.I),
        ["8.1"],
        ["explain"],
    ),
    # Atomic structure / bonding asks (before option nouns like orbital / ionic)
    (
        re.compile(r"\b(ionisation|ionization)\s+energy\b", re.I),
        ["1.4"],
        ["explain", "recall"],
    ),
    (
        re.compile(
            r"\b(period 3).*\b(p electron|oxide|amphoteric)|"
            r"\b(forms a solid oxide)\b.*\b(hydroxide|hydrochloric)\b",
            re.I | re.S,
        ),
        ["9.2", "1.3"],
        ["recall", "compare"],
    ),
    (
        re.compile(r"\b(unpaired|p electron|electron configuration)\b", re.I),
        ["1.3"],
        ["recall"],
    ),
    (
        re.compile(r"\b(isotope)\b", re.I),
        ["1.2"],
        ["recall"],
    ),
    (
        re.compile(
            r"\b(shape of|bond angle)\b",
            re.I,
        ),
        ["3.5"],
        ["recall", "draw"],
    ),
    (
        re.compile(r"\b(volatility|intermolecular)\b", re.I),
        ["11.1", "3.6"],
        ["explain", "compare"],
    ),
    (
        re.compile(r"\b(ideal gas|pV\s*=\s*nRT)\b", re.I),
        ["4.1"],
        ["calculate"],
    ),
    # Redox / equilibrium
    (
        re.compile(r"\b(oxidation number|oxidation state|redox|half[- ]equation)\b", re.I),
        ["6.1"],
        ["recall", "explain"],
    ),
    (
        re.compile(r"\b(Kc|Kp|equilibrium constant)\b", re.I),
        ["7.1", "7.2"],
        ["calculate", "explain"],
    ),
    # Organic / polyfunctional before generic mole-count (citric acid etc.)
    (
        re.compile(
            r"\b(citric acid)\b|"
            r"\b(excess of sodium metal)\b.*\b(acid|CO2H)\b|"
            r"\b(CO2H)\b.*\b(HO|OH)\b",
            re.I | re.S,
        ),
        ["18.1", "16.1", "2.2"],
        ["calculate", "recall"],
    ),
    (
        re.compile(r"\b(molecular formula)\b", re.I),
        ["13.1"],
        ["recall"],
    ),
    (
        re.compile(r"\b(SN2|bromoethane|cyanide|propanenitrile)\b", re.I),
        ["15.1", "19.2"],
        ["explain", "recall"],
    ),
    (
        re.compile(r"\b(cis[- ]trans|optical isomerism|chirality)\b", re.I),
        ["13.4"],
        ["recall"],
    ),
    (
        re.compile(r"\b(produce two different carboxylic acids|acidified manganate)\b", re.I),
        ["14.2"],
        ["recall"],
    ),
    (
        re.compile(r"\b(ester|reflux).*(sodium hydroxide|NaOH)|CO2C|palmitate", re.I),
        ["18.2"],
        ["recall"],
    ),
    # Stoichiometry: narrow 2.2 vs 2.4; composition → 2.3+2.4
    (
        re.compile(
            r"\b(complete combustion|minimum mass|combustion of)\b.*\b(dm3|g\b|mass)\b"
            r"|\b(mass of oxygen)\b",
            re.I | re.S,
        ),
        ["2.4"],
        ["calculate"],
    ),
    (
        re.compile(
            r"\d+(?:\.\d+)?\s*g of \w+ contains|\bcontains\b.*\b\d+(?:\.\d+)?\s*g\b|"
            r"\bempirical formula\b",
            re.I | re.S,
        ),
        ["2.3", "2.4"],
        ["calculate"],
    ),
    (
        re.compile(
            r"\b(largest number of|how many (moles|atoms|molecules)|avogadro|"
            r"number of (hydrogen )?atoms)\b",
            re.I,
        ),
        ["2.2"],
        ["calculate", "recall"],
    ),
    # Nitrogen / halogen / Group 2 — stem ask, not reagent nouns
    (
        re.compile(
            r"\b(reacts with Cl\s*[₂2]|reacts with chlorine)\b|"
            r"\b(NH[₄4]Cl)\b.*\b(Cl\s*[₂2]|chlorine)\b|"
            r"\b(Cl\s*[₂2]|chlorine)\b.*\b(NH[₄4]Cl|NH[₃3]|ammonia)\b",
            re.I | re.S,
        ),
        ["12.1", "11.4"],
        ["explain", "recall"],
    ),
    (
        re.compile(r"\b(acid rain|nitrogen dioxide|\bNO2\b)\b", re.I),
        ["12.1"],
        ["explain", "recall"],
    ),
    (
        re.compile(
            r"\b(silver nitrate|halide).*(ammonia|NH3)|"
            r"\b(concentrated ammonia solution)\b",
            re.I | re.S,
        ),
        ["11.3"],
        ["practical", "recall"],
    ),
    (
        re.compile(
            r"\b(group\s*2|alkaline earth|magnesium nitrate|"
            r"thermal decomposition of hydrated)\b",
            re.I,
        ),
        ["10.1"],
        ["recall"],
    ),
    (
        re.compile(r"\b(group\s*17|halogen molecule|chlorine, bromine and iodine)\b", re.I),
        ["11.1"],
        ["recall", "compare"],
    ),
    (
        re.compile(
            r"\b(going across period|across period 3|periodicity|periodic table|"
            r"atomic radius)\b",
            re.I,
        ),
        ["9.1"],
        ["recall", "compare"],
    ),
    (
        re.compile(r"\b(iodoform|carbonyl|aldehyde|ketone|HCN|hydroxynitrile)\b", re.I),
        ["17.1", "19.2"],
        ["recall"],
    ),
    (
        re.compile(r"\b(alcohol|phenol)\b", re.I),
        ["16.1"],
        ["recall"],
    ),
    (
        re.compile(r"\b(electrophilic addition|reaction of .* alkene)\b", re.I),
        ["14.2"],
        ["recall"],
    ),
    (
        re.compile(r"\b(hydrocarbon|functional group|structural isomer)\b", re.I),
        ["13.1"],
        ["recall"],
    ),
    (
        re.compile(r"\b(haber|manufacture of ammonia)\b", re.I),
        ["12.1"],
        ["explain"],
    ),
    (
        re.compile(r"\b(dot-and-cross|VSEPR)\b", re.I),
        ["3.2", "3.4"],
        ["recall", "draw"],
    ),
]

# Full-body fallbacks only for patterns unlikely to be option-steal.
_MOCK_BODY_RULES: list[tuple[re.Pattern[str], list[str], list[str]]] = [
    (
        re.compile(r"\b(mol\b|mole|avogadro)\b", re.I),
        ["2.2"],
        ["calculate", "recall"],
    ),
    (
        re.compile(r"\b(enthalpy|ΔH)\b", re.I),
        ["5.1", "5.2"],
        ["calculate"],
    ),
]


@dataclass
class PaperMeta:
    exam_board: str = "CIE"
    syllabus_code: str = "9701"
    level: str = "AS"
    year: int | None = None
    session: str | None = None
    paper: str | int | None = None
    source_qp: str | None = None
    source_ms: str | None = None

    def question_id(self, question: str) -> str:
        session = (self.session or "xx").lower()
        paper = str(self.paper or "x")
        year = self.year or 0
        q = str(question).replace("(", "").replace(")", "").replace(".", "-")
        return f"cie-{self.syllabus_code}-{year}-{session}-p{paper}-q{q}"


def parse_paper_meta_string(raw: str | None) -> dict[str, Any]:
    """Parse `year=2021,session=MJ,paper=11,level=AS` into a dict."""
    if not raw:
        return {}
    out: dict[str, Any] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "year":
            out[key] = int(value)
        elif key == "paper":
            out[key] = int(value) if value.isdigit() else value
        else:
            out[key] = value
    return out


def infer_paper_meta_from_name(name: str) -> PaperMeta:
    """Infer meta from stems like `9701_s21_qp_11`."""
    meta = PaperMeta()
    m = re.search(
        r"(?P<code>\d{4})_(?P<sess>[smw])(?P<yy>\d{2})_(?:qp|ms)_(?P<paper>\d{1,2})",
        name,
        re.I,
    )
    if not m:
        m = re.search(
            r"(?P<code>\d{4})_(?P<sess>[smw])(?P<yy>\d{2})_p(?P<paper>\d{1,2})",
            name,
            re.I,
        )
    if m:
        meta.syllabus_code = m.group("code")
        yy = int(m.group("yy"))
        meta.year = 2000 + yy if yy < 80 else 1900 + yy
        sess = m.group("sess").lower()
        meta.session = {"s": "MJ", "w": "ON", "m": "FM"}.get(sess, sess.upper())
        meta.paper = int(m.group("paper"))
        paper_num = int(str(meta.paper)[0]) if meta.paper else 0
        meta.level = "AS" if paper_num in (1, 2) else "A"
        stem = f"{meta.syllabus_code}_{sess}{m.group('yy')}"
        meta.source_qp = f"raw/papers/{stem}_qp_{meta.paper}.pdf"
        meta.source_ms = f"raw/papers/{stem}_ms_{meta.paper}.pdf"
    return meta


def allowed_code_list(
    *,
    as_only: bool = True,
    syllabus_path: Path | None = None,
) -> list[tuple[str, str]]:
    path = syllabus_path or DEFAULT_SYLLABUS
    return as_only_codes(path) if as_only else list_codes(path)


def validate_tag_fields(
    tags: dict[str, Any],
    *,
    allowed_codes: set[str],
    syllabus: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate / normalize model output. Raises ValueError on bad codes."""
    codes_raw = tags.get("syllabus_codes") or []
    if not isinstance(codes_raw, list) or not codes_raw:
        raise ValueError("syllabus_codes is required and must be a non-empty list")

    codes: list[str] = []
    for c in codes_raw:
        code = str(c).strip()
        if code not in allowed_codes:
            raise ValueError(f"Unknown or disallowed syllabus code: {code}")
        if code not in codes:
            codes.append(code)

    skills: list[str] = []
    for s in tags.get("skills") or []:
        s = str(s).strip()
        if s in ALLOWED_SKILLS and s not in skills:
            skills.append(s)

    qtype = str(tags.get("question_type") or "mcq").strip()
    if qtype not in ALLOWED_QUESTION_TYPES:
        qtype = "mcq"

    difficulty = tags.get("difficulty")
    if difficulty is not None:
        try:
            difficulty = int(difficulty)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid difficulty: {difficulty}") from exc
        if difficulty < 1 or difficulty > 5:
            raise ValueError(f"difficulty must be 1–5, got {difficulty}")

    command_words = [str(x).strip() for x in (tags.get("command_words") or []) if str(x).strip()]
    misconceptions = [str(x).strip() for x in (tags.get("misconceptions") or []) if str(x).strip()]
    learning_objectives = [
        str(x).strip() for x in (tags.get("learning_objectives") or []) if str(x).strip()
    ]
    syl = syllabus or load_syllabus()
    lo_lookup = flatten_learning_outcomes(syl)
    lo_raw = tags.get("learning_outcomes") or []
    if lo_raw and not isinstance(lo_raw, list):
        raise ValueError("learning_outcomes must be a list of LO ids")
    learning_outcomes = validate_learning_outcomes(
        [str(x) for x in lo_raw],
        syllabus=syl,
        allowed=set(lo_lookup),
    )
    # Ensure parent syllabus_codes cover every LO
    code_titles = flatten_codes(syl)
    for lo_id in learning_outcomes:
        parent = parent_code_for_lo(lo_id)
        if parent in codes or parent.split(".")[0] in codes:
            continue
        if parent in allowed_codes or parent in code_titles:
            codes.append(parent)

    titles = resolve_titles(codes, syl)
    lo_texts = [lo_lookup[i] for i in learning_outcomes]

    return {
        "syllabus_codes": codes,
        "topic_titles": titles,
        "skills": skills,
        "question_type": qtype,
        "difficulty": difficulty if difficulty is not None else 2,
        "command_words": command_words,
        "misconceptions": misconceptions,
        "learning_outcomes": learning_outcomes,
        "learning_outcome_texts": lo_texts,
        "learning_objectives": learning_objectives,
    }


def _split_stem_options(body: str) -> tuple[str, str]:
    """Split MCQ body into stem vs options.

    CIE layouts usually put ``A`` alone on a line, or ``A``/``B``/``C``/``D``
    as consecutive lettered lines. Avoid prose like ``A single gaseous product…``.
    """
    text = body.strip()
    m = re.search(r"(?m)^\s*A\s*$", text)
    if m:
        return text[: m.start()].strip(), text[m.start() :].strip()

    best: re.Match[str] | None = None
    for m in re.finditer(r"(?m)^\s*A\s+\S.*$", text):
        following = [ln for ln in text[m.end() :].splitlines() if ln.strip()][:6]
        letters = [
            lm.group(1)
            for ln in following
            if (lm := re.match(r"^\s*([B-D])\s+\S", ln))
        ]
        if letters[:3] == ["B", "C", "D"]:
            best = m  # prefer the last A/B/C/D block
    if best:
        return text[: best.start()].strip(), text[best.start() :].strip()
    return text, ""


def _mock_hit(
    codes: list[str],
    skills: list[str],
    *,
    question_type: str,
    fallback: bool = False,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "syllabus_codes": list(codes),
        "skills": list(skills),
        "question_type": question_type,
        "difficulty": 2,
        "command_words": [],
        "misconceptions": [],
        "learning_outcomes": [],
        "learning_objectives": [],
    }
    if fallback:
        out["_mock_fallback"] = True
    return out


def mock_tag_question(body: str, *, question_type: str = "mcq") -> dict[str, Any]:
    """Deterministic tagging for dry-run / CI without an API key.

    Prefers stem asks over option/reagent keywords (see spot-check-notes).
    """
    stem, _options = _split_stem_options(body)

    for pattern, codes, skills in _MOCK_STEM_RULES:
        if pattern.search(stem):
            return _mock_hit(codes, skills, question_type=question_type)

    for pattern, codes, skills in _MOCK_BODY_RULES:
        if pattern.search(body):
            return _mock_hit(codes, skills, question_type=question_type)

    # Last-resort fallbacks — avoid bare 1.1 (atomic radius) which is almost always wrong.
    if re.search(r"\b(C\d+H\d+|organic|structure)\b", body, re.I):
        return _mock_hit(["13.1"], ["recall"], question_type=question_type, fallback=True)
    if re.search(r"\b(mol\b|mass|dm3|gaseous product)\b", body, re.I):
        return _mock_hit(["2.2"], ["calculate"], question_type=question_type, fallback=True)

    return _mock_hit(["2.2"], ["recall"], question_type=question_type, fallback=True)


def _strip_ms_section(text: str) -> tuple[str, str | None]:
    """Split draft body from appended `--- MARK SCHEME ---` block."""
    parts = re.split(r"\n--- MARK SCHEME ---\n", text, maxsplit=1)
    body = parts[0].strip()
    ms_answer = None
    if len(parts) == 2:
        m = re.search(r"Answer:\s*([A-D])", parts[1], re.I)
        if m:
            ms_answer = m.group(1).upper()
    return body, ms_answer


def build_tag_prompt(
    *,
    body: str,
    ms_answer: str | None,
    vocabulary: list[tuple[str, str]],
    question_type_hint: str = "mcq",
) -> tuple[str, str]:
    vocab_lines = "\n".join(f"- {code}: {title}" for code, title in vocabulary)
    system = (
        "You are tagging Cambridge International AS & A Level Chemistry (9701) past-paper "
        "questions. Assign syllabus_codes ONLY from the provided controlled vocabulary. "
        "Never invent new codes. Prefer the most specific subtopic codes. "
        "Tag the skill being assessed (command word + required calculation/explanation), "
        "NOT decorative chemical context (e.g. a Period 3 oxides list is not bonding LO 4.2). "
        "Enthalpy / Hess / ΔH / ΔHf / ΔHr calculations → topic 5.x, never 4.2. "
        "If context spans multiple topics, prefer the LO that matches the mark scheme / asked task. "
        "FORBIDDEN: tagging from an intro list of compounds alone. "
        "Return a single JSON object only."
    )
    user = f"""Tag the following chemistry question.

Allowed syllabus codes (code: title):
{vocab_lines}

Allowed skills: {", ".join(sorted(ALLOWED_SKILLS))}
Allowed question_type: {", ".join(sorted(ALLOWED_QUESTION_TYPES))}
difficulty: integer 1 (easiest) to 5 (hardest)

Hard rules:
- Tag the assessed skill for THIS part only (not the whole question's theme).
- Enthalpy/Hess/ΔH calculations → 5.1 / 5.2 (never 4.2 bonding from oxide context).
- Prefer LO matching the mark scheme / calculation asked.
- FORBIDDEN: tagging from intro compound lists alone.

Return JSON with keys:
{{
  "syllabus_codes": ["<code>", ...],   // required, ≥1, from allowed list only
  "skills": ["..."],
  "question_type": "{question_type_hint}",
  "difficulty": 2,
  "command_words": [],
  "misconceptions": [],                // optional teaching notes
  "learning_outcomes": ["3.1-1"],      // REQUIRED: ≥1 CIE LO id from vocabulary (e.g. 3.1-1, 2.4-1a)
  "learning_objectives": []            // optional free-text notes — NOT syllabus LO ids
}}

Mark scheme answer (if known): {ms_answer or "unknown"}

Question text:
\"\"\"
{body}
\"\"\"
"""
    return system, user


def call_openai_compatible(
    *,
    system: str,
    user: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Call an OpenAI-compatible chat completions endpoint in JSON mode."""
    key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("CHEMBANK_API_KEY")
    if not key:
        raise RuntimeError(
            "No API key. Set OPENAI_API_KEY (or CHEMBANK_API_KEY), or pass --mock."
        )
    url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip(
        "/"
    )
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    model_name = model or os.environ.get("CHEMBANK_MODEL") or os.environ.get(
        "OPENAI_MODEL", "gpt-4o-mini"
    )

    payload = {
        "model": model_name,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "chembank/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:500]}") from exc

    content = raw["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return json.loads(content)


def tag_question_text(
    text: str,
    *,
    paper_meta: PaperMeta,
    question: str,
    page_hint: int | None = None,
    ms_answer: str | None = None,
    question_type_hint: str = "mcq",
    as_only: bool = True,
    syllabus_path: Path | None = None,
    mock: bool = False,
    model: str | None = None,
) -> dict[str, Any]:
    """Tag one question draft; return a full question record ready for export."""
    body, embedded_ms = _strip_ms_section(text)
    answer = ms_answer or embedded_ms

    syllabus = load_syllabus(syllabus_path)
    vocabulary = allowed_code_list(as_only=as_only, syllabus_path=syllabus_path)
    allowed = {c for c, _ in vocabulary}
    # Also allow major topic codes that appear in the vocabulary flatten for titles
    all_titles = flatten_codes(syllabus)

    if mock or os.environ.get("CHEMBANK_TAG_MOCK", "").lower() in {"1", "true", "yes"}:
        raw_tags = mock_tag_question(body, question_type=question_type_hint)
    else:
        system, user = build_tag_prompt(
            body=body,
            ms_answer=answer,
            vocabulary=vocabulary,
            question_type_hint=question_type_hint,
        )
        raw_tags = call_openai_compatible(system=system, user=user, model=model)

    validated = validate_tag_fields(raw_tags, allowed_codes=allowed, syllabus=syllabus)
    # Prefer titles without [AS]/[A] suffix noise for subtopics
    validated["topic_titles"] = [all_titles[c] for c in validated["syllabus_codes"]]

    marks = 1 if question_type_hint == "mcq" else None
    record: dict[str, Any] = {
        "id": paper_meta.question_id(question),
        "exam_board": paper_meta.exam_board,
        "syllabus_code": paper_meta.syllabus_code,
        "level": paper_meta.level,
        "year": paper_meta.year,
        "session": paper_meta.session,
        "paper": paper_meta.paper,
        "question": str(question),
        "marks": marks,
        **validated,
        "ms_answer": answer,
        "source_qp": paper_meta.source_qp,
        "source_ms": paper_meta.source_ms,
        "page_qp": page_hint,
        "body": body,
        "mark_scheme": f"Answer: **{answer}**" if answer else "",
    }
    return record


def _load_ms_key(draft_dir: Path) -> dict[str, str]:
    path = draft_dir / "ms_key.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def _load_index(draft_dir: Path) -> dict[str, dict[str, Any]]:
    path = draft_dir / "index.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {str(r["question"]): r for r in rows}


def iter_draft_questions(
    draft_dir: Path,
    *,
    only: list[str] | None = None,
    limit: int | None = None,
) -> list[tuple[str, Path]]:
    files = sorted(
        draft_dir.glob("q*.txt"),
        key=lambda p: int(re.search(r"\d+", p.stem).group()) if re.search(r"\d+", p.stem) else 0,
    )
    only_set = {str(x) for x in only} if only else None
    items: list[tuple[str, Path]] = []
    for path in files:
        qnum = re.match(r"q(\d+)\.txt$", path.name)
        if qnum:
            q = str(int(qnum.group(1)))
        else:
            m = re.match(r"q(.+)\.txt$", path.name)
            if not m:
                continue
            q = m.group(1)
        if only_set is not None and q not in only_set:
            continue
        items.append((q, path))
    if limit is not None:
        items = items[:limit]
    return items


def tag_draft_dir(
    draft_dir: Path,
    *,
    paper_meta: PaperMeta | None = None,
    paper_meta_overrides: dict[str, Any] | None = None,
    as_only: bool = True,
    syllabus_path: Path | None = None,
    mock: bool = False,
    model: str | None = None,
    only: list[str] | None = None,
    limit: int | None = None,
    out_json_dir: Path | None = None,
    out_md_dirs: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """Batch-tag all q*.txt drafts; write JSON sidecars and/or Markdown exports."""
    draft_dir = Path(draft_dir)
    if not draft_dir.is_dir():
        raise FileNotFoundError(f"Draft directory not found: {draft_dir}")

    meta = paper_meta or infer_paper_meta_from_name(draft_dir.name)
    if paper_meta_overrides:
        for key, value in paper_meta_overrides.items():
            if hasattr(meta, key) and value is not None:
                setattr(meta, key, value)

    ms_key = _load_ms_key(draft_dir)
    index = _load_index(draft_dir)
    results: list[dict[str, Any]] = []

    json_dir = out_json_dir or (draft_dir / "tagged")
    json_dir.mkdir(parents=True, exist_ok=True)
    md_dirs = out_md_dirs or []

    for question, path in iter_draft_questions(draft_dir, only=only, limit=limit):
        text = path.read_text(encoding="utf-8")
        idx = index.get(question, {})
        qtype = idx.get("paper_style") or "mcq"
        if qtype not in ALLOWED_QUESTION_TYPES:
            qtype = "mcq"
        record = tag_question_text(
            text,
            paper_meta=meta,
            question=question,
            page_hint=idx.get("page_hint"),
            ms_answer=ms_key.get(question) or idx.get("ms_answer"),
            question_type_hint=qtype,
            as_only=as_only,
            syllabus_path=syllabus_path,
            mock=mock,
            model=model,
        )
        sidecar = json_dir / f"q{question}.json"
        sidecar.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for md_dir in md_dirs:
            write_question_markdown(record, Path(md_dir) / f"{record['id']}.md")
        results.append(record)

    summary_path = json_dir / "index.json"
    summary_path.write_text(
        json.dumps(
            [
                {
                    "id": r["id"],
                    "question": r["question"],
                    "syllabus_codes": r["syllabus_codes"],
                    "ms_answer": r.get("ms_answer"),
                    "file": f"q{r['question']}.json",
                }
                for r in results
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return results
