#!/usr/bin/env python3
"""Generate English MCQ worked solutions for Chemical Energetics (5.1–5.4) and
Redox (6.1) homework, merging into quiz-app/question-worked-solutions.json.

Choice questions only (structured questions' mark scheme already serves as the solution).
Every `answer` is verified against the question bank ms_answer before writing.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "quiz-app" / "question-worked-solutions.json"

S = {}

# ============ 5.1 Enthalpy change (HW id 27) ============
S["cie-9701-2024-on-p13-q10"] = {
  "answer": "A",
  "solution": "1  H⁺ + OH⁻ → H₂O is neutralisation — always exothermic (ΔH negative).\n2  CH₄ + 2O₂ → CO₂ + 2H₂O is combustion — always exothermic (ΔH negative).\n3  NH₃(g) → NH₃(l) is condensation (gas → liquid) — releases energy, so ΔH negative.\nAll three are exothermic, so none has a positive enthalpy change.\n→ A"
}
S["cie-9701-2023-on-p13-q9"] = {
  "answer": "D",
  "solution": "Enthalpy changes of neutralisation are ALWAYS negative (acid + base reactions are always exothermic).\nThe other statements are false: reactions can be endothermic (ΔH positive), combustion is always exothermic, and formation can be either exothermic or endothermic.\n→ D"
}
S["cie-9701-2021-on-p12-q34"] = {
  "answer": "C",
  "solution": "N₂F₄ decomposes into NF₂ radicals: N₂F₄ → 2NF₂. Only the weak N–N bond (≈ +160 kJ mol⁻¹) breaks.\n1  FALSE — N–F bonds are NOT broken; only the N–N bond breaks.\n2  TRUE — the N–N bond in N₂F₄ is unusually weak, so ΔH ≈ +160 kJ mol⁻¹.\n3  TRUE — NF₂ is bent (non-linear), like water.\n→ 2 and 3 only → C"
}
S["cie-9701-2021-mj-p11-q32"] = {
  "answer": "A",
  "solution": "The incomplete profile shows products HIGHER than reactants → the reaction is endothermic.\n1  CaCO₃ → CaO + CO₂ is thermal decomposition (endothermic) ✓\n2  H₂(g) → 2H(g) breaks the H–H bond (endothermic) ✓\n3  Cl⁻(aq) → Cl⁻(g) + aq is the reverse of hydration (endothermic) ✓\nAll three reactions are endothermic.\n→ 1, 2 and 3 → A"
}
S["cie-9701-2021-on-p11-q8"] = {
  "answer": "C",
  "solution": "Enthalpy change of atomisation = formation of ONE mole of gaseous atoms from the element in its standard state.\nIodine's standard state is I₂(s), so atomisation is:\n½I₂(s) → I(g)   (one mole of I atoms).\n→ C"
}
S["cie-9701-2024-mj-p11-q10"] = {
  "answer": "B",
  "solution": "The reaction is endothermic, so products sit ABOVE reactants (ΔH positive).\nEa = 2 × ΔH means the peak is 2ΔH above the reactants, and the products are ΔH above the reactants (i.e. the peak is ΔH above the products).\nThe correct diagram shows reactants lowest, products at ΔH above them, and the peak at 2ΔH above reactants.\n→ B"
}
S["cie-9701-2022-on-p12-q9"] = {
  "answer": "A",
  "solution": "Read the pathway: products are at the lowest level, reactants at +50 kJ mol⁻¹, and the peak at +80 kJ mol⁻¹.\nThe reverse reaction climbs from products (0) up to the peak (80), so its activation energy = +80 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2025-mj-p12-q13"] = {
  "answer": "D",
  "solution": "ΔH = −61.5 kJ mol⁻¹, so the reaction is EXOTHERMIC: products (CO₂ + 4HCl) sit LOWER than reactants (CCl₄ + 2H₂O).\nThe activation energy is +62 kJ mol⁻¹, so the hump rises 62 above the reactants.\nOnly D has products below reactants with the correct Ea hump.\n→ D"
}
S["cie-9701-2023-on-p13-q15"] = {
  "answer": "D",
  "solution": "Forward reaction is exothermic (products lower than reactants).\nThe reverse reaction is therefore endothermic and must climb from the products up to the same peak, then back down to reactants.\nReverse Ea = forward Ea + |ΔH|, which is GREATER than the forward Ea of +30 kJ mol⁻¹.\n→ D"
}
S["cie-9701-2024-mj-p13-q10"] = {
  "answer": "C",
  "solution": "½N₂ + ½O₂ → NO has ΔH = +90 kJ mol⁻¹, so it is ENDOTHERMIC: products (NO) sit ABOVE reactants.\nThe activation energy Ea is measured from the reactants up to the peak, so Ea > 90.\nOnly the diagram with products higher than reactants (and Ea drawn from reactant level) is correct.\n→ C"
}
S["cie-9701-2023-on-p13-q10"] = {
  "answer": "D",
  "solution": "Standard enthalpy change of neutralisation = the enthalpy change when an aqueous acid and an aqueous alkali react to form ONE MOLE of water.\nThe key phrase is 'one mole of water'.\n→ D"
}
S["cie-9701-2024-on-p12-q9"] = {
  "answer": "B",
  "solution": "Enthalpy change of formation = formation of ONE mole of a compound from its ELEMENTS in their STANDARD states.\nA uses C(g) — carbon's standard state is C(s), not C(g).\nC and D start from compounds, not elements.\nB: ½N₂(g) + ½O₂(g) → NO(g) forms 1 mol of NO from elements in standard states.\n→ B"
}
S["cie-9701-2023-fm-p12-q10"] = {
  "answer": "D",
  "solution": "The standard enthalpy change of reaction refers to the equation AS WRITTEN (all substances in standard states).\nXeF₆ + 3H₂O → XeO₃ + 6HF produces six moles of HF.\nSo ΔH°r is the enthalpy change when six moles of hydrogen fluoride are produced (the reaction as written).\n→ D"
}
S["cie-9701-2023-mj-p13-q10"] = {
  "answer": "B",
  "solution": "Standard enthalpy change of formation of water = formation of ONE mole of liquid water from its elements in standard states:\nH₂(g) + ½O₂(g) → H₂O(l).\n→ B"
}
S["cie-9701-2025-mj-p11-q5"] = {
  "answer": "A",
  "solution": "2H₂(g) + O₂(g) → 2H₂O(l)\nΔH°r = ΣΔHf°(products) − ΣΔHf°(reactants) = 2ΔHf°(H₂O) − [0 + 0] = 2 × ΔHf°(H₂O).\n→ A"
}
S["cie-9701-2025-mj-p14-q13"] = {
  "answer": "D",
  "solution": "Formation of ethanol = one mole of liquid ethanol from its elements in standard states:\n2C(s) + 3H₂(g) + ½O₂(g) → C₂H₅OH(l).\nCarbon must be C(s), hydrogen H₂(g), oxygen O₂(g), and ethanol is a liquid at standard conditions.\n→ D"
}
S["cie-9701-2024-fm-p12-q10"] = {
  "answer": "C",
  "solution": "Formation of propane = one mole of gaseous propane from its elements in standard states:\n3C(s) + 4H₂(g) → C₃H₈(g).\nA and B use atomic C(g) or H(g), which are not standard states; D forms liquid propane.\n→ C"
}
S["cie-9701-2024-mj-p12-q10"] = {
  "answer": "C",
  "solution": "Formation of sodium oxide = one mole of Na₂O from its elements in standard states:\n2Na(s) + ½O₂(g) → Na₂O(s).\nOnly C forms exactly one mole of Na₂O from elemental sodium and oxygen.\n→ C"
}
S["cie-9701-2025-mj-p13-q12"] = {
  "answer": "B",
  "solution": "ΔH° is the STANDARD enthalpy change, so it is measured under standard conditions: 298 K AND 101 kPa (1 atm).\nA is wrong (298 °C instead of 298 K).\nC is wrong — the equation forms 2 mol NH₃, but a formation value is per 1 mol.\nD is wrong — 1 mol N₂ reacts with 3 mol H₂, not 1 mol.\n→ B"
}
S["cie-9701-2021-on-p12-q9"] = {
  "answer": "B",
  "solution": "The question asks for the DECOMPOSITION of ammonium chloride, which is the reverse of the given reaction:\nNH₄Cl(s) → NH₃(g) + HCl(g),  ΔH = +314 kJ mol⁻¹ (endothermic).\nSo products (NH₃ + HCl) sit HIGHER than the reactant (NH₄Cl), and ΔH is drawn upward.\n→ B"
}
S["cie-9701-2025-fm-p12-q15"] = {
  "answer": "C",
  "solution": "Exothermic means ΔH is negative — more energy is released making bonds than is absorbed breaking bonds.\nSo the total bond energy of the PRODUCTS is GREATER than that of the reactants, and ΔH is negative.\n→ C"
}
S["cie-9701-2025-on-p12-q10"] = {
  "answer": "D",
  "solution": "The heat pad gets HOTTER, so the reaction is EXOTHERMIC.\nIron reacts with oxygen (air) to form rust — iron is oxidised, i.e. iron LOSES electrons.\n→ D"
}

# ============ 5.2 Calorimetry (HW id 28) ============
S["cie-9701-2025-on-p12-q9"] = {
  "answer": "C",
  "solution": "Energy absorbed by the water = m c ΔT (not the mass of hydrocarbon).\n= 200 g × 4.18 J g⁻¹ K⁻¹ × (41.0 − 23.7) K = 200 × 4.18 × 17.3 J.\n→ C"
}
S["cie-9701-2025-mj-p11-q11"] = {
  "answer": "B",
  "solution": "n(H₂SO₄) = 0.050 dm³ × 1.0 = 0.050 mol → 0.10 mol H⁺.\nn(NaOH) = 0.100 dm³ × 1.0 = 0.100 mol → 0.10 mol OH⁻.\nSo 0.10 mol of water forms.\nq = (total volume) × c × ΔT = 150 cm³ × 4.2 × (29 − 20) = 5670 J.\nΔHneut = −5670 / 0.10 = −56 700 J mol⁻¹ = −56.7 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2024-mj-p13-q9"] = {
  "answer": "C",
  "solution": "Mass burned = 58.34 − 57.85 = 0.49 g.\nn = 0.49 / 74 = 6.62 × 10⁻³ mol.\nq = 175 g × 4.18 × (41.1 − 17.6) = 175 × 4.18 × 23.5 = 17 190 J.\nΔHc = −17 190 / 6.62 × 10⁻³ = −2.60 × 10⁶ J mol⁻¹ = −2600 kJ mol⁻¹ (3 s.f.).\n→ C"
}
S["cie-9701-2025-on-p14-q10"] = {
  "answer": "C",
  "solution": "0.04 mol HCl reacts with 0.04 mol NaOH, giving 0.04 mol water.\nTotal volume = 20 + 20 = 40 cm³.\nΔHneut = −(V × c × ΔT) / n = −(40 × 4.2 × 15) / 0.04 J mol⁻¹.\n→ C"
}
S["cie-9701-2023-mj-p12-q9"] = {
  "answer": "B",
  "solution": "n(HCl) = n(NaOH) = 0.0250 dm³ × 4.00 = 0.100 mol.\nTotal mass = 50.0 cm³ × 1.00 g cm⁻³ = 50.0 g.\nq = 50.0 × 4.18 × (30.0 − 15.0) = 3135 J.\nΔHneut = −3135 / 0.100 = −31 350 J mol⁻¹ ≈ −31.4 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2021-on-p11-q7"] = {
  "answer": "B",
  "solution": "Doubling BOTH volumes doubles the moles of water formed AND doubles the total mass of solution.\nEnergy released ∝ moles (×2), but heat capacity ∝ mass (×2), so ΔT = q/(mc) is unchanged.\nThe temperature rise stays 12 °C.\n→ B"
}

# ============ 5.3 Hess's law (HW id 29) ============
S["cie-9701-2021-mj-p11-q4"] = {
  "answer": "D",
  "solution": "CH₄ + 2O₂ → CO₂ + 2H₂O.\nΔHc(CH₄) = ΣΔHf(products) − ΣΔHf(reactants)\n= ΔHf(CO₂) + 2ΔHf(H₂O) − ΔHf(CH₄).\nHere ΔH₂ = ΔHc(C) = ΔHf(CO₂), ΔH₃ = ΔHc(H₂) = ΔHf(H₂O), ΔH₁ = ΔHf(CH₄).\nSo ΔHc = ΔH₂ + 2ΔH₃ − ΔH₁.\n→ D"
}
S["cie-9701-2021-mj-p13-q8"] = {
  "answer": "D",
  "solution": "In the cycle, X is the step from CH₄(g) to CO₂(g) + 2H₂O(l), i.e. the formation of TWO moles of water (plus CO₂).\nX corresponds to 2 × the enthalpy change of formation of water, 2ΔHf(H₂O).\n→ D"
}
S["cie-9701-2021-mj-p13-q7"] = {
  "answer": "A",
  "solution": "Use the cycle: ΔHsol = ΔHlatt(dissociation) + ΔHhyd(Cs⁺) + ΔHhyd(Br⁻).\nThe question's q is the reverse of lattice dissociation: q = −ΔHlatt(dissociation).\n+25.9 = ΔHlatt + (−276) + (−335) → ΔHlatt = +636.9 kJ mol⁻¹.\nSo q = −636.9 ≈ −637 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2021-fm-p12-q32"] = {
  "answer": "B",
  "solution": "In the combustion cycle, ΔHc(CH₄) is the 'elements → combustion products' arrow:\nΔHc(CH₄) = ΔHf(CO₂) + 2ΔHf(H₂O) = ΔHc(C) + 2ΔHc(H₂).\nStatement 1 (using ΔHf of the products) and statement 2 (using ΔHc of C and H₂) both give this correctly; statement 3 uses CO, which is not part of the cycle.\n→ 1 and 2 only → B"
}
S["cie-9701-2022-on-p12-q10"] = {
  "answer": "B",
  "solution": "For a pair of reverse reactions, the ENDOTHERMIC direction always has the HIGHER activation energy (Ea = Ea(reverse) + |ΔH|).\nW (ΔH −56) and X (ΔH +56): X is endothermic, so X > W.\nY (ΔH +11) and Z (ΔH −11): Y is endothermic, so Y > Z.\n→ B"
}
S["cie-9701-2022-mj-p11-q9"] = {
  "answer": "D",
  "solution": "2C(s) + 3H₂(g) + 3.5O₂(g) → 2CO₂(g) + 3H₂O(l).\nQ = ΣΔHf(products) − ΣΔHf(reactants) = 2ΔHf(CO₂) + 3ΔHf(H₂O) − 0.\n→ 3 × ΔHf[H₂O(l)] + 2 × ΔHf[CO₂(g)].\n→ D"
}
S["cie-9701-2022-mj-p11-q10"] = {
  "answer": "C",
  "solution": "The pathway shows 2NaOH + H₂SO₄ → Na₂SO₄ + 2H₂O, so TWO moles of water are formed.\nThe overall enthalpy change is (x − y), so per mole of water ΔHneut = (x − y)/2.\n→ C"
}
S["cie-9701-2024-mj-p11-q9"] = {
  "answer": "C",
  "solution": "In the cycle: CH₄ + 2O₂ → C + 2H₂ + 2O₂ is X (atomisation, endothermic → positive).\nY = −890 (combustion of CH₄, exothermic) and Z = −964 (combustion of C and H₂, exothermic).\nSo Y and Z are both negative, X is positive.\n→ C"
}
S["cie-9701-2022-mj-p13-q10"] = {
  "answer": "A",
  "solution": "MgCO₃ → MgO + CO₂.\nΔHr = ΣΔHf(products) − ΣΔHf(reactants)\n= [ΔHf(MgO) + ΔHf(CO₂)] − ΔHf(MgCO₃)\n= (−601.7 + (−393.5)) − (−1095.8) = −995.2 + 1095.8 = +100.6 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2022-on-p13-q9"] = {
  "answer": "C",
  "solution": "ΔHr = ΔHf(PCl₅) − ΔHf(PCl₃) − ΔHf(Cl₂).\nSince Cl₂ is an element, ΔHf(Cl₂) = 0, so ΔHr = ΔHf(PCl₅) − ΔHf(PCl₃) = −124 kJ mol⁻¹.\nSo ΔHf(PCl₅) is MORE negative than ΔHf(PCl₃), and the Cl₂ bond energy is NOT needed (Cl₂ is in its standard state).\n→ C"
}
S["cie-9701-2023-mj-p11-q5"] = {
  "answer": "B",
  "solution": "CaC₂(s) + H₂O(l) → CaO(s) + C₂H₂(g) is already balanced.\nΔHr = ΣΔHf(products) − ΣΔHf(reactants)\n= [(−635) + (+228)] − [(−60) + (−286)] = −407 − (−346) = −61 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2024-on-p12-q10"] = {
  "answer": "D",
  "solution": "3VCl₂ → 2VCl₃ + V.\nΔHr = ΣΔHf(products) − ΣΔHf(reactants)\n= [2(−573) + 0] − [3(−452)] = −1146 + 1356 = +210 kJ mol⁻¹.\n→ D"
}
S["cie-9701-2023-on-p12-q11"] = {
  "answer": "B",
  "solution": "Overall: 4NH₃ + 8O₂ → 4HNO₃ + 4H₂O.\nStage 1: −904; Stage 2 ×2 (for 4NO): −228; Stage 3: −348.\nTotal = −904 − 228 − 348 = −1480 kJ for 4 moles of HNO₃.\nPer mole (equation 1, ÷4) = −1480/4 = −370 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2025-mj-p13-q6"] = {
  "answer": "C",
  "solution": "4NH₃ + 5O₂ → 4NO + 6H₂O.\nΔHr = ΣΔHf(products) − ΣΔHf(reactants)\n= [4(+90.3) + 6(−241.8)] − [4(−46.1) + 0]\n= (361.2 − 1450.8) − (−184.4) = −1089.6 + 184.4 = −905.2 kJ mol⁻¹.\n→ C"
}
S["cie-9701-2022-mj-p12-q9"] = {
  "answer": "A",
  "solution": "2NO₂(g) → N₂O₄(g).\nΔHr = ΔHf(N₂O₄) − 2ΔHf(NO₂) = (+9.2) − 2(+33.2) = 9.2 − 66.4 = −57.2 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2022-on-p12-q16"] = {
  "answer": "A",
  "solution": "From CH₄ → C(g) + 4H(g), ΔH = +1648, so C–H = 1648/4 = 412 kJ mol⁻¹.\nC₂H₆ contains 1 C–C bond and 6 C–H bonds.\nForming C₂H₆ from atoms releases: 1(350) + 6(412) = 350 + 2472 = 2822 kJ mol⁻¹.\nΔH = −2822 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2022-fm-p12-q8"] = {
  "answer": "D",
  "solution": "Fermentation: C₆H₁₂O₆ → 2CO₂ + 2C₂H₅OH.\nUsing enthalpies of combustion (CO₂ is already the combustion product, ΔHc = 0):\nΔHr = ΣΔHc(reactants) − ΣΔHc(products) = a − 2b.\n→ D"
}
S["cie-9701-2024-on-p13-q9"] = {
  "answer": "B",
  "solution": "C₄H₁₀ + 6.5O₂ → 4CO₂ + 5H₂O.\nΔHc(C₄H₁₀) = ΣΔHc(elements) − ΔHf(butane)\n= 4(−394) + 5(−286) − (−129) = −1576 − 1430 + 129 = −2877 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2024-fm-p12-q9"] = {
  "answer": "B",
  "solution": "2C₂H₆ + 3O₂ → 2CH₄ + 2CO₂ + 2H₂O.\nBoth C₂H₆ and CH₄ burn to CO₂ + H₂O, so:\nΔHr = ΣΔHc(reactants) − ΣΔHc(products) = 2ΔHc(C₂H₆) − 2ΔHc(CH₄)\n(CO₂ and H₂O have ΔHc = 0).\n→ B"
}
S["cie-9701-2025-on-p14-q9"] = {
  "answer": "B",
  "solution": "P₄O₁₀(s) + 6H₂O(l) → 4H₃PO₄(s).\nΔHr = ΣΔHf(products) − ΣΔHf(reactants)\n= 4(−1279) − [(−3012) + 6(−286)] = −5116 − (−4728) = −388 kJ mol⁻¹.\n→ B"
}
S["cie-9701-2025-mj-p12-q6"] = {
  "answer": "A",
  "solution": "Formation of methanol: C + 2H₂ + ½O₂ → CH₃OH.\nΔHf(CH₃OH) = ΣΔHc(elements) − ΔHc(CH₃OH)\n= (−394) + 2(−286) − (−726) = −394 − 572 + 726 = −240 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2023-mj-p12-q10"] = {
  "answer": "D",
  "solution": "Step 1: 2NO + O₂ → 2NO₂, ΔH = 2ΔHf(NO₂) − 2ΔHf(NO) = 2(34) − 2(91) = −114 kJ mol⁻¹.\nStep 2: 2NO₂ → N₂O₄, ΔH = −58 kJ mol⁻¹.\nOverall: 2NO + O₂ → N₂O₄, ΔH = −114 − 58 = −172 kJ mol⁻¹.\n→ D"
}

# ============ 5.4 Bond energies (HW id 30) ============
S["cie-9701-2025-on-p11-q7"] = {
  "answer": "D",
  "solution": "55 kJ is RELEASED, so the reaction is exothermic.\nExothermic means more energy is GIVEN OUT making new bonds than is TAKEN IN breaking old bonds.\n→ D"
}
S["cie-9701-2025-mj-p14-q5"] = {
  "answer": "D",
  "solution": "S₈(s) + 8O₂(g) → 8SO₂(g), ΔHc = −2376 kJ mol⁻¹.\nS₈ has 8 S–S bonds (ring): S–S = 2232/8 = 279 kJ mol⁻¹. O=O = 496.\nBonds broken = 8(279) + 8(496) = 2232 + 3968 = 6200.\nBonds formed = 16 × (S=O) (two S=O per SO₂).\nΔHc = broken − formed = 6200 − 16(S=O) = −2376.\n16(S=O) = 8576 → S=O = 536 kJ mol⁻¹.\n→ D"
}
S["cie-9701-2022-mj-p13-q9"] = {
  "answer": "B",
  "solution": "The AVERAGE bond energy of C–H in methane = ¼ of the energy to break all four C–H bonds in one mole of CH₄:\n¼CH₄(g) → ¼C(g) + H(g).\nThis gives the energy of one C–H bond on average.\n→ B"
}
S["cie-9701-2023-fm-p12-q16"] = {
  "answer": "A",
  "solution": "1  TRUE — diatomic molecules have a single bond type, so their bond energy is an exact value (always positive).\n2  FALSE — the Group 7 bond energy trend is due to bond length/overlap, NOT id–id intermolecular forces.\n3  FALSE — the D–Cl bond energy is not in the table, so the D₂ + Cl₂ reaction cannot be calculated from these data alone.\n→ 1 only → A"
}
S["cie-9701-2021-mj-p12-q8"] = {
  "answer": "A",
  "solution": "N₂ + O₂ → 2NO, ΔH = +180 kJ mol⁻¹.\nBonds broken = N≡N (945) + O=O (498) = 1443.\nBonds formed = 2 × (N=O bond).\nΔH = broken − formed = 1443 − 2(N=O) = +180.\n2(N=O) = 1263 → N=O = 631.5 ≈ 630 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2023-mj-p13-q13"] = {
  "answer": "C",
  "solution": "H₂ + ½O₂ → H₂O(g) (one mole of hydrogen).\nBonds broken = 1(H–H) + ½(O=O) = 436 + 248 = 684.\nBonds formed = 2(O–H) = 2(463) = 926.\nΔH = 684 − 926 = −242 kJ mol⁻¹.\n→ C"
}
S["cie-9701-2024-mj-p12-q9"] = {
  "answer": "C",
  "solution": "C₂H₆ + 2F₂ → C₂H₄F₂ + 2HF, ΔH = −960 kJ mol⁻¹.\nBonds broken = 2(C–H) + 2(F–F) = 2(410) + 2(158) = 1136.\nBonds formed = 2(C–F) + 2(H–F) = 2(C–F) + 2(562) = 2(C–F) + 1124.\nΔH = broken − formed = 1136 − [2(C–F) + 1124] = −960.\n12 − 2(C–F) = −960 → 2(C–F) = 972 → C–F = 486 kJ mol⁻¹.\n→ C"
}
S["cie-9701-2025-mj-p12-q10"] = {
  "answer": "D",
  "solution": "1  FALSE — both ΔHvap and ΔHmelt are POSITIVE (endothermic).\n2  TRUE — vaporisation breaks all hydrogen bonds, melting breaks only some, so ΔHvap > ΔHmelt.\n3  TRUE — ice and water both have HYDROGEN bonding (same type).\n→ 2 and 3 only → D"
}
S["cie-9701-2021-fm-p12-q7"] = {
  "answer": "A",
  "solution": "Energy released = mass water × c × ΔT = W × 4.2 × Y (J).\nMoles of ethanol = X / Z.\nΔHc = −(W × 4.2 × Y) / (X/Z) = −(W × 4.2 × Y × Z)/X J mol⁻¹\n= −(4.2 × W × Y × Z)/(1000 × X) kJ mol⁻¹.\n→ A"
}
S["cie-9701-2025-on-p11-q8"] = {
  "answer": "B",
  "solution": "Energy absorbed by water = 200 × 4.2 × (66 − 18) = 200 × 4.2 × 48 = 40 320 J.\nThis is 45% of the total, so total = 40 320 / 0.45 = 89 600 J.\nPer gram of fuel = 89 600 / 1.60 = 56 000 J g⁻¹ = 56 kJ g⁻¹.\n→ B"
}
S["cie-9701-2025-fm-p12-q12"] = {
  "answer": "A",
  "solution": "n(NaOH) = 0.0250 dm³ × 0.100 = 0.00250 mol.\nTotal volume = 50.0 cm³; q = 50.0 × 4.18 × 2.50 = 522.5 J.\nΔH = −522.5 / 0.00250 = −209 000 J mol⁻¹ = −209 kJ mol⁻¹.\n→ A"
}
S["cie-9701-2023-mj-p13-q12"] = {
  "answer": "A",
  "solution": "n(HNO₃) = 0.020 × 4.00 = 0.080 mol; n(NaOH) = 0.030 × 2.00 = 0.060 mol.\nNaOH is limiting, so 0.060 mol of water forms.\nEnergy released = 0.060 × 57 000 = 3420 J.\n3420 = 50 × 4.2 × ΔT → ΔT = 3420/210 = 16.3 °C.\nFinal temperature = 25.0 + 16.3 = 41.3 °C.\n→ A"
}
S["cie-9701-2022-on-p13-q10"] = {
  "answer": "B",
  "solution": "n = 0.0250 dm³ × 0.350 = 0.00875 mol.\nTotal volume = 50.0 cm³; q = 50.0 × 4.2 × 2.5 = 525 J.\nΔH = −525 / 0.00875 = −60 000 J mol⁻¹ = −60 kJ mol⁻¹.\n→ B"
}

# ============ 6.1 Redox balancing (HW id 38) ============
S["as-redox-balancing-q01"] = {
  "answer": "D",
  "solution": "CO → CO₂: carbon goes from +2 to +4, so carbon is OXIDISED (oxidation number +2).\nNO → N₂: nitrogen goes from +2 to 0, so nitrogen is REDUCED (oxidation number −2).\n→ carbon +2, nitrogen −2 → D"
}
S["as-redox-balancing-q02"] = {
  "answer": "C",
  "solution": "(NH₄)₂Cr₂O₇ → N₂ + 4H₂O + Cr₂O₃.\nN goes from −3 to 0 → oxidised.\nCr goes from +6 to +3 → reduced.\n→ nitrogen oxidised, chromium reduced → C"
}
S["as-redox-balancing-q03"] = {
  "answer": "D",
  "solution": "ClO⁻ (chlorate(I)) acts as an OXIDISING agent, so it oxidises Fe²⁺.\nOxidation = loss of electrons: Fe²⁺ → Fe³⁺ + e⁻.\nSo iron(II) ions LOSE electrons to become iron(III) ions.\n→ D"
}
S["as-redox-balancing-q04"] = {
  "answer": "C",
  "solution": "2CuSO₄ + 4KI → 2CuI + I₂ + 2K₂SO₄.\nCu goes +2 → +1 (reduced), so copper ions act as OXIDISING agents.\nOnly HALF the iodide is oxidised to I₂ (the rest stays as I⁻ in CuI and K₂SO₄).\n→ all copper ions oxidising agents → C"
}
S["as-redox-balancing-q05"] = {
  "answer": "D",
  "solution": "wClO₃⁻ + xMnO₄⁻ + yH⁺ → wClO₄⁻ + xMnO₂ + zH₂O.\nCl: +5 → +7 (loses 2e⁻, ×3); Mn: +7 → +4 (gains 3e⁻, ×2).\nSo w = 3, x = 2. Balance H⁺: y = 2, z = 1.\n→ 3ClO₃⁻ + 2MnO₄⁻ + 2H⁺ → 3ClO₄⁻ + 2MnO₂ + H₂O (w=3, x=2, y=2) → D"
}
S["as-redox-balancing-q06"] = {
  "answer": "A",
  "solution": "MnO₄⁻ (Mn +7 → +4, gains 3e⁻, ×2) and SO₃²⁻ (S +4 → +6, loses 2e⁻, ×3).\nElectrons: 2 MnO₄⁻ gain 6e⁻, 3 SO₃²⁻ lose 6e⁻.\nRatio MnO₄⁻ : SO₃²⁻ = 2 : 3.\n→ A"
}
S["as-redox-balancing-q07"] = {
  "answer": "A",
  "solution": "Combining the two half-equations (multiply the first by 2 and the second by 3 to balance 6e⁻):\n2MnO₄⁻ + 4H₂O + 3SO₃²⁻ → 2MnO₂ + 3SO₄²⁻ + ...\nBalanced: 2MnO₄⁻ + H₂O + 3SO₃²⁻ → 2MnO₂ + 3SO₄²⁻ + 2OH⁻.\nSo u = x = z = 2. Manganese is reduced to +4; sulfur oxidised +4 → +6.\nAll three statements are correct → A"
}
S["as-redox-balancing-q08"] = {
  "answer": "B",
  "solution": "5HO₂CCO₂H + 2MnO₄⁻ + 6H⁺ → 10CO₂ + 2Mn²⁺ + 8H₂O.\nEach ethanedioic acid loses 2e⁻ (×5 = 10e⁻); each MnO₄⁻ gains 5e⁻ (×2 = 10e⁻).\nBalancing gives 8 water molecules.\n→ B"
}
S["as-redox-balancing-q09"] = {
  "answer": "D",
  "solution": "aH₂SO₄ + bP → cH₃PO₄ + dSO₂ + eH₂O.\nBalanced: 5H₂SO₄ + 2P → 2H₃PO₄ + 5SO₂ + 2H₂O.\n(P: 0 → +5, loses 5e⁻, ×2; S: +6 → +4, gains 2e⁻, ×5.)\nSum a+b+c+d+e = 5+2+2+5+2 = 16.\n→ D"
}
S["as-redox-balancing-q10"] = {
  "answer": "C",
  "solution": "X MnO₄⁻ + Fe²⁺ + H⁺ → Mn²⁺ + Y Fe³⁺ + H₂O.\nMnO₄⁻ (Mn +7 → +2, gains 5e⁻) needs 5 Fe²⁺ (each loses 1e⁻).\nSo X = 1, Y = 5: MnO₄⁻ + 5Fe²⁺ + 8H⁺ → Mn²⁺ + 5Fe³⁺ + 4H₂O.\n→ C"
}
S["as-redox-balancing-q11"] = {
  "answer": "C",
  "solution": "2S₂O₃²⁻ + xVO₂⁺ + yH⁺ → S₄O₆²⁻ + zVO²⁺ + 2H₂O.\nV goes +5 → +4 (gains 1e⁻). Each S₂O₃²⁻ loses 1e⁻ (2S +2 → +2.5), so 2 thiosulfate lose 2e⁻ → need 2 VO₂⁺.\nSo x = z = 2, and y = 4. Vanadium: +5 → +4.\n→ x and z equal and HALF of y, V +5→+4 → C"
}
S["as-redox-balancing-q12"] = {
  "answer": "C",
  "solution": "vCl₂ + wOH⁻ → xCl⁻ + yClO₃⁻ + zH₂O (disproportionation).\nCl: 0 → −1 (gains 1e⁻, ×5) and 0 → +5 (loses 5e⁻, ×1).\nSo 5 Cl⁻ and 1 ClO₃⁻ per 6 Cl atoms → v = 3, x = 5, y = 1.\n3Cl₂ + 6OH⁻ → 5Cl⁻ + ClO₃⁻ + 3H₂O.\n→ C"
}
S["as-redox-balancing-q13"] = {
  "answer": "D",
  "solution": "Cu + HNO₃ → Cu(NO₃)₂ + NO + H₂O.\nBalanced: 3Cu + 8HNO₃ → 3Cu(NO₃)₂ + 2NO + 4H₂O.\n(Cu: 0 → +2, loses 2e⁻, ×3; N: +5 → +2, gains 3e⁻, ×2.)\n8 moles of acid react with 3 moles of copper.\n→ D"
}
S["as-redox-balancing-q14"] = {
  "answer": "C",
  "solution": "vICl₃ + wH₂O → xHCl + yHI + zHIO₃ + zHClO₃.\nCl: +1 → −1 (gains 2e⁻, ×8) and +1 → +5 (loses 4e⁻, ×1).\nI: +1 → +1 in HI (no change) and +1 → +5 (loses 4e⁻, ×1).\nBalanced: 3ICl₃ + 6H₂O → 8HCl + 2HI + HIO₃ + HClO₃.\nSo v = 3, x = 8, z = 1.\n→ C"
}
S["as-redox-balancing-q15"] = {
  "answer": "B",
  "solution": "First equation: 2SO₃²⁻ + 2H₂O + Zn → Zn²⁺ + 4OH⁻ + S₂O₄²⁻ (a = 2, b = 2).\nSecond: MnO₂ + 2SO₃²⁻ + 4H⁺ → Mn²⁺ + S₂O₆²⁻ + 2H₂O (w = 2, x = 4).\n→ a = 2, b = 2, w = 2, x = 4 → B"
}


def main():
    # 校验：answer 必须与题库 ms_answer 一致（结构化题跳过）
    def load(p, marker):
        raw = open(p, encoding="utf-8").read()
        i = raw.index(marker); i = raw.index("=", i) + 1; j = raw.rindex("};")
        return json.loads(raw[i:j + 1])

    mcq = load(ROOT / "quiz-app" / "site" / "data.js", "window.CHEMBANK_DATA")
    struct = load(ROOT / "quiz-app" / "site" / "structured-data.js", "window.STRUCTURED_DATA")
    lookup = {}
    for q in mcq["questions"]:
        lookup[q["id"]] = q
    for q in struct["questions"]:
        lookup[q["id"]] = q

    # Redox 自定义题只在 Supabase（不在本地题库），答案取自 scripts/patch_redox_answers.py
    REDOX_ANSWERS = ["D", "C", "D", "C", "D", "A", "A", "B", "D", "C", "C", "C", "D", "C", "B"]
    redox_known = {f"as-redox-balancing-q{i:02d}": a for i, a in enumerate(REDOX_ANSWERS, 1)}

    mismatches = []
    for qid, entry in S.items():
        q = lookup.get(qid)
        if q is None and qid not in redox_known:
            mismatches.append(f"{qid}: 不在题库")
            continue
        if q is not None and q.get("type") == "structured":
            mismatches.append(f"{qid}: 是 structured，不应写文字解析")
            continue
        ms = ((q or {}).get("ms_answer") or redox_known.get(qid) or "").strip().upper()
        ans = (entry.get("answer") or "").strip().upper()
        if ms and ans != ms:
            mismatches.append(f"{qid}: 解析答案 {ans!r} ≠ ms_answer {ms!r}")
    if mismatches:
        print("✗ 校验失败，拒绝写入：")
        for m in mismatches:
            print("  -", m)
        raise SystemExit(1)

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    before = len(data)
    for qid, entry in S.items():
        data[qid] = entry
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Merged: {before} → {len(data)} entries; {len(S)} English MCQ solutions written (all verified vs ms_answer)")


if __name__ == "__main__":
    main()
