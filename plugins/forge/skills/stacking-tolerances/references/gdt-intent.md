# GD&T intent notes

Reference: **ASME Y14.5-2018 (R2024)**, dimensioning and tolerancing (reaffirmed with ANSI approval 12 Nov 2024; a revision was in progress as of the last check but no newer edition had published -- `docs/research/R5a-standards-drawings-ipc-accessibility.md`). ISO users: **ISO 1101:2017** (geometric tolerance symbols and zones) plus **ISO 8015** (independency principle) and **ISO 14405-1** (linear-size modifiers). Cite the edition; never quote the standard's text (copyrighted) -- describe the rule in your own words and point the reader at the clause number.

## Translating a loop diagram into a stack file

1. Draw the 1-D loop: start and end at the two surfaces that define the gap, and list every dimension the loop crosses, in order.
2. Each dimension becomes one `[[contributor]]`. `direction` is +1 if walking the loop in that dimension's positive sense widens the gap, -1 if it narrows it.
3. A dimension controlled by a **feature-control frame** (position, profile, perpendicularity, ...) rather than a plain +/- tolerance contributes its **tolerance zone diameter or width**, not a linear +/-. For a position tolerance on a hole pattern feeding a fastener clearance stack, use the tolerance zone radius (half the stated value) as the contributor's `tol_plus`/`tol_minus`, and say so in `description`.
4. **Bonus tolerance** (MMC/LMC modifiers, Y14.5 rule 2.10-ish material condition modifiers): if a contributor's feature-control frame carries an MMC or LMC modifier, the *available* tolerance grows as the feature departs from its material-condition limit. A worst-case stack that ignores bonus tolerance is conservative (safe but pessimistic); state in the stack `description` whether bonus tolerance was credited, and if so, at what feature size.
5. **Datum reference frame order matters.** Two contributors that share a datum feature are not independent draws in the same way two contributors on unrelated datums are -- if a stack leans on that independence assumption (RSS, Monte Carlo), say so and flag it as an assumption in the stack description, not a silent default.

## When a stack fails

- **Worst-case fails:** the design is wrong at some combination of allowed part conditions. Either tighten a contributor's tolerance (cost), change a nominal, or change the architecture (e.g. add a compliant element, a shim, an adjustment).
- **RSS fails but worst-case passes:** statistically some fraction of assemblies will fall outside the requirement even though no single part is out of spec. This is a process-capability risk, not an automatic block -- decide with manufacturing-engineer whether the process Cpk covers it, or whether 100% inspection / selective assembly is needed.
- **Monte Carlo disagrees sharply with RSS:** usually means a contributor's distribution assumption (normal vs uniform) or asymmetry is not well modelled by the closed-form RSS decomposition. Trust the Monte Carlo sampled bound over the closed-form RSS in that case, and note why in the stack description.

## What a numeric stack does not cover

- Thermal expansion mismatches across the loop (add a temperature-dependent term as a separate contributor if the assembly sees a temperature range).
- Assembly-induced deflection (a loose part settling under its own weight or a fastener's clamp load) -- that is an FEA question (`running-fea`), not a rigid-body tolerance stack.
- Wear or creep over life -- state as an assumption/limit of validity, not silently ignored.
