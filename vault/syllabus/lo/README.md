---
tags: [syllabus, learning-outcome, index]
aliases: [LO index, learning outcomes]
---

# Learning outcome hubs

CIE 9701 LO notes live here as `syllabus/lo/<id>.md` (e.g. [[syllabus/lo/1.1-1|LO 1.1-1]]).

**How to find an LO in Obsidian**

1. Quick Switcher (`Cmd/Ctrl+O`) → type `1.1-1` or `LO 1.1-1` (each hub has aliases)
2. Browse this folder — every AS LO has a note with `# LO …` + full official text
3. Dataview on the hub (or below) — do **not** rely on vault search of bare ids that only sit in question YAML

## Id scheme

| Pattern | Example | Meaning |
|---------|---------|---------|
| `{subtopic}-{n}` | `3.1-1` | Numbered LO under subtopic 3.1 |
| `{subtopic}-{n}{letter}` | `2.4-1a` | Lettered part (a)(b)… under a numbered LO |

Parent topic code is always the subtopic (`3.1`, `2.4`). Questions keep both:

- `syllabus_codes: [3.1]`
- `learning_outcomes: [3.1-1]`

## Example LOs (topic 1.1)

- [[syllabus/lo/1.1-1|LO 1.1-1]] — nucleus / empty space *(no tagged questions yet)*
- [[syllabus/lo/1.1-2|LO 1.1-2]] — relative charges & masses *(no tagged questions yet)*
- [[syllabus/lo/1.1-6|LO 1.1-6]] — count p/n/e *(has tagged questions)*
- [[syllabus/lo/1.1-7|LO 1.1-7]] — atomic/ionic radius trends *(has tagged questions)*

## Dataview — questions by LO

```dataview
TABLE ms_answer, syllabus_codes, year, paper, question
FROM "questions"
WHERE contains(learning_outcomes, "3.1-1")
SORT year ASC, paper ASC, question ASC
```

## CLI

```bash
chembank los --code 1.1
chembank export-lo-hubs --vault vault          # regenerate all AS LO hubs
chembank codes --lo --as-only | wc -l
```
