# FORGE — Claude Code Product-Engineering Operating System (owner's brief)

> The owner's original brief (September 2026), stored so builder agents work from the exact spec. **Where this brief and `docs/decisions/ADR-001-forge-architecture.md` disagree, the ADR wins.** It records verified platform facts and owner-approved deviations (ADR-001 §15).

Turn this machine's Claude Code into a world-class product-engineering organisation: systems, industrial design, mechanical, electrical, embedded, software, simulation, manufacturing, test and compliance. Output quality must match the engineering discipline of top hardware companies. That quality comes from process, not vibes. Every claim is backed by evidence, every design is checked by something that can fail, and nothing ships without an independent review and, where it matters, a human signature. Package everything as a reusable Claude Code plugin called forge, served from a local marketplace in this repo, and prove it works with an eval suite that compares Claude-with-Forge against plain Claude Code.

## 0. Operating principles

- **Verification is the product.** Work is done only when a check that can fail has passed, and the evidence is saved. A test that cannot fail proves nothing: prove every new check fails on a deliberately wrong input.
- **The maker is never the checker.** The agent that builds is never the one that judges. Reviewers run in fresh contexts with read-only tools and calibrated rubrics, because models overrate their own work.
- **Numbers beat pictures, and pictures beat nothing.** CAD that compiles and looks right can still have wrong dimensions or design intent. Every geometric requirement gets a numeric check; renders are a second layer, never the only one.
- **Build in small, measured steps.** Model a feature, measure it, render it, compare, snapshot. Never write a whole part, board or module blind.
- **Design artifacts are code.** CAD in build123d, circuits as code compiling to KiCad (ADR: tscircuit, not atopile), systems models in SysML v2 textual notation, firmware as code, requirements in plain-text files. Everything is diffable, testable, reviewable and reproducible. GUI tools are for inspection, drawings and last-resort operations.
- **Mechanisms beat prompts.** Rules that matter become hooks, linters, tests or permissions. Push each check to the fastest layer that can hold it: hook (ms), then pre-commit (s), then CI (min), then human review (h).
- **Context is the scarcest resource.** The root CLAUDE.md is a table of contents under 100 lines. Domain knowledge lives in path-scoped rules and skills that load only when relevant. Exploration happens in subagents.
- **Every failure becomes a permanent check.** Capture the root cause, add a mechanism that catches it next time, and add an eval case.
- **Physics in the loop.** Geometry is not function. Use analysis, FEA, circuit simulation, firmware simulation and HIL wherever a requirement is physical.
- **Humans sign safety, money and fabrication.** Anything that could hurt someone, cost real money, or goes to a fab or factory needs a human sign-off line. Nothing is ever called "production-ready" or "validated" without physical evidence.
- **Least privilege and supply-chain hygiene.** Vet, pin and sandbox third-party components; detect tool-definition changes after approval.
- **Measure the harness itself.** Forge must show a positive, measured improvement over plain Claude Code on realistic engineering tasks, or it gets fixed.

## 3. Build the forge plugin

`plugins/forge/` with a valid manifest, plus `.claude-plugin/marketplace.json` at the repo root so it installs with `/plugin`. Run `claude plugin validate` until clean.

### 3.1 Instruction files

- **User-scope `~/.claude/CLAUDE.md`:** already done (six Forge habit lines appended).
- **Project template `templates/project/CLAUDE.md`:** under 100 lines, written as a table of contents. It covers:
  - build, test and verify commands;
  - the current gate;
  - where requirements, params, evidence and decisions live;
  - pointers to rules and skills.
  
  It never contains encyclopedic content.
- **Path-scoped rules in `.claude/rules/`:** each has `paths:` globs, is short and imperative, and links to deeper standards docs.

| Rule | Loads for |
|---|---|
| `mechanical.md` | `cad/**` |
| `electrical.md` | `ecad/`, `circuits/` |
| `firmware.md` | `firmware/**` |
| `software.md` | `app/`, `services/` |
| `systems.md` | `requirements/`, `model/` |
| `simulation.md` | `analysis/**` |
| `manufacturing.md` | `mfg/`, `bom/` |
| `compliance.md` | `compliance/**` |

### 3.2 Subagents (`plugins/forge/agents/`)

Every agent gets:
- a sharp description with trigger phrases;
- least-privilege tools;
- a model choice (fast/mid-tier for bulk production, strongest for reviewers);
- `memory: project` (**ADR deviation: judges get no memory**);
- a short system prompt: role, standards to apply, required output schema, what to refuse.

Reviewers are read-only and never edit.

| Agent | Role |
|---|---|
| product-manager | Fuzzy idea → user needs, jobs-to-be-done, success metrics, scope. Interviews the owner with AskUserQuestion. |
| systems-engineer | Requirements in EARS with IDs, rationale and verification method (inspection, analysis, demo, test). Interfaces. Budgets (power, mass, thermal, cost, link). SysML v2 textual model. The traceability graph. |
| industrial-designer | Form, colour/material/finish, ergonomics, visual language across a family: one radius family, planned parting lines and seams, no gratuitous features. |
| ux-designer | Software and on-device UI, accessibility (WCAG 2.2), flows. Uses the frontend-design and design skills. |
| mechanical-engineer | The only author of `cad/`. Stepwise build123d through the MCP. Parametric; params from one source of truth. Assemblies, fasteners, snap-fits with strain calculations, tolerance stacks, GD&T intent. |
| manufacturing-engineer | Process selection (FDM, SLA, SLS, injection molding, CNC, sheet metal, cast), DFM/DFA, cost drivers, tooling implications, fixtures. |
| electrical-engineer | Architecture, power tree, component selection with lifecycle status, schematics as code, KiCad layout guidance, ngspice simulations, ERC/DRC, EMC pre-compliance thinking. |
| embedded-engineer | Firmware architecture, drivers, RTOS, boot/OTA security, power states, unit tests, static analysis, simulation (Renode/QEMU/Wokwi), HIL through bounded tools only. |
| software-architect | Apps, cloud and APIs, data, security, observability. Delegates software sprints to gstack if installed. |
| simulation-engineer | FEA, thermal, CFD, circuit simulation. Always does a hand-calc sanity check and a mesh/step convergence check, and states assumptions and validity limits. |
| rf-emc-engineer | Antennas, keep-outs, radomes/windows, coexistence, EMC risk, the certification path. |
| test-engineer | V&V plan: every requirement mapped to a test; fixtures; acceptance criteria; HIL plans. |
| safety-compliance-engineer | Hazard analysis (STPA), DFMEA/PFMEA, standards map, claims review (no accidental medical/safety claims), privacy and security by design. |
| supply-chain-engineer | BOM with MPNs, alternates, lifecycle and lead time, cost roll-ups at volume tiers. Flags single-source risks. |
| verification-evaluator (read-only, strongest model) | Skeptical judge that grades work against requirements and rubrics using the evidence, and tries to refute. Reports only defects that affect requirements, safety, fit, function, manufacturability or cost; style notes are optional. Output: a structured verdict (PASS/FAIL/BLOCKED per criterion, with evidence links). |
| red-team (read-only, strongest model) | Pre-mortem: "it's a year later and this failed; why?" Attacks assumptions, edge cases, misuse, supply shocks. |

### 3.3 Skills (`plugins/forge/skills/<name>/SKILL.md`)

**Authoring rules:**
- Gerund names.
- Trigger-rich descriptions, including cases where the skill should not fire.
- SKILL.md under 500 lines, with details in `references/`.
- Deterministic work done by `scripts/`.
- Non-negotiable rules in the first lines.
- `context: fork` for heavy reviews.
- `disable-model-invocation: true` for anything with side effects (release, fab export, flashing hardware).

**Discovery and systems**
- **interviewing-stakeholders:** produces SPEC.md.
- **writing-requirements:** EARS plus verification methods, with a lint script.
- **modeling-systems:** SysML v2 textual, validated by the parser.
- **tracing-requirements:** builds the requirement → design element → test → evidence graph; fails on orphans or untested requirements.
- **writing-adrs.**

**Design exploration**
- **exploring-concepts:** a dynamic workflow generates at least N concepts in parallel. Independent judges score them against a weighted Pugh matrix, and a tournament produces the top 2. ASK the owner to choose.

**Mechanical**
- **intaking-datasheets:** turns datasheets into params with page references. Where the datasheet is silent, writes caliper-measurement procedures.
- **modeling-cad-parts:** stepwise build123d, with snapshots before risky boolean/fillet operations.
- **verifying-geometry:** a scripted numeric suite. It covers:
  - solid validity and watertight exports;
  - bounding box and volume ranges;
  - minimum wall thickness by process;
  - clearances and interference in assemblies;
  - draft on molded faces and minimum radii;
  - hole-to-edge distances and boss/rib ratios;
  - mass properties.
- **inspecting-renders:** CADCodeVerify style. Before looking at any render, write 10–20 yes/no validation questions from the requirements. Render standard views, sections and exploded views. Answer each question with evidence, and list every deviation.
- **checking-dfm:** per process, with rule tables sourced from R5.
- **stacking-tolerances:** worst-case and RSS, with GD&T intent per ASME Y14.5.
- **drafting-drawings:** FreeCAD TechDraw PDFs with critical dimensions and tolerances (ADR: headless DXF → scripted PDF).
- **rendering-products:** an engineering render pack, plus optional Blender marketing renders.

**Simulation**
- **running-fea:** gmsh + CalculiX, with boundary conditions stated, a hand-calc cross-check, a convergence study, safety factors, and limits stated honestly.

**Electrical and embedded**
- **designing-circuits:** circuits-as-code → KiCad, plus ngspice for critical nets.
- **checking-ecad:** kicad-cli ERC/DRC plus the fab house's DFM rules; human sign-off before fabrication.
- **building-firmware:** build, static analysis, unit tests, simulation, size and timing budgets.
- **testing-on-hardware:** HIL through bounded tools only. Every test is also run once against a wrong expectation to prove it can fail.

**Safety, compliance and supply chain**
- **analyzing-risk:** STPA plus DFMEA, with S/O/D and action tracking.
- **mapping-compliance:** product profile → applicable standards → test plan → pre-scan plan.
- **costing-bom.**

**Reviews and release**
- **reviewing-designs:** the gate review. It runs verification-evaluator, red-team and the relevant specialists in parallel, each in a fresh context, then reconciles into `reviews/Gx.md` with a blank human sign-off line.
- **releasing-designs:** a versioned bundle containing:
  - STEP, STL and drawings;
  - Gerbers and fab outputs;
  - the BOM;
  - firmware binaries with hashes;
  - test reports and the evidence manifest;
  - the changelog and git SHA.

**Harness upkeep**
- **capturing-failures:** failure → root cause → new rule, hook, check or eval → prove it catches the original failure.
- **gardening-docs:** finds stale docs, broken links, outdated versions and rules no one follows; proposes small fixes.

### 3.4 Hooks (in the plugin)

- **SessionStart:** print the gate, failing checks, open assumptions and review findings, and any tool-definition drift from `forge doctor --quick`.
- **UserPromptSubmit** (optional, lightweight): suggest relevant skills.
- **PreToolUse guardrails:**
  - block destructive shell commands outside `out/`, and block force-push;
  - block writes to `release/`, to params marked verified, to `security/`, and to HIL bench config;
  - require a sourced justification to change any verified value;
  - block network access to non-allowlisted domains.
- **PostToolUse:** fast, path-dispatched checks, each under 30 s, feeding a short failure summary back with the blocking exit code.
  - `cad/` → build the changed part, validity check, params lint
  - `ecad/` → ERC
  - `firmware/` → compile
  - `requirements/` → EARS lint and trace check
  - `docs/` → link check
- **Stop:** the evidence gate. If any domain changed since the last green run, require a fresh `evidence/manifest.json` entry for that change (checks run, results, tool versions, git SHA); otherwise block with a clear summary. Handle the block limit gracefully.
- **SubagentStop:** reviewers must return the verdict schema; free-form output is rejected.
- **PreCompact:** write a state snapshot (modified files, open findings, current gate, failing checks).

### 3.5 Dynamic workflows (`plugins/forge/workflows/`)

- **concept-tournament:** parallel concepts, independent judges, pairwise comparison, top-2 report.
- **gate-review:** parallel specialist reviews, then reconciliation, then an evidence-linked report.
- **standards-research:** multi-source research with cross-checking and citations.
- **regression-sweep:** rebuild and re-verify everything, with a diff against the last green run.

### 3.6 Output style and model strategy

**Output style `engineering-report`:**
- lead with evidence;
- units on every number;
- explicit assumptions and confidence levels;
- "what would change my mind";
- no marketing language;
- keep the coding instructions active.

**Models:**
- The advisor uses Opus.
- Cheaper models do bulk generation and concrete-rubric eval judging.
- The ADR documents how cost scales.

### 3.7 Evidence and credibility model

L0 claimed; L1 computed/measured in CAD; L2 simulated with sanity checks; L3 independently reviewed; L4 physically tested with data; L5 certified by an accredited body or qualified human engineer. Reports state each claim's level. Nothing below L4 is called "validated"; nothing below L5 "certified" or "production-ready".

## 4. Project template and gates (`templates/project/`)

**`/forge:new-project` scaffolds:**
- the TOC CLAUDE.md, rules and params;
- the directories: `requirements/`, `model/`, `cad/`, `ecad/`, `firmware/`, `app/`, `analysis/`, `mfg/`, `bom/`, `compliance/`, `tests/`, `evidence/`, `reviews/`, `docs/decisions/`, `release/`;
- ASSUMPTIONS.md, RISKS.md, a Makefile and CI config.

**Stage gates** (`docs/standards/gates.md`):

| Gate | Name | What passes it |
|---|---|---|
| G0 | Discovery & requirements freeze | Every requirement has a verification method; interfaces and budgets drafted |
| G1 | Concept / PDR | Concept tournament done; architecture chosen; top risks with mitigations |
| G2 | Detailed design / CDR | All automated checks green; DFMEA done; tolerance stacks and key simulations done |
| G3 | EVT | Prototypes built and measured; params updated from measurements; assumptions retired |
| G4 | DVT | Every requirement verified at L4; compliance pre-scans; reliability tests |
| G5 | PVT | Pilot production, yield and process capability, fixtures, final BOM and cost |
| G6 | Launch | Release bundle and certifications |

Each gate record contains: criteria, evidence links, the evaluator verdict, red-team findings, open risks, and a human sign-off line. Claude may recommend; only a human passes a gate.

## 5. The verification ladder (every domain)

Syntax → build → validity → numeric requirement checks → physics (analysis, simulation, HIL) → visual inspection (question-first) → independent evaluator → red-team → human → physical test. Each rung is a script or skill with a pass/fail result, and each result lands in the evidence manifest. `make verify` runs every automatable rung. For long unattended runs, use `/goal` with a verifiable condition and an explicit bound.

## 6. Eval suite (`plugins/forge/evals/`, `claude plugin eval`)

25+ cases, each with graders on outcome and path.

**Mechanical** (e.g. a parametric dev-board enclosure with USB access and a snap-fit lid; a bracket with loads and holes; a gear pair to a module and ratio). Graders:
- a STEP file exists;
- a regex over the measurement report checks walls, clearances and holes;
- an llm grader judges render PNGs against a concrete rubric;
- `tool_used` confirms the skills fired.

**Electrical** (e.g. a 3.3 V regulator from 5 V with load and protection). Graders: ERC passes (written to a file), and a simulation result is within spec.

**Firmware** (a debounced input with a state machine and unit tests for a common MCU target). Graders: the build passes, the tests pass, and the tests fail on a mutated implementation.

**Requirements** (a messy brief → EARS with verification methods). Graders: the lint passes, and the trace has no orphans.

**Seeded-defect review** (the key test). Designs with 5–10 planted defects each:
- a wall below the process minimum;
- a hidden interference;
- a missing strain relief;
- a tolerance-stack failure;
- a wrong regulator dissipation;
- a missing ESD path;
- an untested requirement;
- an unsupported claim.

Measure recall and precision. Target recall ≥ 0.8.

**Refusal and discipline:**
- a push to skip verification: refuse or stop;
- an impossible requirement: flag it and ask;
- a request to mark a gate as passed: decline.

**Running:**
- ≥ 3 runs per case, with the no-plugin baseline (Δ);
- report pass@k and pass^k;
- pin the agent and judge models;
- set a cost ceiling;
- a CI job gates Forge changes on the score;
- save `evals/BASELINE.md`.

Forge ships only when the mean Δ is clearly positive and seeded-defect recall meets the target. Never tune graders to make scores look good; read the transcripts.

## 7. Self-improvement loops

- **Failure capture:** every defect caught goes through capturing-failures, plus an eval case.
- **Weekly routine** (ASK before enabling anything recurring):
  - forge doctor plus the drift check;
  - gardening-docs;
  - re-verify tool versions and the What's-new digest;
  - re-run the evals;
  - propose a small PR.
- **After any model change:** re-run the evals.
- **Harness simplification:** remove components that show no Δ.

## 8. Acceptance

- `forge doctor` plus `claude plugin validate`, and a list of every component.
- **Smoke project:** one generic mechanical part and one small circuit through the full pipeline to G2-level evidence, then archived as an example.
- **Eval summary table:** WITH, W/OUT, Δ, pass^k, recall and precision, and cost.
- **README:**
  - how to install;
  - how to start a new project;
  - how to run gates, evals and the weekly routine;
  - known limitations;
  - what always needs a human.
- **ASK:** what's proven, what's unproven, and the top 5 risks.
