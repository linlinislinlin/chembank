# Spot-check notes — `9701_s21_qp_11`

Against `syllabus/cie-9701-as-a-level-chemistry.yaml`. Path: `--mock` → human q1–q10 → this pass (q1–q40 sample, focus q1–q15 + later).

**Checked:** 40/40 stems+codes+`ms_answer` (all A–D, match `ms_key.json`).  
**OK:** 36 **Fixed this pass:** 4 (q13, q19, q23, q27)

## Prior human corrections (q1–q10) — still hold

| Q | Codes now | Note |
|---|-----------|------|
| 1 | `2.2` | OK — mole/Avogadro only |
| 2 | `1.3` | OK |
| 3 | `3.5` | OK — shape only |
| 4 | `5.2`, `5.1` | OK |
| 5 | `8.2` | OK — Boltzmann / T |
| 6 | `2.4` | OK — combustion mass/volume |
| 7 | `1.4` | OK — IE (not orbital steal) |
| 8 | `4.1` | OK — ideal gas |
| 9 | `6.1` | OK — ox. numbers |
| 10 | `8.1`, `12.1` | OK — heat exchanger / Haber |

## This pass — fixes applied

| Q | Before | After | Why |
|---|--------|-------|-----|
| 13 | `12.1`, `10.1`, `11.2` | `12.1`, `11.4` | NH₃ + Cl₂ is chlorine chemistry (`11.4`); Ca(OH)₂/CaO are reagents, not Group 2 trends (`10.1`) |
| 19 | `2.3`, `2.4`, `9.2` | `2.3`, `2.4` | Mass → formula ID only; Period 3 is option context, not chemical periodicity ask |
| 23 | `13.1`, `14.2` | `13.1` | Ask is molecular formula from structure; not alkene reactions |
| 27 | `18.1`, `2.2` | `18.1`, `16.1`, `2.2` | Citric acid tertiary OH also liberates H₂ with Na → need `16.1` |

Files updated: `draft/.../tagged/qN.json`, `questions/`, `vault/questions/` for those four only.

## Sample later Qs — OK (no change)

| Q | Codes | Verdict |
|---|-------|---------|
| 11 | `8.3`, `8.1` | OK — catalysts |
| 12 | `9.2`, `1.3` | OK — amphoteric oxide → Al; p-electron count |
| 14–16 | `10.1` / `10.1` / `11.3` | OK |
| 17 | `11.1`, `3.6` | OK — volatility + IMF |
| 18 | `12.1` | OK — acid rain / NO₂ |
| 20 | `15.1`, `19.2` | OK — SN2 + nitrile |
| 21–22 | `14.2` / `13.4` | OK |
| 24–26 | `18.2` / `16.1`+`17.1`+`6.1` / `22.1`+`13.1` | OK (`6.1` justified by e⁻ half-eq framing) |
| 28–30 | carbonyl/HCN; propene; synthesis | OK |
| 31–40 | equilibria/ester; ΔH profile; gas density; shapes; Period 3; Gp2; haloalkanes; iodoform; coloured products; ester uses | OK |

Borderline acceptable (not fixed): q25 keeps `6.1`; q28 keeps `13.4` (correct option is chirality); q39 multi-tags the three reaction families in statements.

## Recurring mis-tag patterns

1. **Stoichiometry over-breadth** — mole count as `2.4` when only `2.2`.
2. **Bonding keyword over-tag** — ionic/covalent context when ask is shape (`3.5`).
3. **Option-keyword steal** — distractor nouns override stem (`orbital`→`1.3`, `ammonia`→`12.1`, `equilibrium`→`7.x`).
4. **Mock fallback `1.1`** — no keyword → atomic radius; usually wrong.
5. **Reagent/context over-tag** — Group 2 / alkene codes from reagents or structure class when ask is N/S+Cl₂, formula, etc. (q13, q23).
6. **Missing co-functional group** — polyfunctional molecules (citric acid OH+COOH) need both `16.1` and `18.1` (q27).
7. **Prefer stem ask** — tag what is asked, not every chemical name that appears.

## Mock heuristic update (post-vault)

`src/chembank/tag.py` now **stem-first** matches (safer A/B/C/D split; avoids prose `A single…`) and narrows the patterns above. On `9701_s21_qp_11`, mock now set-matches human codes for **q1–q15 + q19/q23/q27** (and 26/40 overall).

**Still expected misses (later organic / multi-step):** q25–26, q28–33, q36–40 — synthesis maps, IR/`22.1`, multi-tag carbonyl/haloalkane chains. Do **not** re-export vault from `--mock` without diffing; human-corrected JSON remains canonical.

Fixtures: `tests/test_mock_tag.py`.
