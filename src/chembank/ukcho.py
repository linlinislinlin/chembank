"""UK Chemistry Olympiad (UKChO) question tagging taxonomy + helpers.

This module is the single source of truth for the UKChO tagging system. It is
deliberately *separate* from the CIE 9701 / 0620 syllabus code machinery:

* CIE questions are anchored to ``syllabus_codes`` + ``learning_outcomes``.
* UKChO questions are anchored to an **AS Anchor** (which Cambridge AS topic the
  student should already have studied) plus a flexible **UKChO Extension Topic**
  taxonomy, skills, difficulty and question features.

Nothing here talks to an external LLM API. ``build_tagging_request`` produces the
prompt/JSON bundle you can paste into any capable model, and
``apply_ai_tags`` merges the model's structured response back into a record while
keeping the tags explicitly marked as *suggested* so a teacher can accept, edit
or remove them.

Design rules baked into the validator (see ``validate_question``):

* A sub-question (``record_type == "ukcho-subquestion"``) is validated on its own
  tags — it never inherits the parent's tags.
* At most 1 primary AS anchor, 0-2 secondary anchors.
* At most 3 extension topics, 1 primary skill, 0-3 secondary skills.
* Unknown extension topics are a *warning*, not an error (the taxonomy is
  flexible / extensible by teachers).
* A record may be uncertain; in that case ``review_required: true`` is expected
  instead of invented certainty.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
#: Frontmatter plus the newline that terminates the closing delimiter, so the
#: remainder is the body exactly as it will be written back.
_FRONTMATTER_BLOCK_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


def split_body(text: str) -> str:
    """Everything after the frontmatter block, ready to be re-appended verbatim.

    Round-tripping must not grow the file, so this consumes the closing delimiter's
    own newline: ``"---\\nfm\\n---\\n\\n# H"`` -> ``"\\n# H"``.
    """
    m = _FRONTMATTER_BLOCK_RE.match(text)
    return text[m.end():] if m else text


# ---------------------------------------------------------------------------
# 1. AS Anchor — which Cambridge AS Chemistry topic must already be studied
# ---------------------------------------------------------------------------

AS_ANCHORS: tuple[str, ...] = (
    "Atomic Structure",
    "Stoichiometry",
    "Chemical Bonding",
    "States of Matter",
    "Energetics",
    "Electrochemistry",
    "Equilibria",
    "Kinetics",
    "Periodicity",
    "Group 2",
    "Group 17",
    "Nitrogen and Sulfur",
    "Introduction to Organic Chemistry",
    "Hydrocarbons",
    "Halogen Compounds",
    "Hydroxy Compounds",
    "Carbonyl Compounds",
    "Carboxylic Acids and Derivatives",
    "Nitrogen Compounds",
    "Polymerisation",
    "Organic Synthesis",
    "Analytical Techniques",
)

# ---------------------------------------------------------------------------
# 2. UKChO Extension Topic — the advanced / Olympiad chemistry actually tested
# ---------------------------------------------------------------------------

EXTENSION_TOPIC_GROUPS: dict[str, tuple[str, ...]] = {
    "Atomic / Bonding": (
        "Molecular Orbital Theory",
        "Bonding Molecular Orbitals",
        "Antibonding Molecular Orbitals",
        "Bond Order",
        "Paramagnetism",
        "Formal Charge",
        "Resonance",
        "Delocalisation",
        "Unusual VSEPR",
        "Sigma and Pi Bonding",
        "Hybridisation",
        "Bond Length and Bond Strength",
    ),
    "Solid State": (
        "Unit Cells",
        "Simple Cubic",
        "Body-Centred Cubic",
        "Face-Centred Cubic",
        "Coordination Number",
        "Crystal Packing",
        "Crystal Density",
        "Lattice Dimensions",
    ),
    "Equilibrium": (
        "Acid-Base Equilibria",
        "Ka",
        "pKa",
        "Buffers",
        "Ksp",
        "Solubility Equilibria",
        "Coupled Equilibria",
        "Multiple Equilibria",
    ),
    "Kinetics": (
        "Rate Equation",
        "Reaction Order",
        "Initial Rates",
        "Half-Life",
        "Mechanism from Rate Law",
        "Arrhenius Reasoning",
    ),
    "Organic": (
        "SN1",
        "SN2",
        "Elimination",
        "Electrophilic Addition",
        "Nucleophilic Addition",
        "Nucleophilic Acyl Substitution",
        "Aldol Chemistry",
        "Carbonyl Chemistry",
        "Retrosynthesis",
        "Multi-Step Synthesis",
        "Reaction Pathways",
        "Selectivity",
        "Unknown Reagent Deduction",
        "Protecting Group Logic",
    ),
    "Analytical": (
        "Mass Spectrometry",
        "Fragmentation",
        "IR Spectroscopy",
        "1H NMR",
        "Structure Deduction",
        "Combined Spectroscopy",
        "UV-Vis",
        "Raman Spectroscopy",
        "Chromatography",
    ),
    "Thermodynamics": (
        "Lattice Enthalpy",
        "Born-Haber Cycle",
        "Entropy",
        "Gibbs Free Energy",
        "Thermodynamic Feasibility",
    ),
    "Transition Metals": (
        "Ligand Field Theory",
        "Crystal Field Splitting",
        "Complex Ions",
        "Colour of Complexes",
        "Catalysis",
    ),
    "Redox / Electrochemistry": (
        "Standard Electrode Potential",
        "Cell Potential Reasoning",
        "Nernst Equation",
        "Disproportionation",
    ),
}

EXTENSION_TOPICS: tuple[str, ...] = tuple(
    topic for topics in EXTENSION_TOPIC_GROUPS.values() for topic in topics
)

# ---------------------------------------------------------------------------
# 3. Skill tags
# ---------------------------------------------------------------------------

SKILLS: tuple[str, ...] = (
    "Recall",
    "Apply",
    "Deduce",
    "Calculate",
    "Interpret Data",
    "Explain",
    "Draw / Represent",
    "Multi-step Reasoning",
    "Spatial Reasoning",
    "Structure Deduction",
    "Mechanism",
    "Experimental Reasoning",
)

# ---------------------------------------------------------------------------
# 4. Difficulty
# ---------------------------------------------------------------------------

DIFFICULTY_LEVELS: tuple[str, ...] = ("Foundation", "Standard", "Challenge")

DIFFICULTY_DESCRIPTIONS: dict[str, str] = {
    "Foundation": "About 1-2 reasoning steps; limited unfamiliar chemistry; good UKChO on-ramp.",
    "Standard": "Typical UKChO: unfamiliar context, self-extraction of data, ~3-5 steps, may combine topics.",
    "Challenge": "Long information-rich problem; multiple concepts, unfamiliar equations, later parts depend on earlier deductions.",
}

# ---------------------------------------------------------------------------
# 5. Question features (nature of the question, not chemistry topics)
# ---------------------------------------------------------------------------

QUESTION_FEATURES: tuple[str, ...] = (
    "Unfamiliar Context",
    "Data-heavy",
    "Calculation-heavy",
    "Long Reading",
    "Multi-step",
    "Cross-topic",
    "Diagram",
    "Graph",
    "Experimental",
    "Organic Mechanism",
    "Structure Deduction",
    "Spatial Reasoning",
    "Information Provided in Question",
    "No Prior Knowledge Required Beyond Prerequisites",
)

# ---------------------------------------------------------------------------
# 6. Prerequisites (seed list; teachers may add free-text extras)
# ---------------------------------------------------------------------------

PREREQUISITE_SEEDS: tuple[str, ...] = (
    "Atomic orbitals",
    "Electron configuration",
    "Hund's rule",
    "Sigma and Pi bonding",
    "Equilibrium constant expression",
    "Mole calculations",
    "Algebra",
    "Logarithms",
    "Functional groups",
    "Reaction conditions",
    "Curly arrows",
    "Nucleophile and electrophile",
    "Relevant AS organic reactions",
    "Density",
    "Solid structure",
    "Reagents and conditions",
)

# ---------------------------------------------------------------------------
# 7. Workflow enums
# ---------------------------------------------------------------------------

RECORD_TYPES: tuple[str, ...] = ("ukcho-parent", "ukcho-subquestion")

# How trustworthy the tags currently are. AI tags are NEVER locked.
TAG_STATUSES: tuple[str, ...] = (
    "unset",
    "suggested",
    "accepted",
    "edited",
    "teacher",
)

TAG_SOURCES: tuple[str, ...] = ("none", "ai", "teacher", "imported")


def is_teacher_authored(rec: dict[str, Any]) -> bool:
    """True when a teacher has reviewed this record.

    Re-ingesting a paper must never overwrite a teacher's judgement, so the ingest
    step asks this before refreshing a record from the tagging sheet. ``tag_source``
    is the primary signal (the workspace sets it to ``"teacher"`` on any edit or
    accept); ``tag_status`` is also checked so a record hand-edited in Obsidian and
    only re-stamped as accepted/edited is still treated as reviewed.
    """
    if str(rec.get("tag_source") or "") == "teacher":
        return True
    return str(rec.get("tag_status") or "") in ("teacher", "accepted", "edited")


# Fields a teacher can inspect / edit on every sub-question.
EDITABLE_TAG_FIELDS: tuple[str, ...] = (
    "primary_as_anchor",
    "secondary_as_anchors",
    "extension_topics",
    "primary_skill",
    "secondary_skills",
    "difficulty_level",
    "difficulty_reason",
    "question_features",
    "prerequisites",
    "requires_extension_knowledge",
    "teacher_notes",
)

# Maps the camelCase keys an AI returns to our snake_case record keys.
AI_KEY_MAP: dict[str, str] = {
    "primaryASAnchor": "primary_as_anchor",
    "secondaryASAnchors": "secondary_as_anchors",
    "extensionTopics": "extension_topics",
    "primarySkill": "primary_skill",
    "secondarySkills": "secondary_skills",
    "difficultyLevel": "difficulty_level",
    "difficultyReason": "difficulty_reason",
    "questionFeatures": "question_features",
    "prerequisites": "prerequisites",
    "requiresExtensionKnowledge": "requires_extension_knowledge",
    "teacherNotes": "teacher_notes",
    "reviewRequired": "review_required",
    "tagStatus": "tag_status",
}

MAX_SECONDARY_AS_ANCHORS = 2
MAX_EXTENSION_TOPICS = 3
MAX_SECONDARY_SKILLS = 3


def taxonomy() -> dict[str, Any]:
    """Return the whole taxonomy as a JSON-serialisable dict (for the web UI)."""
    return {
        "asAnchors": list(AS_ANCHORS),
        "extensionTopicGroups": {
            group: list(topics) for group, topics in EXTENSION_TOPIC_GROUPS.items()
        },
        "extensionTopics": list(EXTENSION_TOPICS),
        "skills": list(SKILLS),
        "difficultyLevels": list(DIFFICULTY_LEVELS),
        "difficultyDescriptions": dict(DIFFICULTY_DESCRIPTIONS),
        "questionFeatures": list(QUESTION_FEATURES),
        "prerequisiteSeeds": list(PREREQUISITE_SEEDS),
        "recordTypes": list(RECORD_TYPES),
        "tagStatuses": list(TAG_STATUSES),
        "tagSources": list(TAG_SOURCES),
        "editableTagFields": list(EDITABLE_TAG_FIELDS),
    }


# ---------------------------------------------------------------------------
# Parsing / serialising
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from an Obsidian markdown file."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def normalize_record(raw: dict[str, Any], fallback_id: str = "") -> dict[str, Any]:
    """Normalise a parsed frontmatter dict into the canonical UKChO shape.

    This is tolerant: missing optional fields become sane defaults so the teacher
    UI can render a partially-tagged question.
    """
    rec: dict[str, Any] = dict(raw)
    rec["id"] = str(raw.get("id") or fallback_id)
    rec["record_type"] = str(raw.get("record_type") or "ukcho-subquestion")
    rec["source"] = str(raw.get("source") or "UKChO")
    rec["year"] = raw.get("year")
    rec["question_number"] = raw.get("question_number")
    rec["sub_question"] = raw.get("sub_question")
    rec["parent_question_id"] = raw.get("parent_question_id")

    if rec["record_type"] == "ukcho-parent":
        rec.setdefault("title", "")
        rec["total_marks"] = raw.get("total_marks")
        rec["overall_themes"] = _as_list(raw.get("overall_themes"))
        rec["sub_question_ids"] = _as_list(raw.get("sub_question_ids"))
        return rec

    rec["primary_as_anchor"] = str(raw.get("primary_as_anchor") or "")
    rec["secondary_as_anchors"] = _as_list(raw.get("secondary_as_anchors"))
    rec["extension_topics"] = _as_list(raw.get("extension_topics"))
    rec["primary_skill"] = str(raw.get("primary_skill") or "")
    rec["secondary_skills"] = _as_list(raw.get("secondary_skills"))
    rec["difficulty_level"] = str(raw.get("difficulty_level") or "")
    rec["difficulty_reason"] = str(raw.get("difficulty_reason") or "")
    rec["question_features"] = _as_list(raw.get("question_features"))
    rec["prerequisites"] = _as_list(raw.get("prerequisites"))
    rec["requires_extension_knowledge"] = bool(raw.get("requires_extension_knowledge", False))
    rec["marks"] = raw.get("marks")
    rec["figures"] = _as_list(raw.get("figures"))
    rec["question_text"] = str(raw.get("question_text") or "")
    rec["answer"] = str(raw.get("answer") or "")
    rec["mark_scheme"] = str(raw.get("mark_scheme") or "")
    rec["teacher_notes"] = str(raw.get("teacher_notes") or "")
    rec["tag_status"] = str(raw.get("tag_status") or "unset")
    rec["tag_source"] = str(raw.get("tag_source") or "none")
    rec["review_required"] = bool(raw.get("review_required", False))
    rec["year_tags"] = _as_list(raw.get("year_tags"))
    return rec


def load_ukcho_questions(questions_dir: Path) -> list[dict[str, Any]]:
    """Load every UKChO markdown record under ``questions_dir``."""
    records: list[dict[str, Any]] = []
    if not Path(questions_dir).is_dir():
        return records
    for md_path in sorted(Path(questions_dir).glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        if not fm:
            continue
        records.append(normalize_record(fm, fallback_id=md_path.stem))
    return records


def to_frontmatter(rec: dict[str, Any]) -> str:
    """Serialise a record back to YAML frontmatter (teacher edits -> vault)."""
    return "---\n" + yaml.safe_dump(rec, allow_unicode=True, sort_keys=False) + "---\n"


def _ordered_keys(rec: dict[str, Any]) -> list[str]:
    """Stable, readable key order for exports."""
    if rec.get("record_type") == "ukcho-parent":
        return [
            "id", "record_type", "source", "year", "question_number", "title",
            "total_marks", "overall_themes", "sub_question_ids", "stems",
            "source_qp", "source_ms", "mock",
        ]
    return [
        "id", "record_type", "source", "year", "question_number", "sub_question",
        "parent_question_id", "marks", "primary_as_anchor", "secondary_as_anchors",
        "extension_topics", "primary_skill", "secondary_skills", "difficulty_level",
        "difficulty_reason", "question_features", "prerequisites",
        "requires_extension_knowledge", "tag_status", "tag_source",
        "review_required", "figures", "source_qp", "source_ms", "question_text",
        "answer", "mark_scheme", "teacher_notes", "year_tags", "mock",
    ]


def to_ordered_dict(rec: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in _ordered_keys(rec):
        if key in rec and rec[key] not in (None, "", [], {}):
            ordered[key] = rec[key]
    for key, value in rec.items():
        if key not in ordered and value not in (None, "", [], {}):
            ordered[key] = value
    return ordered


# ---------------------------------------------------------------------------
# Validation — hard errors vs soft warnings
# ---------------------------------------------------------------------------


def validate_question(rec: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for one record.

    Hard errors break the controlled contract; warnings are review prompts.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not rec.get("id"):
        errors.append("missing id")
    if rec.get("source") != "UKChO":
        errors.append(f"source must be 'UKChO' (got {rec.get('source')!r})")

    record_type = rec.get("record_type")
    if record_type not in RECORD_TYPES:
        errors.append(f"record_type must be one of {RECORD_TYPES} (got {record_type!r})")
        return errors, warnings

    if record_type == "ukcho-parent":
        if rec.get("question_number") in (None, ""):
            errors.append("parent is missing question_number")
        if rec.get("year") in (None, ""):
            errors.append("parent is missing year")
        return errors, warnings

    # ---- sub-question contract ------------------------------------------
    primary = rec.get("primary_as_anchor") or ""
    if not primary:
        errors.append("missing primary_as_anchor")
    elif primary not in AS_ANCHORS:
        errors.append(f"primary_as_anchor not in controlled list: {primary!r}")

    secondaries = rec.get("secondary_as_anchors") or []
    for anchor in secondaries:
        if anchor not in AS_ANCHORS:
            errors.append(f"secondary_as_anchor not in controlled list: {anchor!r}")
        if anchor == primary:
            warnings.append(f"secondary_as_anchor duplicates the primary: {anchor!r}")
    if len(secondaries) > MAX_SECONDARY_AS_ANCHORS:
        warnings.append(
            f"{len(secondaries)} secondary AS anchors (guideline: <= {MAX_SECONDARY_AS_ANCHORS})"
        )

    extensions = rec.get("extension_topics") or []
    for topic in extensions:
        if topic not in EXTENSION_TOPICS:
            warnings.append(f"extension topic outside the starter taxonomy: {topic!r}")
    if len(extensions) > MAX_EXTENSION_TOPICS:
        warnings.append(
            f"{len(extensions)} extension topics (guideline: <= {MAX_EXTENSION_TOPICS})"
        )
    if (
        extensions
        and not rec.get("requires_extension_knowledge")
        and not rec.get("review_required")
    ):
        warnings.append(
            "extension_topics present but requires_extension_knowledge is false — confirm"
        )

    skill = rec.get("primary_skill") or ""
    if not skill:
        errors.append("missing primary_skill")
    elif skill not in SKILLS:
        errors.append(f"primary_skill not in controlled list: {skill!r}")

    secondary_skills = rec.get("secondary_skills") or []
    for s in secondary_skills:
        if s not in SKILLS:
            errors.append(f"secondary_skill not in controlled list: {s!r}")
        if s == skill:
            warnings.append(f"secondary_skill duplicates the primary: {s!r}")
    if len(secondary_skills) > MAX_SECONDARY_SKILLS:
        warnings.append(
            f"{len(secondary_skills)} secondary skills (guideline: <= {MAX_SECONDARY_SKILLS})"
        )

    difficulty = rec.get("difficulty_level") or ""
    if not difficulty:
        errors.append("missing difficulty_level")
    elif difficulty not in DIFFICULTY_LEVELS:
        errors.append(f"difficulty_level not in {DIFFICULTY_LEVELS} (got {difficulty!r})")
    elif not rec.get("difficulty_reason"):
        warnings.append("difficulty_level set without difficulty_reason")

    features = rec.get("question_features") or []
    for feature in features:
        if feature not in QUESTION_FEATURES:
            errors.append(f"question_feature not in controlled list: {feature!r}")

    if not rec.get("prerequisites"):
        warnings.append("no prerequisites listed (guideline: list when possible)")

    if not rec.get("question_text"):
        warnings.append("missing question_text")

    tag_status = rec.get("tag_status") or "unset"
    if tag_status not in TAG_STATUSES:
        errors.append(f"tag_status must be one of {TAG_STATUSES} (got {tag_status!r})")
    elif tag_status == "suggested" and (rec.get("tag_source") or "none") == "none":
        warnings.append("tag_status is 'suggested' but tag_source is missing (who suggested it?)")

    # 'suggested' is the normal AI workflow state and is surfaced as a badge in
    # the teacher UI — it is not itself a problem. 'review_required' is the flag
    # for genuine AI uncertainty, and it should not be set once a teacher owns
    # the tags.
    if rec.get("review_required") and tag_status in ("accepted", "teacher"):
        warnings.append("review_required is still true but tag_status says a teacher accepted the tags")

    if rec.get("year") in (None, ""):
        warnings.append("missing year")
    if rec.get("sub_question") in (None, ""):
        warnings.append("missing sub_question label")

    return errors, warnings


def validate_all(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a whole vault; returns a report dict."""
    report: dict[str, Any] = {"count": 0, "ok": 0, "errors": {}, "warnings": {}}
    for rec in records:
        if rec.get("record_type") == "ukcho-parent":
            continue
        report["count"] += 1
        errors, warnings = validate_question(rec)
        if errors:
            report["errors"][rec.get("id", "?")] = errors
        else:
            report["ok"] += 1
        if warnings:
            report["warnings"][rec.get("id", "?")] = warnings
    return report


# ---------------------------------------------------------------------------
# Display labels
# ---------------------------------------------------------------------------

def question_label(rec: dict[str, Any]) -> str:
    """Human label for a question or sub-question, e.g. ``Q3``, ``Q3(b)``, ``Q3(b)(i)``.

    ``sub_question`` is stored compactly ("b", "b-i") because it is derived from
    the extract's part key, but a paper writes nested brackets — so "b-i" must
    render as ``Q3(b)(i)``, never ``Q3(b-i)``. This is the single source of truth
    for every place a record is shown (site, teacher workspace, tagging prompt).
    """
    qn = rec.get("question_number")
    sub = str(rec.get("sub_question") or "").strip()
    if not sub:
        return f"Q{qn}"
    part, _, roman = sub.partition("-")
    return f"Q{qn}({part})" + (f"({roman})" if roman else "")


def full_label(rec: dict[str, Any]) -> str:
    """``UKChO 2025 Q3(b)(i)`` — the label used when a model reads a question."""
    year = rec.get("year")
    return (f"UKChO {year} " if year else "") + question_label(rec)


# ---------------------------------------------------------------------------
# AI tagging workflow (no external API calls)
# ---------------------------------------------------------------------------

TAGGING_INSTRUCTIONS = """\
You are tagging a UK Chemistry Olympiad (UKChO) question for a teaching question bank.

Tag the ACTUAL chemical reasoning required, not keywords. Separate the story/context
of the question from the chemistry being tested. Do NOT mark information that is
explicitly provided inside the question as prerequisite knowledge.

Rules:
1. One primary_as_anchor (which Cambridge AS Chemistry topic the student must already
   have studied). Add 0-2 secondary_as_anchors only if genuinely cross-topic.
2. 0-3 extension_topics from the controlled taxonomy. Omit if the question only uses
   standard AS knowledge in an Olympiad context.
3. Exactly one primary_skill, plus 0-3 secondary_skills.
4. Exactly one difficulty_level: Foundation | Standard | Challenge, with a one-sentence
   difficulty_reason explaining WHY.
5. relevant question_features (nature of the question, not chemistry).
6. Concise prerequisites (knowledge the student must already have). If the question
   supplies unfamiliar chemistry in the stem, tag "Information Provided in Question"
   and set requires_extension_knowledge appropriately instead of listing it as a prereq.
7. Prefer the smallest accurate set of tags. If uncertain, set review_required to true
   rather than inventing certainty.

Return ONLY a JSON object with these keys:
  primaryASAnchor, secondaryASAnchors, extensionTopics, primarySkill, secondarySkills,
  difficultyLevel, difficultyReason, questionFeatures, prerequisites,
  requiresExtensionKnowledge, reviewRequired

Controlled taxonomy (choose only from these lists):
"""


def build_tagging_request(rec: dict[str, Any]) -> dict[str, Any]:
    """Build a self-contained prompt bundle to hand to any capable model.

    Returns a dict with ``system`` (instructions + taxonomy) and ``user`` (the
    question) plus the raw taxonomy for tooling.
    """
    tax = taxonomy()
    system = TAGGING_INSTRUCTIONS + json.dumps(
        {
            "asAnchors": tax["asAnchors"],
            "extensionTopics": tax["extensionTopics"],
            "skills": tax["skills"],
            "difficultyLevels": tax["difficultyLevels"],
            "questionFeatures": tax["questionFeatures"],
        },
        ensure_ascii=False,
        indent=2,
    )
    user = (
        f"{full_label(rec)}\n"
        f"Marks: {rec.get('marks', '?')}\n\n"
        f"Question:\n{rec.get('question_text', '')}\n"
    )
    if rec.get("mark_scheme"):
        user += f"\nMark scheme:\n{rec['mark_scheme']}\n"
    return {"system": system, "user": user, "taxonomy": tax}


def apply_ai_tags(rec: dict[str, Any], ai_payload: dict[str, Any]) -> dict[str, Any]:
    """Merge an AI's structured response into a record as *suggested* tags.

    Accepts either camelCase (as returned by the model) or snake_case keys. The
    result is never locked: ``tag_status`` becomes ``suggested`` and
    ``tag_source`` becomes ``ai`` so the teacher UI can offer accept / edit /
    remove. Existing teacher-authored values are not silently destroyed — the
    caller decides whether to apply the returned dict.
    """
    updated = dict(rec)
    unknown: list[str] = []

    for key, value in ai_payload.items():
        target = AI_KEY_MAP.get(key, key)
        if target not in EDITABLE_TAG_FIELDS and target not in (
            "review_required",
            "tag_status",
            "tag_source",
        ):
            unknown.append(key)
            continue
        if target in ("secondary_as_anchors", "extension_topics",
                      "secondary_skills", "question_features", "prerequisites"):
            updated[target] = _as_list(value)
        elif target == "requires_extension_knowledge":
            updated[target] = bool(value)
        elif target == "review_required":
            updated[target] = bool(value)
        else:
            updated[target] = value

    # A model may answer with raw camelCase without a review flag: never treat
    # fresh AI output as settled.
    updated["tag_status"] = "suggested"
    updated["tag_source"] = "ai"
    if not updated.get("review_required"):
        errors, _warnings = validate_question(updated)
        if errors:
            updated["review_required"] = True
    if unknown:
        updated["_ai_unmapped_keys"] = unknown
    return updated


def difficulty_band_from_marks(marks: int | None) -> str:
    """Very rough fallback band. NOT a substitute for reading the question."""
    if not marks:
        return "Standard"
    if marks <= 2:
        return "Foundation"
    if marks <= 6:
        return "Standard"
    return "Challenge"
