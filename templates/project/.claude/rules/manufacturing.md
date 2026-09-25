---
paths:
  - "mfg/**"
  - "bom/**"
---

# Manufacturing

- Process selection (FDM, SLA, SLS, injection molding, CNC, sheet metal, cast) is stated explicitly with the DFM rule set that applies -- `docs/standards/manufacturing.md` cites the source (R5c/R5d), never invented figures (advisory -- `checking-dfm`'s verify entrypoint checks the numbers against the cited rule table, but not that a human-written doc cites its source).
- DFM checks (wall minimums, draft, ribs/bosses, radii, tolerances) are process-specific; a value valid for FDM is not valid for injection molding. Cite the process before citing the rule.
- `checking-dfm`'s verify entrypoint runs per-process rule tables: `forge-python skills/checking-dfm/scripts/verify.py --project . --changed cad/,mfg/ --fast`.
- BOM entries (`bom/`) carry MPNs, alternates, lifecycle status and lead time; flag single-source parts. Cost roll-ups state the volume tier they assume (`costing-bom`'s verify entrypoint, check_id `supply.bom_rollup`, checks every line is priced).
- Tooling implications and fixtures are stated with the process, not assumed generic (advisory -- no automated check reads fixture/tooling prose).
- Any commitment to a vendor, quote or fab order needs a human sign-off (`permissions.ask`) -- Claude recommends, never commits spend (enforced by `permissions.ask`, CONTRACTS §8).
