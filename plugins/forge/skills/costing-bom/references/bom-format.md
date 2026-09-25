# BOM CSV format reference

## Columns

| Column | Required | Meaning |
|---|---|---|
| `ref_des` | yes | Reference designator(s), e.g. `R1`, `U3`, or `C1,C2,C3` for a ganged line. |
| `description` | yes | Human-readable part description. |
| `mpn` | yes | Manufacturer part number, exact. |
| `manufacturer` | yes | The MPN's manufacturer. |
| `qty_per_unit` | yes | Quantity consumed per assembled unit (not per BOM line count). |
| `lifecycle` | yes | `Active`, `NRND`, `EOL`, `Obsolete`, `Preview`, or a distributor-reported equivalent. |
| `lead_time_weeks` | yes | Current quoted lead time, in weeks. |
| `alternates` | yes (may be empty) | Semicolon-separated alternate MPNs. Empty = single-source. |
| `risk_note` | yes (may be empty) | Required non-empty whenever the line is single-source or non-Active. |
| `price_<qty>` | at least one | Unit price at that order quantity, in USD unless the project states otherwise. Any positive integer suffix is a valid tier. |

## Worked examples

**A well-covered single-source part** (passes):
```
U1,MCU,STM32F103C8T6,STMicro,1,NRND,26,,plan: migrate to STM32F103C8T7 by Q1 2027; owner J. Chen; qual due 2026-12-01,3.10,2.40,1.90
```
`alternates` is empty (single-source) and `lifecycle` is NRND (risk) — but `risk_note` states the mitigation, an owner and a date, so both flags are acknowledged and the line passes.

**An unacknowledged risk** (fails):
```
U2,Regulator,LM317T,TI,1,Active,8,,,0.55,0.40
```
No alternates and no `risk_note` — `single_source_acknowledged` fails with a remediation string naming the part and asking for either a real alternate or a mitigation note.

**A properly multi-sourced part** (passes, no note needed):
```
R1,10k resistor 0402,RC0402FR-0710KL,Yageo,2,Active,4,RC0402JR-0710KL;ERJ-2RKF1002X,,0.02,0.01,0.005
```

## Roll-up math

For each `price_<qty>` column present, the roll-up sums `price * qty_per_unit` across every line item that has a price in that column, giving the extended per-unit assembly cost at that order volume. Lines missing a price in a given tier column simply don't contribute to that tier's total (but a line with **no** price in *any* tier column fails `bom.all_lines_priced`).

## Choosing tiers

Pick tiers that match your actual quoting plan (e.g. prototype qty, first production run, steady-state volume) — `price_1`, `price_25`, `price_500`, `price_5000` is a perfectly valid set. The script infers tiers from whatever `price_<N>` columns exist; it does not require a fixed list.
