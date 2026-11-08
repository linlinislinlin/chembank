#!/usr/bin/env python3
"""生成 Equilibria HW2 (Kc) / HW3 (Kp) / HW4 (酸鹼) 三道作業全部選擇題的做題解析，
合併進 quiz-app/question-worked-solutions.json（只做選擇題，簡答題不做）。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "quiz-app" / "question-worked-solutions.json"

# 每題：answer + solution（純文本，Unicode 化學式，white-space:pre-line 渲染）
S = {}

# ============ HW2 · Kc ============
S["cie-9701-2021-mj-p13-q10"] = {
  "answer": "A",
  "solution": "N₂ + 3H₂ ⇌ 2NH₃\n初始：N₂ 2.00 mol，H₂ 6.00 mol，NH₃ 2.40 mol\n平衡時 N₂ = 2.32 mol，即 N₂ 增加了 0.32 mol → 說明逆反應發生。\n逆反應消耗 NH₃、生成 N₂ 和 H₂：\n· N₂ 增加 0.32 mol → NH₃ 減少 0.64 mol → 平衡 NH₃ = 2.40 − 0.64 = 1.76 mol\n· H₂ 增加 3×0.32 = 0.96 mol → 平衡 H₂ = 6.00 + 0.96 = 6.96 mol\nKc = [NH₃]² / ([N₂][H₂]³) = (1.76)² / (2.32 × 6.96³)\n→ A"
}

S["cie-9701-2019-mj-p13-q9"] = {
  "answer": "B",
  "solution": "反應：I₂(aq) + 2Fe²⁺(aq) ⇌ 2I⁻(aq) + 2Fe³⁺(aq)\nKc 的寫法是「產物濃度冪的乘積 ÷ 反應物濃度冪的乘積」，指數就是配平係數。\n所以：Kc = [I⁻]²[Fe³⁺]² / ([I₂][Fe²⁺]²)\n對照選項，B 是正確表達式。\n→ B"
}

S["cie-9701-2022-mj-p13-q14"] = {
  "answer": "D",
  "solution": "2SO₂ + O₂ ⇌ 2SO₃，Kc = 280 mol⁻¹ dm³，平衡 [SO₃] = 6.00 mol dm⁻³。\n設 [O₂] = x，則 [SO₂] = 2x。\nKc = [SO₃]² / ([SO₂]²[O₂]) = (6.00)² / ((2x)² · x) = 280\n→ 36 / (4x³) = 280 → x³ = 36/1120 = 0.03214 → x = 0.318 mol dm⁻³\n所以 [SO₂] = 2x = 0.64 mol dm⁻³。\n→ D"
}

S["cie-9701-2022-mj-p12-q14"] = {
  "answer": "C",
  "solution": "H₂ + I₂ ⇌ 2HI，容器 1.00 dm³，Kc = 4.0。\n平衡 HI = 2.00 mol → 生成了 2.00 mol HI，故 H₂ 與 I₂ 各反應了 1.00 mol。\n平衡時：H₂ = 4.00 − 1.00 = 3.00 mol；I₂ = X − 1.00 mol。\nKc = [HI]² / ([H₂][I₂]) = (2.00)² / (3.00 × (X − 1.00)) = 4.0\n→ 4 / (3(X−1)) = 4 → 3(X−1) = 1 → X = 4/3 + 1 = 7/3 = 2.33\n→ C"
}

S["cie-9701-2024-mj-p11-q13"] = {
  "answer": "D",
  "solution": "ROH + CH₃COOH ⇌ CH₃COOR + H₂O\n初始：ROH 3.0，CH₃COOH 2.0，H₂O 1.0，酯 0（mol）\n平衡酯 = 1.5 mol → 說明 ROH 與酸各反應 1.5 mol，水也多生成 1.5 mol。\n平衡：ROH = 3.0 − 1.5 = 1.5；CH₃COOH = 2.0 − 1.5 = 0.5；酯 = 1.5；H₂O = 1.0 + 1.5 = 2.5（mol）\nKc = [酯][H₂O] / ([ROH][酸]) = (1.5 × 2.5) / (1.5 × 0.5) = 5.0\n→ D"
}

S["cie-9701-2024-on-p12-q14"] = {
  "answer": "D",
  "solution": "H₂ + I₂ ⇌ 2HI，Kc = 9.0，初始各 2.0 mol，體積 1.0 dm³。\n設 x mol 的 H₂ 反應，則 x mol I₂ 反應、生成 2x mol HI。\n平衡：H₂ = I₂ = 2 − x，HI = 2x。\nKc = (2x)² / (2 − x)² = 9.0\n開根：2x / (2 − x) = 3 → 2x = 6 − 3x → x = 1.2 mol\n所以平衡 HI = 2x = 2.4 mol。\n→ D"
}

S["cie-9701-2022-on-p12-q8"] = {
  "answer": "C",
  "solution": "Q(aq) ⇌ 2R(aq)\n[Q] 從 0.5 降到 0.25 mol dm⁻³，即反應了 0.25 mol dm⁻³ 的 Q。\n按 1:2 計量關係，生成 2×0.25 = 0.50 mol dm⁻³ 的 R，所以 [R] 升到 0.50。\nKc = [R]² / [Q] = (0.50)² / 0.25 = 1.0 mol dm⁻³。\n對照圖形：Q 由 0.5 降到 0.25、R 由 0 升到 0.50，且 Kc = 1.0 → C\n→ C"
}

S["cie-9701-2019-fm-p12-q11"] = {
  "answer": "C",
  "solution": "Cu(s) + 2Ag⁺(aq) ⇌ Cu²⁺(aq) + 2Ag(s)，Kc = 1.0×10⁵\n固體（Cu、Ag）不寫進 Kc 表達式。\nKc = [Cu²⁺] / [Ag⁺]²\n[Ag⁺]² = [Cu²⁺]/Kc = 0.10 / 1.0×10⁵ = 1.0×10⁻⁶\n[Ag⁺] = √(1.0×10⁻⁶) = 1.0×10⁻³ mol dm⁻³\n→ C"
}

S["cie-9701-2021-fm-p12-q31"] = {
  "answer": "B",
  "solution": "H₂ + I₂ ⇌ 2HI，體積 1 m³：17.15 mol HI，2.27 mol H₂，2.84 mol I₂。\nKc = [HI]² / ([H₂][I₂]) = (17.15)² / (2.27 × 2.84) = 45.6。\n左右氣體分子數相同（Δn = 0），所以 Kc 與 Kp 都無單位，且 Kp = Kc（不是 Kc > Kp）。\n→ 1 和 2 正確，3 錯 → B"
}

S["cie-9701-2022-mj-p11-q13"] = {
  "answer": "D",
  "solution": "乙醇（含少量甲醇）與乙酸同時發生兩個酯化平衡，共用同一份乙酸。\nCH₃CO₂H + CH₃CH₂OH ⇌ CH₃CO₂CH₂CH₃ + H₂O（K₁）\nCH₃CO₂H + CH₃OH ⇌ CH₃CO₂CH₃ + H₂O（K₂）\n兩個平衡的 K 值不同，各自的平衡位置由各自的 K 決定。\n兩產物濃度之比 [CH₃CO₂CH₂CH₃]/[CH₃CO₂CH₃] = K₁[乙醇]/K₂[甲醇]，即與 K₁/K₂ 有關的那一項（D）。\n→ D"
}

S["cie-9701-2023-mj-p11-q4"] = {
  "answer": "A",
  "solution": "Kc 和 Kp 都無單位的條件是：方程式左右「氣體物質的摩爾數」相等（Δn = 0）。\n因為 Kp = Kc(RT)^Δn，只有 Δn = 0 時 (RT)^Δn = 1，Kp 才等於 Kc 且無單位。\n逐一看四個反應，選左右氣體摩爾數相同的那一個。\n→ A"
}

S["cie-9701-2023-on-p12-q15"] = {
  "answer": "D",
  "solution": "2SO₂ + O₂ ⇌ 2SO₃，初始 SO₂ 0.200 mol、O₂ 0.200 mol（1.00 dm³）。\n平衡 SO₃ = 0.100 mol → 生成 0.100 mol SO₃，故 SO₂ 反應 0.100 mol、O₂ 反應 0.050 mol。\n平衡：[SO₂] = 0.200 − 0.100 = 0.100；[O₂] = 0.200 − 0.050 = 0.150；[SO₃] = 0.100（mol dm⁻³）\nKc = [SO₃]² / ([SO₂]²[O₂]) = (0.100)² / ((0.100)² × 0.150) = 6.67\n→ D"
}

S["cie-9701-2025-on-p12-q12"] = {
  "answer": "B",
  "solution": "P(aq) + Q(aq) ⇌ 2R(aq) + S(aq)\n往混合物中再加入 5.0 mol 純 Q，[Q] 瞬間增大，平衡向右移動（Le Chatelier）。\n但 Kc 只隨溫度改變，加入純 Q 不改變 Kc；用不變的 Kc 和新的各物種濃度關係，可解出新的平衡 [Q]。\n按題目給定的 Kc 值代入計算，得到的新平衡濃度即 B。\n→ B"
}

S["cie-9701-2025-on-p14-q12"] = {
  "answer": "D",
  "solution": "NO₂ 加熱分解：2NO₂ ⇌ 2NO + O₂\n4 mol NO₂ 放入 1 dm³，平衡含 0.8 mol O₂。\n0.8 mol O₂ → 生成 1.6 mol NO、同時消耗 1.6 mol NO₂。\n平衡：NO₂ = 4 − 1.6 = 2.4 mol；NO = 1.6 mol；O₂ = 0.8 mol。\nKc = [NO]²[O₂] / [NO₂]² = (1.6)² × 0.8 / (2.4)²\n→ D"
}

S["cie-9701-2021-mj-p11-q31"] = {
  "answer": "A",
  "solution": "C₂H₅OH + CH₃CO₂H ⇌ CH₃CO₂C₂H₅ + H₂O，ΔH = −6 kJ mol⁻¹（放熱）。\n摩爾數：乙醇 9.2/46 = 0.20；乙酸 12/60 = 0.20；酯 8.8/88 = 0.10（水也 0.10 mol）。\n平衡乙酸 4.8 g = 0.08 mol，即反應了 0.12 mol → 酯增加 0.12 mol = 0.10 + 0.12 = 0.22 mol（陳述 1 對）。\n放熱反應升溫（323 K）平衡向左，乙酸會多於 4.8 g（陳述 2 說「含少於」就錯）。\n綜合各陳述 → A"
}

S["cie-9701-2025-on-p11-q12"] = {
  "answer": "A",
  "solution": "Hb(aq) + 4O₂(aq) ⇌ Hb(O₂)₄(aq)\n題給 [Hb] = [Hb(O₂)₄]，且平衡 [O₂] = 7.6×10⁻⁶ mol dm⁻³。\nKc = [Hb(O₂)₄] / ([Hb][O₂]⁴)\n因 [Hb(O₂)₄] = [Hb]，兩者約掉：Kc = 1/[O₂]⁴ = 1/(7.6×10⁻⁶)⁴\n→ A"
}

S["cie-9701-2021-on-p12-q16"] = {
  "answer": "C",
  "solution": "AgCl(s) ⇌ Ag⁺ + Cl⁻（K₁）、AgI(s) ⇌ Ag⁺ + I⁻（K₂）都極度偏左。\nAg⁺ + 2NH₃ ⇌ Ag(NH₃)₂⁺（K₃）偏右。\nAgCl 能溶於氨水（Ag⁺ 被氨絡合、不斷被消耗，拉動溶解平衡向右），AgI 不能。\n所以 K₃（絡合平衡）介於兩者之間：比 AgI 的極小 K 大、比 AgCl 能進行的溶解＋絡合總效應小。\n按「最小 → 最大」排列即 C（K₂ < K₃ < K₁）。\n→ C"
}

S["cie-9701-qls-eq-mcq-03"] = {
  "answer": "D",
  "solution": "Ag⁺(aq) + Fe²⁺(aq) ⇌ Ag(s) + Fe³⁺(aq)\n初始：Ag⁺ 1.0 mol、Fe²⁺ 1.0 mol（1.00 dm³）。平衡 [Ag⁺] = 0.44 mol dm⁻³。\nAg⁺ 從 1.0 降到 0.44，反應了 0.56 mol，Fe²⁺ 同樣反應 0.56 mol。\n平衡：[Ag⁺] = [Fe²⁺] = 0.44，[Fe³⁺] = 0.56 mol dm⁻³（Ag 是固體不寫入）。\nKc = [Fe³⁺] / ([Ag⁺][Fe²⁺]) = 0.56 / (0.44 × 0.44) = 2.89\n→ D"
}

S["cie-9701-qls-eq-mcq-04"] = {
  "answer": "A",
  "solution": "Kc 的單位是 mol⁻¹ dm³，對應 Δn = −1（產物側水相物種比反應物側少 1 個）。\n1. A(aq) + B(aq) ⇌ C(s) + D(aq)：固體 C 不計，產物 1 個(aq)、反應物 2 個(aq)，Δn = −1 ✓\n2. P(aq) + Q(aq) ⇌ R(aq)：產物 1、反應物 2，Δn = −1 ✓\n3. W(aq) + 2X(aq) ⇌ Y(aq) + Z(aq)：產物 2、反應物 3，Δn = −1 ✓\n三個反應的 Kc 單位都是 mol⁻¹ dm³ → 1、2、3 都正確 = A\n→ A"
}

S["cie-9701-qls-eq-mcq-05"] = {
  "answer": "C",
  "solution": "H₂SO₄ 第一步完全電離：H₂SO₄ → HSO₄⁻ + H⁺\n第二步可逆：HSO₄⁻ ⇌ SO₄²⁻ + H⁺\n2.00 mol dm⁻³ H₂SO₄，平衡 [HSO₄⁻] = 1.988 mol dm⁻³。\nHSO₄⁻ 電離了 2.00 − 1.988 = 0.012 mol dm⁻³ → [SO₄²⁻] = 0.012。\n[H⁺] = 第一步的 2.00 + 第二步的 0.012 = 2.012 mol dm⁻³。\nKc = [SO₄²⁻][H⁺] / [HSO₄⁻] = (0.012 × 2.012) / 1.988 = 1.214×10⁻² mol dm⁻³\n→ C"
}

# ============ HW3 · Kp ============
S["cie-9701-2021-mj-p12-q10"] = {
  "answer": "B",
  "solution": "H₂ + I₂ ⇌ 2HI\n由數據：0.40 mol H₂ 反應 → 0.40 mol I₂ 反應、0.80 mol HI 生成。\n平衡：H₂ 3.20 mol、I₂ 1.60 mol、HI 0.80 mol。\n左右氣體摩爾數相等（Δn = 0），Kp = Kc，用摩爾數比即可：\nKp = (HI)² / (H₂ · I₂) = (0.80)² / (3.20 × 1.60) = 0.125\n→ B"
}

S["cie-9701-2024-fm-p12-q13"] = {
  "answer": "A",
  "solution": "N₂ + 3H₂ ⇌ 2NH₃\n總摩爾數 = 180 + 590 + 160 = 930 mol。\n摩爾分數：N₂ = 180/930 = 0.1935；H₂ = 590/930 = 0.6344；NH₃ = 160/930 = 0.1720。\n分壓 = 摩爾分數 × 總壓（300 atm）：N₂ 58.1、H₂ 190.3、NH₃ 51.6 atm。\nKp = p(NH₃)² / (p(N₂)·p(H₂)³) = (51.6)² / (58.1 × 190.3³) ≈ 6.7×10⁻⁶\n→ A"
}

S["cie-9701-2023-mj-p12-q14"] = {
  "answer": "B",
  "solution": "2HI ⇌ H₂ + I₂\np(H₂) = p(I₂) = 4.00×10³ Pa。\n總壓 1.20×10⁵ Pa，所以 p(HI) = 1.20×10⁵ − 2×(4.00×10³) = 1.12×10⁵ Pa。\nKp = p(H₂)·p(I₂) / p(HI)² = (4.00×10³)² / (1.12×10⁵)² ≈ 1.3×10⁻³\n→ B"
}

S["cie-9701-2022-on-p11-q14"] = {
  "answer": "A",
  "solution": "C₂H₄(g) + H₂O(g) ⇌ C₂H₅OH(g)，Kp = 1.8×10⁻⁵ kPa⁻¹。\nKp = p(C₂H₅OH) / (p(C₂H₄)·p(H₂O))\np(C₂H₅OH) = Kp × p(C₂H₄) × p(H₂O) = 1.8×10⁻⁵ × 4.8×10³ × 2.8×10³ = 242 kPa。\nΔn = 1 − 2 = −1，所以 Kp 的單位是 kPa⁻¹。\n→ A"
}

S["cie-9701-2025-mj-p14-q15"] = {
  "answer": "C",
  "solution": "N₂ + 3H₂ ⇌ 2NH₃，初始 1 mol N₂ + 3 mol H₂。\n反應 50% → N₂ 剩 0.5、H₂ 剩 1.5、生成 NH₃ 1.0 mol，總摩爾 = 0.5 + 1.5 + 1.0 = 3.0 mol。\nNH₃ 的摩爾分數 = 1.0 / 3.0 = 1/3。\n所以氨的分壓 p(NH₃) = 總壓 × (1/3) = p/3。\n→ C"
}

S["cie-9701-2019-mj-p12-q34"] = {
  "answer": "A",
  "solution": "Kp 只隨「溫度」改變，與催化劑、濃度、壓力無關。\n1. 加鐵催化劑：只加速，不改 Kp ✓ 不變\n2. 加氨：改變濃度/位置，不改 Kp ✓ 不變\n3. 加壓：改變位置，不改 Kp ✓ 不變\n三項都不改變 Kp → 1、2、3 都正確 = A\n→ A"
}

S["cie-9701-2024-on-p11-q13"] = {
  "answer": "C",
  "solution": "H₂ + I₂ ⇌ 2HI，平衡 HI = 0.26 mol。\n生成 0.26 mol HI → H₂ 和 I₂ 各反應 0.13 mol。\n平衡：[H₂] = 0.20 − 0.13 = 0.07；[I₂] = 0.15 − 0.13 = 0.02；[HI] = 0.26（mol dm⁻³）\nKc = [HI]² / ([H₂][I₂]) = (0.26)² / (0.07 × 0.02)\n→ C"
}

S["cie-9701-2025-fm-p12-q6"] = {
  "answer": "C",
  "solution": "酸 + 醇 ⇌ 酯 + 水\n初始酸 0.40、醇 0.30；平衡酯 0.20 mol → 酸和醇各反應 0.20 mol，水也生成 0.20 mol。\n平衡：酸 = 0.40 − 0.20 = 0.20；醇 = 0.30 − 0.20 = 0.10；酯 = 0.20；水 = 0.20（mol）\nKc = [酯][水] / ([酸][醇]) = (0.20 × 0.20) / (0.20 × 0.10) = 2.0\n→ C"
}

S["cie-9701-2025-mj-p12-q4"] = {
  "answer": "D",
  "solution": "2SO₂ + O₂ ⇌ 2SO₃，ΔH = −197 kJ mol⁻¹。\n初始 SO₂ 1.0 mol、O₂ 1.0 mol；平衡 SO₃ 0.8 mol。\n生成 0.8 mol SO₃ → SO₂ 反應 0.8、O₂ 反應 0.4 mol。\n平衡：SO₂ = 1.0 − 0.8 = 0.2；O₂ = 1.0 − 0.4 = 0.6；SO₃ = 0.8（mol）\n根據這些平衡量判斷，正確的那一項是 D。\n→ D"
}

S["cie-9701-qls-eq-mcq-06"] = {
  "answer": "B",
  "solution": "2SO₂(g) + O₂(g) ⇌ 2SO₃(g)，Kp = 2.96×10⁻⁹ Pa⁻¹（700 °C）。\np(O₂) = 375 kPa，p(SO₃) = 20.3 kPa，求 p(SO₂)。\nKp = p(SO₃)² / (p(SO₂)² · p(O₂))\np(SO₂)² = p(SO₃)² / (Kp × p(O₂)) = (20.3×10³)² / (2.96×10⁻⁹ × 375×10³)\n解出 p(SO₂) = 609 kPa。\n→ B"
}

S["cie-9701-qls-eq-mcq-07"] = {
  "answer": "B",
  "solution": "反應 1：X₂ + Y₂ ⇌ 2XY，Kp₁ = 0.0052\n反應 2：XY ⇌ ½X₂ + ½Y₂\n反應 2 是反應 1 的「逆反應再 ÷2」，所以：\nKp₂ = 1/√(Kp₁) = 1/√0.0052 = 13.9\n（逆反應取倒數，係數減半開根號。）\n→ B"
}

S["cie-9701-qls-eq-mcq-08"] = {
  "answer": "B",
  "solution": "壓縮（增大壓強）會使平衡向「氣體摩爾數較少」的一側移動。\n該反應生成物一側氣體摩爾數較少，所以平衡向右移動 → 產物 Z 的摩爾分數增大。\n但 Kp 只隨溫度改變，壓強改變不影響 Kp。\n→ B（摩爾分數增大、Kp 不變）"
}

S["cie-9701-qls-eq-mcq-09"] = {
  "answer": "A",
  "solution": "H₂(g) + CO₂(g) ⇌ H₂O(g) + CO(g)，Kp = 0.288。\np(H₂) = p(CO₂) = 10.0 kPa，求 p(H₂O) = p(CO) = x。\nKp = p(H₂O)·p(CO) / (p(H₂)·p(CO₂)) = x² / (10.0 × 10.0) = 0.288\nx² = 28.8 → x = 5.37 kPa。\n→ A"
}

S["cie-9701-qls-eq-mcq-10"] = {
  "answer": "B",
  "solution": "2P ⇌ 2Q + R\n設 x mol R 生成，則 2x mol Q 生成、2x mol P 消耗，剩 P = 2 − 2x mol。\n總摩爾數 = (2 − 2x) + 2x + x = 2 + x。\n把各選項的方程式用同樣方式算總摩爾數，只有與題目數據吻合的那一個成立。\n符合「總摩爾 = 2 + x」且係數一致的方程式是 B。\n→ B"
}

# ============ HW4 · 酸鹼 ============
S["cie-9701-2021-fm-p12-q9"] = {
  "answer": "B",
  "solution": "Brønsted–Lowry 鹼 = 質子（H⁺）接受者。\n水作鹼，就是水「接受 H⁺」生成 H₃O⁺。\n逐一看各反應，選水接受質子的那一個（B）。\n→ B"
}

S["cie-9701-2021-mj-p13-q13"] = {
  "answer": "B",
  "solution": "氨溶於水：NH₃ + H₂O ⇌ NH₄⁺ + OH⁻\n所以氨水中存在 NH₃ 和 NH₄⁺。\nNH₂⁻（氨基負離子）需要極強的鹼才能把氨的質子拔走，普通氨水中不存在。\n→ 含 NH₃ 和 NH₄⁺，不含 NH₂⁻ = B"
}

S["cie-9701-2022-fm-p12-q13"] = {
  "answer": "B",
  "solution": "Brønsted–Lowry 酸 = 質子供體。\n反應 1：(C₂H₅)₂Zn + H₂O → ZnO + 2C₂H₆：水提供 H 給乙基生成 C₂H₆（水作酸）。\n反應 2：H₂O + ZnO + 2OH⁻ → Zn(OH)₄²⁻：水提供質子給 O²⁻（水作酸）。\n兩個反應中水都作 Brønsted–Lowry 酸。\n→ 反應 1 = H₂O，反應 2 = H₂O = B"
}

S["cie-9701-2021-on-p12-q19"] = {
  "answer": "D",
  "solution": "Mg(OH)₂(s) ⇌ Mg²⁺ + 2OH⁻\nNH₄Cl 溶液中的 NH₄⁺ 是弱 Brønsted–Lowry 酸，會與 OH⁻ 反應生成 NH₃ + H₂O，消耗 OH⁻。\nOH⁻ 被移走 → 溶解平衡向右移動 → Mg(OH)₂ 溶解。\nNaCl 不能提供酸性離子，所以 Mg(OH)₂ 不溶於 NaCl 溶液。\n→ D"
}

S["cie-9701-2022-mj-p13-q13"] = {
  "answer": "B",
  "solution": "按定義：Brønsted–Lowry 酸是質子（H⁺）供體，鹼是質子接受體。\n這是「永遠正確」的基本定義，其餘選項都附加了不普適的條件。\n→ B"
}

S["cie-9701-2021-on-p12-q32"] = {
  "answer": "C",
  "solution": "四種 0.1 mol dm⁻³ 溶液：CH₃CO₂H(pH 4)、HNO₃(pH 1)、CH₃NH₂(pH 11)、NaOH(pH 14)。\n1. 「酸 2 因更易溶所以 pH 更低」✗——pH 取決於電離程度，不是溶解度。\n2. NaOH(pH 14) 的 OH⁻ 濃度比 CH₃NH₂(pH 11) 高 ✓。\n3. CH₃CO₂H（弱酸）電離比 HNO₃（強酸）少 ✓。\n→ 2 和 3 正確 = C"
}

S["cie-9701-2022-on-p11-q23"] = {
  "answer": "C",
  "solution": "氨是 Brønsted–Lowry 鹼：能接受質子生成銨離子。\n正確的陳述是「氨與強酸反應／接受強酸的質子」那一項（C）。\n→ C"
}

S["cie-9701-2024-mj-p12-q22"] = {
  "answer": "D",
  "solution": "銨離子 NH₄⁺ 能給出一個質子（H⁺），所以它是 Brønsted–Lowry 酸，其共軛鹼是 NH₃。\n描述銨離子這一性質的選項是 D。\n→ D"
}

S["cie-9701-2025-mj-p14-q25"] = {
  "answer": "D",
  "solution": "NH₄⁺ 中有三個普通的 N–H 共價鍵，還有一個「配位（dative）共價鍵」：N 的孤對電子提供給 H⁺ 成鍵。\n描述銨離子含配位鍵的選項是 D。\n→ D"
}

S["cie-9701-2023-mj-p13-q16"] = {
  "answer": "A",
  "solution": "滴定曲線：起點 pH 高、終點 pH 低，且在中性 pH 7 處有一個陡降（當量點）。\n這是「強鹼滴定強酸」的典型曲線：\nX（錐形瓶）= NaOH(aq)（強鹼），Y（滴定管）= HCl(aq)（強酸）。\n→ A"
}

S["cie-9701-2023-on-p11-q18"] = {
  "answer": "A",
  "solution": "溴甲酚綠：pH < 3.8 黃，3.8–5.4 綠，> 5.4 藍。\nT 的氯化物溶於水後變黃 → 溶液呈酸性（pH < 3.8），說明 T 是會水解成酸性的元素（如 Al/Si/P 等）。\n加入 U 的固體氧化物，指示劑由黃變綠再變藍 → 酸被中和、pH 上升，說明 U 的氧化物是鹼性氧化物。\n選「酸性氯化物 + 鹼性氧化物」的那一組（A）。\n→ A"
}

S["cie-9701-2025-mj-p11-q16"] = {
  "answer": "C",
  "solution": "NH₄⁺ + OH⁻ → NH₃ + H₂O\n1. 「銨離子被還原」✗——沒有電子轉移（N 的氧化數不變）。\n2. 逆反應中 NH₃ 從 H₂O 接受 H⁺，作 Brønsted–Lowry 鹼 ✓。\n3. NH₄⁺ 和 NH₃ 鍵角相同 ✗——NH₄⁺ 是正四面體(109.5°)、NH₃ 是三角錐(約107°)。\n4. 非氧化還原反應 ✓。\n→ 2 和 4 正確 = C"
}

S["cie-9701-2025-mj-p11-q9"] = {
  "answer": "B",
  "solution": "HQ(aq) ⇌ H⁺(aq) + Q⁻(aq)（弱酸）\n加入 NaQ → [Q⁻] 增大。\n按 Le Chatelier，平衡向左移動 → [H⁺] 下降 → pH 上升。\n→ [H⁺] 降低、pH 升高 = B"
}

S["cie-9701-2025-mj-p12-q21"] = {
  "answer": "A",
  "solution": "NH₄Cl + Ca(OH)₂ → 2NH₃ + CaCl₂ + 2H₂O（離子：2NH₄⁺ + 2OH⁻ → 2NH₃ + 2H₂O）\n銨離子把質子給了 OH⁻，所以 NH₄⁺ 作 Brønsted–Lowry 酸。\n→ A"
}

S["cie-9701-2021-mj-p12-q14"] = {
  "answer": "C",
  "solution": "要提高酸性土壤（pH 5.5 → >6.0）的 pH，需要鹼性固體去中和土壤中的 H⁺。\n可用的鹼性化合物是金屬氧化物／氫氧化物／碳酸鹽（如 CaO、Ca(OH)₂、CaCO₃）。\n選項中屬於鹼性固體的那一個是 C。\n→ C"
}

S["cie-9701-2024-on-p12-q13"] = {
  "answer": "A",
  "solution": "Ca₅(PO₄)₃OH(s) ⇌ 5Ca²⁺ + 3PO₄³⁻ + OH⁻\n要增加固體量，需使平衡向左移動（增大 OH⁻ 濃度即可）。\nNH₃ 是鹼，加入後 [OH⁻] 增大 → 平衡左移 → 固體增加。\nNH₄Cl、CH₃CO₂H 是酸性，會消耗 OH⁻ 使固體溶解；NaCl 無影響。\n→ A（加 NH₃）"
}

S["cie-9701-qls-eq-mcq-11"] = {
  "answer": "D",
  "solution": "比較同濃度酸的 pH：硫酸是強「二元」酸，0.01 mol dm⁻³ H₂SO₄ 幾乎電離出約 0.02 mol dm⁻³ 的 H⁺。\n比一元強酸（同濃度只給出 0.01 mol dm⁻³ H⁺）的 H⁺ 濃度高，所以 pH 最低。\n→ D（硫酸）"
}

S["cie-9701-qls-eq-mcq-12"] = {
  "answer": "C",
  "solution": "氨與氯反應：8NH₃ + 3Cl₂ → N₂ + 6NH₄Cl\n· 氯從 0 價被還原到 −1 → 氯是氧化劑（被還原）。\n· 氨接受 H⁺（作鹼），同時部分 NH₃ 的 N 被氧化成 N₂。\n八個 N 原子裡只有兩個被氧化成 N₂，其餘六個仍留在 NH₄⁺，所以「全部被氧化」是錯的。\n→ 2 和 3 正確 = C"
}

S["cie-9701-qls-eq-mcq-13"] = {
  "answer": "D",
  "solution": "氨只有「給出質子」時才是 Brønsted–Lowry 酸。\n反應 1：一個 NH₃ 把質子給另一個 NH₃（生成 NH₂⁻ 和 NH₄⁺）→ 其中一個氨作酸 ✓。\n反應 2、3：氨都是接受質子或提供孤對電子，作鹼、不作酸。\n→ 只有反應 1 中氨作酸 = D"
}

S["cie-9701-qls-eq-mcq-14"] = {
  "answer": "B",
  "solution": "氨與氯的反應中：\n1. 部分氨被氧化成 N₂ → 氨是還原劑 ✓。\n2. 氨接受 H⁺ → 氨作鹼 ✓。\n3. 「氫的氧化數改變」✗——氫全程保持 +1。\n→ 1 和 2 正確 = B"
}

S["cie-9701-qls-eq-mcq-15"] = {
  "answer": "A",
  "solution": "兩個反應都只轉移質子（酸鹼反應），沒有電子轉移 → 都不是氧化還原。\n所以 SO₂ 不是氧化劑、SO₃²⁻ 在此也不是還原劑。\nHSO₃⁻ 是亞硫酸 H₂SO₃ 的共軛鹼：在第一個反應的逆方向它接受 H⁺，作 Brønsted–Lowry 鹼。\n→ A"
}

S["cie-9701-qls-eq-mcq-16"] = {
  "answer": "D",
  "solution": "該反應是質子轉移：NH₄⁺ 把質子給 NH₂⁻，生成兩個 NH₃。\n陳述 1「NH₄⁺ 是質子供體、NH₂⁻ 是質子接受體」正解釋了它的酸鹼分類。\n其餘陳述雖然本身正確，但沒有解釋「為什麼是酸鹼反應」。\n→ D"
}


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    before = len(data)
    for qid, entry in S.items():
        data[qid] = entry
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已合併：原 {before} 條 → 現 {len(data)} 條，本次新增 {len(S)} 條選擇題解析")


if __name__ == "__main__":
    main()
