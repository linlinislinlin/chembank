#!/usr/bin/env python3
"""Build typeset student PDFs for AS stoichiometry homework 1–4."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml

SKILL = Path("/Users/tsinglan-school/.cursor/skills/chemistry-homework-formatter")
PREAMBLE = (SKILL / "templates/homework-preamble.tex").read_text(encoding="utf-8")
PRINT = Path("/Users/tsinglan-school/Desktop/题库/print")
QLS = Path("/Users/tsinglan-school/Desktop/QLS/AS/Homework/Stoichiometry")
VALIDATE = SKILL / "scripts/validate_manifest.py"
XELATEX = Path("/Users/tsinglan-school/Library/TinyTeX/bin/universal-darwin/xelatex")

EXTRA = r"""
\setlist[enumerate]{leftmargin=1.55em,itemsep=0.06em,topsep=0.12em}
\newcommand{\qhead}[1]{%
  \par\vspace{0.38em}%
  {\normalsize\bfseries #1}\par\vspace{0.12em}%
}
\newcommand{\mcq}[1]{%
  \par\noindent\textbf{#1.}\enspace\ignorespaces
}
\newcommand{\mcqend}{\hfill{[1]}\par}
\newcommand{\optrow}[4]{%
\par\noindent{\small
\begin{tabular}{@{}p{0.48\linewidth}@{}p{0.48\linewidth}@{}}
\textbf{A}\; #1 & \textbf{B}\; #2 \\[0.12em]
\textbf{C}\; #3 & \textbf{D}\; #4
\end{tabular}}\par
}
\newcommand{\optlist}[4]{%
\par
\begin{enumerate}[label=\textbf{\Alph*.}, leftmargin=1.55em, itemsep=0.05em, topsep=0.08em]
\item #1
\item #2
\item #3
\item #4
\end{enumerate}
}
\newcommand{\qfig}[2][0.58]{%
\par
\begin{center}\vspace{-0.1em}%
\includegraphics[width=#1\linewidth,keepaspectratio]{#2}%
\end{center}\vspace{-0.1em}%
}
"""


def header(title: str, marks: int, topics: str, extra: str) -> str:
    return rf"""
\begin{{document}}
\sethomework{{{title}}}{{{marks} marks}}

\begin{{center}}
{{\large\bfseries {title}}}\\[0.2em]
{{\small CIE 9701 AS Chemistry · {marks} MCQ · {marks} marks}}
\end{{center}}

\noindent Name: \underline{{\hspace{{5.8cm}}}} \quad Class: \underline{{\hspace{{2.6cm}}}} \quad Date: \underline{{\hspace{{2.8cm}}}}

\vspace{{0.25em}}
{{\small {topics}

Circle \textbf{{one}} letter (A--D) for each question. Show working. Calculators and a Periodic Table may be used.{extra}}}
\vspace{{0.15em}}
"""


HW = {}

HW[1] = {
    "slug": "2-stoichiometry-homework-1",
    "title": "AS stoichiometry homework 1 · mole foundations",
    "n": 14,
    "topics": r"Topics: 1 masses of atoms and molecules · 2 the mole and Avogadro · 3 reacting masses · 4 complete combustion.",
    "extra": "",
    "sections": [
        (1, r"1 · Masses of atoms and molecules"),
        (4, r"2 · The mole and the Avogadro constant"),
        (8, r"3 · Reacting masses"),
        (12, r"4 · Complete combustion"),
    ],
    "figs": {1: ("fig-q01-spectrum.png", 0.48), 3: ("fig-q03-apparatus.png", 0.72)},
    "qs": {
        1: r"""The mass spectrum of a sample of neon is shown. The relative abundance of each peak is written in brackets above it.
\qfig[0.48]{fig-q01-spectrum.png}
What is the relative atomic mass, $A_\mathrm{r}$, of this sample of neon?
\optrow{20.15}{20.20}{21.00}{21.82}""",
        2: r"""A sample of sulfur consists mostly of \ce{^{32}S}. It also contains 4.2\% \ce{^{34}S} and 2.8\% \ce{^{36}S}. No other isotopes of sulfur are present.

What is the relative atomic mass, $A_\mathrm{r}$, of \textbf{this} sample of sulfur?
\optrow{32.1}{32.2}{34.0}{34.3}""",
        3: r"""The diagram shows the apparatus used to find the relative molecular mass of a volatile liquid.

When 0.10\,g of a volatile liquid is injected into the syringe, all of the volatile liquid evaporates and the volume increases by 85\,cm$^3$.

The heater maintains a temperature of 400\,K and the experiment is carried out at a pressure of 101\,300\,Pa.
\qfig[0.78]{fig-q03-apparatus.png}
If the vapour of the volatile liquid behaves as an ideal gas, which expression can be used to calculate the relative molecular mass of the liquid?
\optlist{$M_\mathrm{r}=(85\times 101\,300)\div(0.10\times 8.31\times 400)$}{$M_\mathrm{r}=(85\times 101.3)\div(0.10\times 8.31\times 400)$}{$M_\mathrm{r}=(0.10\times 8.31\times 400)\div(85\times 10^{-6}\times 101\,300)$}{$M_\mathrm{r}=(0.10\times 8.31\times 400)\div(85\times 10^{-6}\times 101.3)$}""",
        4: r"""Which statement about the Avogadro constant is correct?
\optlist{It is the mass of one mole of any element.}{It is the mass of $6.02\times 10^{23}$ atoms of any element.}{It is the number of atoms in one mole of neon.}{It is the number of atoms in 12\,g of any element.}""",
        5: r"""Which contains the largest number of hydrogen atoms?
\optlist{0.10\,mol of pentane}{0.20\,mol of but-2-ene}{1.00\,mol of hydrogen molecules}{$6.02\times 10^{23}$ hydrogen atoms}""",
        6: r"""Which sample contains the most iodine?
\optrow{1\,g of \ce{CaI2}}{1\,g of \ce{KI}}{1\,g of \ce{NaI}}{1\,g of \ce{NH4I}}""",
        7: r"""What contains $9.03\times 10^{23}$ oxygen atoms?
\optlist{0.25\,mol aluminium oxide}{0.75\,mol sulfur dioxide}{1.5\,mol sulfur trioxide}{3.0\,mol water}""",
        8: r"""Sodium peroxide, \ce{Na2O2}, is used to absorb carbon dioxide from the atmosphere and release oxygen in closed environments such as space capsules and submarines.
\[\ce{2Na2O2 + 2CO2 -> 2Na2CO3 + O2}\]
Which mass of sodium peroxide would be required to remove 2.4\,dm$^3$ of carbon dioxide from the atmosphere at room temperature and pressure?
\optrow{2.4\,g}{3.9\,g}{7.8\,g}{15.6\,g}""",
        9: r"""A student reacts 0.100\,mol of each of sodium, magnesium and phosphorus atoms separately with an excess of oxygen.

Which rows are correct?

{\centering
{\small
\begin{tabular}{c l c}
\toprule
 & oxide & mass of oxide formed\,/\,g \\
\midrule
1 & sodium & 3.10 \\
2 & magnesium & 4.03 \\
3 & phosphorus & 7.10 \\
\bottomrule
\end{tabular}}\par}

\optrow{1, 2 and 3}{1 and 2 only}{1 and 3 only}{2 and 3 only}""",
        10: r"""Separate samples, each of mass 1.0\,g, of the compounds listed are treated with an excess of dilute acid.

Which compound releases the largest amount of \ce{CO2}?
\optrow{1.0\,g \ce{CaCO3}}{1.0\,g \ce{Li2CO3}}{1.0\,g \ce{MgCO3}}{1.0\,g \ce{Na2CO3}}""",
        11: r"""2.0\,g of ammonium nitrate, \ce{NH4NO3}, decomposes to give 0.90\,g of water and a single gas.

What is the identity of the gas?
\optrow{\ce{NO}}{\ce{NO2}}{\ce{N2O}}{\ce{N2}}""",
        12: r"""What is the minimum mass of oxygen required to ensure the complete combustion of 12\,dm$^3$ of propane measured under room conditions?
\optrow{60\,g}{80\,g}{120\,g}{160\,g}""",
        13: r"""Mixture R consists of one mole of \ce{C3H6} and one mole of \ce{C4H6}.

What is the minimum number of moles of oxygen molecules needed for complete combustion of mixture R?
\optrow{6.5}{7}{10}{20}""",
        14: r"""If 1 mole of hexane combusts in an excess of oxygen, how many moles of products are formed?
\optrow{11}{12}{13}{14}""",
    },
}

HW[2] = {
    "slug": "2-stoichiometry-homework-2",
    "title": "AS stoichiometry homework 2 · limiting reagent and yield",
    "n": 15,
    "topics": r"Topics: 5 excess / limiting reagent · 6 precise $A_\mathrm{r}$ · 7 percentage yield and purity. Later questions also use earlier skills (mole, reacting masses, combustion).",
    "extra": "",
    "sections": [
        (1, r"5 · Excess and limiting reagent"),
        (8, r"6 · Significant figures / precise $A_\mathrm{r}$"),
        (10, r"7 · Percentage yield and purity"),
        (13, r"Earlier skills · mole, reacting masses, combustion"),
    ],
    "figs": {},
    "qs": {
        1: r"""Calcium oxide and magnesium sulfide each react with acid.
\begin{align*}
\ce{CaO(s) + 2H+(aq) &-> Ca^{2+}(aq) + H2O(l)}\\
\ce{MgS(s) + 2H+(aq) &-> Mg^{2+}(aq) + H2S(g)}
\end{align*}
A mixture of these two compounds, X, reacts with exactly 0.125\,mol of dilute hydrochloric acid.

The amount of hydrogen sulfide formed is 0.0250\,mol.

What was the mass of calcium oxide in mixture X?
\optrow{1.4\,g}{2.1\,g}{2.8\,g}{4.2\,g}""",
        2: r"""A 3.7\,g sample of copper(II) carbonate is added to 25\,cm$^3$ of 2.0\,mol\,dm$^{-3}$ hydrochloric acid.

Which volume of gas is produced at room conditions?
\optrow{0.60\,dm$^3$}{0.72\,dm$^3$}{1.20\,dm$^3$}{2.40\,dm$^3$}""",
        3: r"""Methane and steam react to produce hydrogen.
\[\ce{CH4(g) + 2H2O(g) -> CO2(g) + 4H2(g)}\]
0.80\,g of methane and 1.35\,g of steam react. One of the reactants is used up.

Which volume of hydrogen, measured at room conditions, will be produced?
\optrow{1.80\,dm$^3$}{3.60\,dm$^3$}{4.80\,dm$^3$}{7.20\,dm$^3$}""",
        4: r"""In separate experiments, 5.0\,g samples of each of four s-block metals are added to an excess of water. The gas evolved is collected and its volume measured under the same conditions of temperature and pressure for each sample.

Which metal produces the largest volume of gas?
\optlist{calcium}{potassium}{rubidium}{strontium}""",
        5: r"""Crystals of copper(II) nitrate are prepared by adding an excess of malachite to nitric acid.

The formula of malachite is \ce{Cu(OH)2.CuCO3}. ($M_\mathrm{r}=221.0$)

12.0\,g of malachite is added to 30.0\,cm$^3$ of 1.50\,mol\,dm$^{-3}$ nitric acid.

Which mass of malachite is left unreacted when the reaction is complete?
\optrow{2.05\,g}{2.49\,g}{7.03\,g}{9.51\,g}""",
        6: r"""X is an impure sample of a Group 2 metal carbonate, \ce{MCO3}. X contains 57\% by mass of \ce{MCO3}. The impurities in X do \textbf{not} react with hydrochloric acid.

7.4\,g of X is reacted with an excess of dilute hydrochloric acid.

0.050\,mol of the Group 2 metal chloride is produced.

What is the identity of the Group 2 metal?
\optrow{\ce{Mg}}{\ce{Ca}}{\ce{Sr}}{\ce{Ba}}""",
        7: r"""In an experiment, 0.600\,mol of chlorine gas, \ce{Cl2}, is reacted with an excess of hot aqueous sodium hydroxide. One of the products is \ce{NaClO3}.

Which mass of \ce{NaClO3} is formed?
\optrow{21.3\,g}{44.7\,g}{63.9\,g}{128\,g}""",
        8: r"""The relative atomic mass of antimony is 121.76.

Antimony has \textbf{two} isotopes. The mass numbers of the two isotopes differ by two. The isotope with the lower mass number is the more abundant.

What is the percentage abundance of the isotope with the \textbf{higher} mass number?
\optrow{12\%}{38\%}{62\%}{88\%}""",
        9: r"""A sample of magnesium contains the isotopes \ce{^{24}Mg}, \ce{^{25}Mg} and \ce{^{26}Mg} only.

The percentage abundance of \ce{^{25}Mg} and \ce{^{26}Mg} is the same.

The relative atomic mass of magnesium in the sample is 24.3.

What is the percentage abundance of \ce{^{24}Mg}?
\optrow{10\%}{20\%}{60\%}{80\%}""",
        10: r"""0.200\,mol ethanenitrile reacts with an excess of dilute sodium hydroxide. The reaction produces organic compound S and ammonia gas only.

The reaction has an 80.0\% yield.

Which mass of S is produced?
\optrow{9.60\,g}{13.1\,g}{15.4\,g}{16.4\,g}""",
        11: r"""A piece of rock has a mass of 2.00\,g. It contains calcium carbonate, but no other basic substances. It neutralises exactly 36.0\,cm$^3$ of 0.500\,mol\,dm$^{-3}$ hydrochloric acid.

What is the percentage by mass of calcium carbonate in the 2.00\,g piece of rock?
\optrow{22.5\%}{45.0\%}{72.0\%}{90.1\%}""",
        12: r"""A sample of 2.30\,g of ethanol is mixed with an excess of aqueous acidified potassium dichromate(VI). The reaction mixture is boiled under reflux for one hour. The required organic product is then collected by distillation. The yield of product is 60.0\%.

Which mass of product is collected?
\optrow{1.32\,g}{1.38\,g}{1.80\,g}{3.00\,g}""",
        13: r"""Which sample contains the same number of the named species as the number of molecules in 35.5\,g of chlorine?
\optlist{atoms in 16\,g of sulfur}{atoms in 23\,g of sodium}{ions in 74.5\,g of potassium chloride}{molecules in 88\,g of carbon dioxide}""",
        14: r"""A 5.00\,g sample of an anhydrous Group 2 metal nitrate loses 3.29\,g in mass when heated strongly.

Which metal is present?
\optrow{magnesium}{calcium}{strontium}{barium}""",
        15: r"""An organic molecule W contains 3 carbon atoms. It requires 4.5 molecules of oxygen for complete combustion.

What could W be?
\optrow{propane}{propanoic acid}{propanone}{propan-1-ol}""",
    },
}

HW[3] = {
    "slug": "2-stoichiometry-homework-3",
    "title": "AS stoichiometry homework 3 · empirical and molecular formulae",
    "n": 18,
    "topics": r"Topics: 8 empirical formulae · 9 molecular formulae · 10 hydrates · 11 combustion analysis · 12 formulae and equations. Later questions also use earlier skills.",
    "extra": "",
    "sections": [
        (1, r"8 · Empirical formulae"),
        (5, r"9 · Molecular formulae"),
        (8, r"10 · Hydrated and anhydrous compounds"),
        (11, r"11 · Combustion analysis"),
        (14, r"12 · Chemical formulae and equations"),
        (16, r"Earlier skills · combining masses, reacting masses, equations"),
    ],
    "figs": {13: ("fig-q13-structures.png", 0.92)},
    "qs": {
        1: r"""What is the empirical formula of butanoic acid?
\optrow{\ce{C2H4O}}{\ce{C3H6O}}{\ce{C4H8O}}{\ce{C5H10O}}""",
        2: r"""Compound X consists of 40.0\% carbon, 6.7\% hydrogen and 53.3\% oxygen by mass.

What is the empirical formula of compound X?
\optrow{\ce{CH2O}}{\ce{C2H2O}}{\ce{C2H4O}}{\ce{CHO}}""",
        3: r"""Compound X is an organic compound that contains 30.6\% carbon, 3.8\% hydrogen, 20.4\% oxygen and 45.2\% chlorine by mass.

What is the empirical formula of X?
\optrow{\ce{C2H3OCl}}{\ce{C2H4OCl}}{\ce{C3H4OCl}}{\ce{C4H3O2Cl2}}""",
        4: r"""R is an oxide of Period 3 element T. 5.00\,g of R contains 2.50\,g of T.

What is T?
\optlist{magnesium}{aluminium}{silicon}{sulfur}""",
        5: r"""Compound X is a straight chain hydrocarbon with an $M_\mathrm{r}$ of 84.

What can be determined about X?
\begin{enumerate}[label=\textbf{\arabic*.}, leftmargin=1.6em]
\item empirical formula
\item molecular formula
\item whether X contains a \ce{C=C} bond or not
\end{enumerate}
The responses \textbf{A} to \textbf{D} should be selected on the basis of

{\centering
{\small
\begin{tabular}{cccc}
\toprule
\textbf{A} & \textbf{B} & \textbf{C} & \textbf{D} \\
\midrule
1, 2 and 3 are correct & 1 and 2 only are correct & 2 and 3 only are correct & 1 only is correct \\
\bottomrule
\end{tabular}}\par}

{\small No other combination of statements is used as a correct response.}""",
        6: r"""An aqueous solution contains 4.00\,g of a carboxylic acid, Q. When this solution reacts with an excess of magnesium, 380\,cm$^3$ of gas is produced, measured at s.t.p.

What is the relative formula mass of Q?
\optrow{59}{118}{126}{236}""",
        7: r"""P is a compound that burns in an excess of oxygen to give carbon dioxide and water only.

2.20\,g of P contains 1.20\,g of carbon and 0.20\,g of hydrogen.

When P is added to a solution of sodium carbonate, bubbles of gas are seen.

What is P?
\optlist{\ce{CH3CHO}}{\ce{CH3CO2H}}{\ce{CH3COCH2CH2OH}}{\ce{CH3CH2CH2CO2H}}""",
        8: r"""A sample of 35.6\,g of hydrated sodium carbonate contains 25.84\% sodium ions by mass.

When this sample is heated, anhydrous sodium carbonate and water are formed.

Which mass of water is given off?
\optrow{7.2\,g}{10.6\,g}{14.4\,g}{21.2\,g}""",
        9: r"""Hydrated cobalt(II) sulfate loses water when heated to give anhydrous cobalt(II) sulfate. All the water of crystallisation is lost to the atmosphere as steam.

When 3.10\,g of hydrated cobalt(II) sulfate, \ce{CoSO4.xH2O}, is heated to constant mass the \textbf{loss} in mass is 1.39\,g.

What is the value of $x$, to the nearest whole number?
\optrow{4}{6}{7}{11}""",
        10: r"""An experiment is carried out to determine the value of $x$ in hydrated lithium hydroxide, \ce{LiOH.xH2O}. A sample of the solid is heated in a crucible over a Bunsen flame.

Complete dehydration takes place; decomposition does \textbf{not} occur.
\begin{align*}
\text{mass of empty crucible\,/\,g} &= Q\\
\text{mass of crucible with \ce{LiOH.xH2O}\,/\,g} &= R\\
\text{mass of crucible and residue after heating\,/\,g} &= S
\end{align*}
Which equation gives the correct value of $x$?
\optlist{$\dfrac{S-R}{18}$}{$\dfrac{R-S}{18}$}{$\dfrac{23.9(R-S)}{18(S-Q)}$}{$\dfrac{23.9(S-R)}{18(S-Q)}$}""",
        11: r"""Compound X contains the elements C, H and O only.

2.00\,g of X produces 4.00\,g of carbon dioxide and 1.63\,g of water when completely combusted.

What is the empirical formula of X?
\optrow{\ce{CHO2}}{\ce{C2H2O}}{\ce{C2H4O}}{\ce{CH2O2}}""",
        12: r"""Substance Q is a hydrocarbon. When 1.00\,g of Q is completely burned, 3.22\,g of carbon dioxide is produced.

What could be the identity of Q?
\optlist{cyclohexene}{cyclopentane}{ethene}{pentane}""",
        13: r"""When a small sample of hydrocarbon Q is completely combusted, it produces 3.52\,g of carbon dioxide and 1.44\,g of water.

What could be the structure of hydrocarbon Q?
\qfig[0.78]{fig-q13-structures.png}""",
        14: r"""Which pair of formulae is correct?
\optlist{\ce{Ag2CO3} and \ce{(NH4)3NO3}}{\ce{K2HCO3} and \ce{Zn3(PO4)2}}{\ce{AgHCO3} and \ce{K3PO4}}{\ce{ZnCO3} and \ce{(NH4)2PO4}}""",
        15: r"""Chlorine dioxide, \ce{ClO2}, reacts with aqueous sodium hydroxide to produce water and a mixture of two sodium salts, \ce{NaClO2} and \ce{NaClO3}.

What is the mole ratio of \ce{NaClO2} to \ce{NaClO3} in the product mixture?
\optrow{1:2}{3:5}{1:1}{5:3}""",
        16: r"""Originally, chemists thought indium oxide had the formula \ce{InO}. By experiment they showed that 4.8\,g of indium combined with 1.0\,g of oxygen to produce 5.8\,g of indium oxide. The $A_\mathrm{r}$ of oxygen was known to be 16.

Which value for the $A_\mathrm{r}$ of indium is calculated using these data?
\optrow{38}{77}{115}{154}""",
        17: r"""A 4.00\,g sample of an anhydrous Group 2 metal nitrate, Z, is heated strongly until there is no further change of mass. A solid residue of mass 1.37\,g is formed.

Which metal is present in Z?
\optlist{barium}{calcium}{magnesium}{strontium}""",
        18: r"""Copper dissolves in dilute nitric acid producing a blue solution of \ce{Cu(NO3)2}, water and nitrogen(II) oxide as the only products.

How many moles of acid react with three moles of copper in the balanced equation?
\optrow{2}{4}{6}{8}""",
    },
}

HW[4] = {
    "slug": "2-stoichiometry-homework-4",
    "title": "AS stoichiometry homework 4 · solutions and gas volumes",
    "n": 16,
    "topics": r"Topics: 13 solutions and concentration · 14 gas volumes at room conditions. Later questions also use earlier skills (mole, empirical formula, hydrates, limiting reagent).",
    "extra": r" For gas volumes, use $24\,\mathrm{dm^3\,mol^{-1}}$ at room conditions (not $pV=nRT$), unless a question gives other conditions.",
    "sections": [
        (1, r"13 · Solutions and concentration"),
        (7, r"14 · Gas volumes at room conditions"),
        (13, r"Earlier skills · mole, empirical, hydrate, limiting"),
    ],
    "figs": {12: ("fig-q12-structures.png", 0.88), 14: ("fig-q14-hexamine.png", 0.32)},
    "qs": {
        1: r"""Sample X is added to water and made up to a total volume of 200\,cm$^3$. This gives a solution of 0.100\,mol\,dm$^{-3}$ \ce{HCl}.

What is X?
\optlist{10\,cm$^3$ of 1.00\,mol\,dm$^{-3}$ \ce{HCl}}{30\,cm$^3$ of 0.90\,mol\,dm$^{-3}$ \ce{HCl}}{50\,cm$^3$ of 0.40\,mol\,dm$^{-3}$ \ce{HCl}}{100\,cm$^3$ of 0.30\,mol\,dm$^{-3}$ \ce{HCl}}""",
        2: r"""Which mixture will react to form exactly one mole of water?

{\centering
{\small
\begin{tabular}{c cc}
\toprule
 & volume 2.00\,mol\,dm$^{-3}$ \ce{H2SO4}\,/\,cm$^3$ & volume 1.00\,mol\,dm$^{-3}$ \ce{NaOH}\,/\,cm$^3$ \\
\midrule
\textbf{A} & 250 & 500 \\
\textbf{B} & 250 & 1000 \\
\textbf{C} & 500 & 500 \\
\textbf{D} & 500 & 1000 \\
\bottomrule
\end{tabular}}\par}""",
        3: r"""Citric acid is found in lemon juice.
\begin{center}citric acid\\[0.15em]\ce{HO2CCH2C(OH)(CO2H)CH2CO2H}\end{center}
Which volume of 0.40\,mol\,dm$^{-3}$ sodium hydroxide solution is required to neutralise a solution containing 0.0050\,mol of citric acid?
\optrow{12.5\,cm$^3$}{25.0\,cm$^3$}{37.5\,cm$^3$}{50.0\,cm$^3$}""",
        4: r"""Hydrogen peroxide, \ce{H2O2}, decomposes into water and oxygen when a suitable catalyst is added.

20.0\,cm$^3$ of aqueous hydrogen peroxide decomposes to produce 600\,cm$^3$ of oxygen at room conditions.

What is the concentration of the aqueous hydrogen peroxide?
\optlist{5.00\,mol\,dm$^{-3}$}{2.50\,mol\,dm$^{-3}$}{1.25\,mol\,dm$^{-3}$}{0.625\,mol\,dm$^{-3}$}""",
        5: r"""A washing powder contains sodium hydrogencarbonate, \ce{NaHCO3}, as one of the ingredients.

In a titration, a solution containing 1.00\,g of this washing powder requires 7.15\,cm$^3$ of 0.100\,mol\,dm$^{-3}$ sulfuric acid for complete reaction. The sodium hydrogencarbonate is the only ingredient that reacts with the acid.

What is the percentage by mass of sodium hydrogencarbonate in the washing powder?
\optrow{3.0\%}{6.0\%}{12.0\%}{24.0\%}""",
        6: r"""The juice of one lemon reacts completely with 120\,cm$^3$ of 0.50\,mol\,dm$^{-3}$ sodium carbonate solution.

The formula of citric acid is \ce{HOOCCH2C(OH)(COOH)CH2COOH}.

No sodium carbonate is left unreacted.

What is the amount of citric acid in one lemon assuming that it is the only acid in the sample?
\optrow{0.02\,mol}{0.04\,mol}{0.06\,mol}{0.09\,mol}""",
        7: r"""A sample of propane, \ce{C3H8}, with a mass of 9.61\,g is completely combusted in an excess of oxygen under room conditions.

Which volume of carbon dioxide gas is produced?
\optrow{4.89\,dm$^3$}{5.24\,dm$^3$}{14.7\,dm$^3$}{15.7\,dm$^3$}""",
        8: r"""A mixture of 10\,cm$^3$ of methane and 10\,cm$^3$ of ethane was sparked with an excess of oxygen. After cooling, the residual gas was passed through aqueous potassium hydroxide.

All gas volumes were measured at the same temperature and pressure.

Which volume of gas was absorbed by the alkali?
\optrow{15\,cm$^3$}{20\,cm$^3$}{30\,cm$^3$}{40\,cm$^3$}""",
        9: r"""In an experiment, 0.100\,mol of propan-1-ol is burnt completely in 12.0\,dm$^3$ of oxygen, measured at room conditions.

What is the final volume of gas, measured at room conditions?
\optrow{7.20\,dm$^3$}{8.40\,dm$^3$}{16.80\,dm$^3$}{18.00\,dm$^3$}""",
        10: r"""What is the total volume of gas produced, measured at room conditions, when 0.010\,mol of anhydrous magnesium nitrate is completely decomposed by heating?
\optrow{240\,cm$^3$}{480\,cm$^3$}{600\,cm$^3$}{720\,cm$^3$}""",
        11: r"""The carbonate of an s-block element is reacted with an excess of hydrochloric acid.

0.833\,g of the carbonate releases 200\,cm$^3$ of gas, measured under room conditions.

What is the identity of the metal carbonate?
\optrow{\ce{Na2CO3}}{\ce{K2CO3}}{\ce{MgCO3}}{\ce{CaCO3}}""",
        12: r"""When 0.010\,mol of a hydrocarbon X reacts with 720\,cm$^3$ of hydrogen at room conditions, an alkane is formed.

What is hydrocarbon X?
\qfig[0.72]{fig-q12-structures.png}""",
        13: r"""How many molecules are present in 62\,g of solid white phosphorus, \ce{P4}?
\optrow{$L$}{$2L$}{$\dfrac{L}{2}$}{$\dfrac{L}{4}$}""",
        14: r"""Hexamine is a crystalline solid used as a fuel in portable stoves.

The diagram shows its skeletal structure.
\qfig[0.28]{fig-q14-hexamine.png}
What is the empirical formula of hexamine?
\optrow{\ce{CH2N}}{\ce{C3H6N2}}{\ce{C4H8N4}}{\ce{C6H12N4}}""",
        15: r"""Barium dithionate, \ce{BaS2O6.2H2O}, is soluble in water.

\ce{S2O6^2-} ions slowly decompose in acidic solution.
\[\ce{S2O6^{2-}(aq) -> SO2(g) + SO4^{2-}(aq)}\]
3.513\,g of \ce{BaS2O6.2H2O} is dissolved in water in a 100\,cm$^3$ volumetric flask and the solution made up to the mark with \ce{HCl(aq)}.

At time $x$\,min, a white precipitate of mass 0.661\,g is present in the flask.

What is the concentration of \ce{BaS2O6} in the volumetric flask at time $x$\,min?
\optrow{0.0077\,mol\,dm$^{-3}$}{0.0090\,mol\,dm$^{-3}$}{0.077\,mol\,dm$^{-3}$}{0.090\,mol\,dm$^{-3}$}""",
        16: r"""An excess of chlorine was bubbled into 100\,cm$^3$ of hot 6.0\,mol\,dm$^{-3}$ sodium hydroxide.

How many moles of sodium chloride would be produced in the reaction?
\optrow{0.30}{0.50}{0.60}{0.72}""",
    },
}


def write_manifest(hw: dict) -> Path:
    slug = hw["slug"]
    root = PRINT / slug
    md = QLS / f"{slug}.md"
    items = [
        {
            "id": "H01",
            "type": "heading",
            "source_loc": "title",
            "keep": True,
            "render": "latex",
            "duplicate_of": None,
            "reason": "first occurrence",
            "text": hw["title"],
        },
        {
            "id": "I01",
            "type": "instruction",
            "source_loc": "instructions",
            "keep": True,
            "render": "latex",
            "duplicate_of": None,
            "reason": "first occurrence",
            "text": "Circle one letter A-D. Show working.",
        },
    ]
    for n, title in hw["sections"]:
        items.append(
            {
                "id": f"S{n:02d}",
                "type": "heading",
                "source_loc": f"section-{n}",
                "keep": True,
                "render": "latex",
                "duplicate_of": None,
                "reason": "first occurrence",
                "text": title,
            }
        )
    for n in range(1, hw["n"] + 1):
        qid = f"Q{n:02d}"
        items.append(
            {
                "id": qid,
                "type": "mcq",
                "source_loc": qid,
                "keep": True,
                "render": "latex",
                "duplicate_of": None,
                "reason": "first occurrence",
                "marks": 1,
                "text": hw["qs"][n],
            }
        )
        if n in hw["figs"]:
            fn, _ = hw["figs"][n]
            items.append(
                {
                    "id": f"Fig-{qid}",
                    "type": "figure",
                    "source_loc": f"{qid}-diagram",
                    "keep": True,
                    "render": "image",
                    "duplicate_of": None,
                    "reason": "graph / diagram / visual options — do not redraw",
                    "image": f"overleaf/images/{fn}",
                }
            )
        items.append(
            {
                "id": f"CLIP-{qid}",
                "type": "mcq",
                "source_loc": f"{qid}-paper-clip",
                "keep": False,
                "render": "image",
                "duplicate_of": qid,
                "reason": "full paper-clip of typeset question",
                "image": f"images/img-{n:03d}.png",
            }
        )
    data = {
        "meta": {
            "source": str(md),
            "title": hw["title"],
            "syllabus": "9701",
            "student_answers": False,
            "language": "en",
        },
        "items": items,
    }
    path = root / "content-manifest.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    n_drop = sum(1 for it in items if not it["keep"])
    audit = root / "dedup-audit.md"
    audit.write_text(
        "| Dropped ID | Why | Kept ID |\n|---|---|---|\n"
        + "\n".join(
            f"| {it['id']} | {it['reason']} | {it.get('duplicate_of') or ''} |"
            for it in items
            if not it["keep"]
        )
        + f"\n\nkept {sum(1 for it in items if it['keep'])} unique items; dropped {n_drop} duplicates; student-no-answers 0.\n",
        encoding="utf-8",
    )
    return path


def write_tex(hw: dict) -> Path:
    ov = PRINT / hw["slug"] / "overleaf"
    ov.mkdir(parents=True, exist_ok=True)
    (ov / "images").mkdir(exist_ok=True)
    body = [header(hw["title"], hw["n"], hw["topics"], hw["extra"])]
    sec = dict(hw["sections"])
    for n in range(1, hw["n"] + 1):
        head = f"\\qhead{{{sec[n]}}}\n" if n in sec else ""
        body.append(
            "\\noindent\\begin{minipage}{\\linewidth}\n"
            f"{head}\\mcq{{{n}}}%\n{hw['qs'][n]}\n\\mcqend\n"
            "\\end{minipage}\\vspace{0.16em}\n"
        )
    body.append("\\end{document}\n")
    tex = PREAMBLE + EXTRA + "\n".join(body)
    path = ov / "main.tex"
    path.write_text(tex, encoding="utf-8")
    return path


def compile_tex(ov: Path) -> None:
    cmd = [str(XELATEX), "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    for _ in range(2):
        r = subprocess.run(cmd, cwd=ov, capture_output=True, text=True)
        if r.returncode != 0:
            log = ov / "main.log"
            tail = log.read_text(errors="replace")[-2500:] if log.exists() else r.stderr[-2500:]
            raise SystemExit(f"XeLaTeX failed in {ov}\n{tail}")


def leak_check(ov: Path) -> None:
    tex = (ov / "main.tex").read_text(encoding="utf-8")
    bad = ("答案区", "Answer Key", "Mark Scheme", "ms_answer", "-ms.png", "教师版", "参考答案")
    hits = [s for s in bad if s.lower() in tex.lower() or s in tex]
    # Chinese leftover in wrapper (not in ce formulae)
    if "第" in tex or "选择题" in tex:
        hits.append("Chinese wrapper")
    if hits:
        raise SystemExit(f"leak in {ov}: {hits}")


def main() -> None:
    for n, hw in HW.items():
        print(f"== HW{n} ==")
        man = write_manifest(hw)
        r = subprocess.run(["python3", str(VALIDATE), "--in", str(man)], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode != 0:
            raise SystemExit(f"manifest fail HW{n}")
        write_tex(hw)
        compile_tex(PRINT / hw["slug"] / "overleaf")
        leak_check(PRINT / hw["slug"] / "overleaf")
        pdf = PRINT / hw["slug"] / "overleaf" / "main.pdf"
        dest = QLS / f"{hw['slug']}.pdf"
        shutil.copy2(pdf, dest)
        print("PDF", dest, "size", dest.stat().st_size)


if __name__ == "__main__":
    main()
