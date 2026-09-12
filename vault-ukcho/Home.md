---
title: UKChO Question Bank
record_type: vault-home
---

# UKChO Question Bank

Source-of-truth vault for UK Chemistry Olympiad questions.

## Structure

| Path | Purpose |
|------|---------|
| `questions/ukcho-<year>-q<n>.md` | Parent question (context, marks, themes, sub-question index) |
| `questions/ukcho-<year>-q<n><part>.md` | One record per **sub-question**, tagged independently |
| `assets/` | Paper / mark-scheme images (optional) |

## Tagging model

Each sub-question carries five layers plus prerequisites:

1. **AS Anchor** — `primary_as_anchor` + `secondary_as_anchors`
2. **UKChO Extension Topic** — `extension_topics`
3. **Skill** — `primary_skill` + `secondary_skills`
4. **Difficulty** — `difficulty_level` (Foundation / Standard / Challenge) + `difficulty_reason`
5. **Question Features** — `question_features`
6. **Prerequisites** — `prerequisites` + `requires_extension_knowledge`

AI-generated tags always land as `tag_status: suggested` / `tag_source: ai` with
`review_required` where uncertain, so a teacher can accept, edit, add or remove
them. Nothing is locked.

Taxonomy lives in `src/chembank/ukcho.py`; open `quiz-app/ukcho-tag.html` (built
into `quiz-app/site/`) to review and edit tags in the browser.
