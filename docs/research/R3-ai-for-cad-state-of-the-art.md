# R3 — AI for CAD and engineering: research and state of the art

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: LLM/VLM-driven programmatic CAD (CadQuery / build123d / OpenSCAD / FreeCAD), its benchmarks, verification loops, physics-in-the-loop agents, and independent evidence on commercial text-to-CAD — read for what it implies for Forge (Claude Code + build123d).

Tagging: **[V]** = read in the primary source (paper PDF, repo README, leaderboard data file). **[R]** = secondary source only. **[U]** = unverified. Several [V] items in §§5–9 were read in the primary PDF by delegated sub-researchers under the same rules; I spot-checked a sample (CAD-Coder Table 2, DesignQA Table 2, and others noted inline) and they matched. All numbers are copied from the cited table or section. Quotes are ≤15 words.

## Summary

1. **CADCodeVerify is real (ICLR 2025, CADPrompt, 200 prompts), but its gains are modest.** [V]
   - Headline gains are measured against 3D-Premise, not against unrefined output.
   - Its VLM answers only 64.6–68.2% of its own verification questions correctly.
   - A numeric geometric-feedback baseline beat it on every GPT-4/Gemini setting.
2. **Valid, plausible CAD still fails on dimensions and intent in 2026.** This is spread across benchmarks, not one paper. [V]
   - BenchCAD: frontier models execute up to 94% but reach IoU ≤0.28.
   - RealCADBench: executability up to 0.93, surface IoU ≤0.22.
   - neuralCAD-Edit: GPT 5.2 validity 0.99 but expert acceptance 0.25.
   - Hephaestus-CCX: 0 strict FEA passes on first attempt.
3. **CADGenBench (a Hugging Face leaderboard, not a paper) and BenchCAD both exist.** [V]
   - CADGenBench scores drawing → STEP generation and editing behind a validity gate plus shape, interface and topology checks. Its reference agent writes build123d.
4. **Executable requirement tests are the best-evidenced lever.** [V]
   - CADTests: AUC vs human judgement 0.928, against 0.663 for Chamfer distance; the tests also improve generation.
   - Kernel-measurement loops work: CADSmith (median IoU 0.81 → 0.96), ReliCAD, CAD-Assistant.
5. **Execution-error feedback fixes validity (invalid rate → about 0) but not geometry.** Most refinement gain comes in round 1, and extra rounds can hurt. [V]
6. **Render/VLM critique is weak and inconsistent.** [V]
   - It helps structure on complex parts (CADSmith).
   - It adds nothing in CADTests and gives mixed results for Claude in the FEA study.
   - VLM judges inflate their own work: 0.53 self-rated vs 0.05 from human experts.
7. **Physics in the loop helps measurably but does not yet produce correct designs.** [V]
   - FEA vs no FEA: 59% vs 22% of designs in the safety-factor band.
   - FEA repair adds about +13 points of requirement pass per round.
   - Specific margins work better than pass/fail verdicts.
   - The best loop reaches only 9/50 strict passes.
8. **Clarifying the spec and stating explicit dimensions before generating gives large gains.** ProCAD: CD ×10³ 7.80 → 0.63; CADFS with a bounding box in the prompt: CD 0.58 → 0.14. [V]
9. **Commercial tools have no public benchmark results.** The independent tests are anecdotal (1–6 prompts, unmeasured). Common failure patterns: silent assumptions, feature omission, assembly errors. [V/R]
10. **Model upgrades outweigh harness changes, and dimensional accuracy is barely measured.** [V]
    - On CADGenBench, model generations moved scores by about 0.4, harness changes by about 0.05.
    - Most papers normalise scale away; only Pointer-CAD v2, CADSmith, CADTests and CADGenBench measure absolute geometry.

## Findings

### 1. CADCodeVerify (Alrashedy, Tambwekar et al., Georgia Tech; ICLR 2025)

- **Venue and identity.** arXiv [2410.05340](https://arxiv.org/abs/2410.05340) v2. The PDF header reads "Published as a conference paper at ICLR 2025". Code: `github.com/Kamel773/CAD_Code_Generation`. [V]
- **Method (§3)** [V]
  - *Generate:* a VLM writes CadQuery from the prompt, zero- or few-shot. Few-shot uses examples drawn from 40 CadQuery documentation snippets (App. B.4).
  - *Execute and repair:* if the code fails to compile, the compiler error is fed back until it runs or N attempts are used (Eq. 2).
  - *Refine:* the VLM writes 2–5 yes/no verification questions from the prompt. It answers them from 4 renders (0°/90°/180°/270°) using chain-of-thought, with "Unclear" allowed. The "No" answers become feedback for a code rewrite (Eq. 3–5). Refinement is capped at 2 rounds because "no improvement was observed beyond the second refinement" (App. B.3).
- **Benchmark: CADPrompt** [V]
  - 200 objects taken from the ABC-derived collection of Wu et al. 2021.
  - Each object has a hand-written natural-language prompt and expert CadQuery code (§4, Table 1).
  - Ground truth was validated in Blender.
  - Metrics: point-cloud distance, Hausdorff distance, IoGT (a bounding-box overlap) and compile rate. All are computed after ICP alignment and **normalisation to a unit cube**, so absolute dimensions are not scored (§5.2).
- **Headline gains are relative to the 3D-Premise baseline, not to the unrefined output** [V; arithmetic mine]
  - The abstract's "7.30% reduction in point-cloud distance" is GPT-4 few-shot: 3D-Premise 0.137 vs CADCodeVerify 0.127 (Table 2).
  - The "5.5% improvement in compile rate" is 91.0% → 96.5% against 3D-Premise, which had *lowered* compile rate from the unrefined 96.0%.
  - Against the unrefined output ("Generated"), GPT-4 few-shot moves point-cloud distance from 0.155 to 0.127 but compile rate only from 96.0% to 96.5% (Table 2).
  - The arXiv listing abstract says "5.0%" while the v2 PDF says "5.5%" (see Not found / discrepancies).
- **Table 2 reports "Best Refine", which is better than either refinement round on its own** [V]. The paper does not define it; per-sample oracle selection is my inference [U].
  - GPT-4 zero-shot (Table 5): Generated 0.153; Refine-1 0.146; Refine-2 0.159 (worse than unrefined); Best 0.132.
  - Gemini few-shot (Table 6): Refine-2 is 0.178 vs Generated 0.171.
  - CodeLlama (Table 7): the second round collapses compile rate to 47.0% (zero-shot) and 65.0% (few-shot), down from 70.0%/73.5% after round 1. Iterating blindly can make the design worse.
- **The numeric feedback baseline beats visual QA** [V]
  - The "geometric solver" baseline feeds back 13 measured properties from FreeCAD (width, height, faces, vertices, volume, …) against ground truth.
  - It has the best point-cloud distance in every GPT-4/Gemini setting (e.g. 0.103 vs CADCodeVerify 0.127, GPT-4 few-shot, Table 2).
  - The authors frame it as an upper bound because it needs the ground truth. In Forge the numeric targets come from the requirements, so the equivalent signal (measured vs *specified*) is available without a ground-truth model. That is my inference.
- **The self-verification answers are weak** [V]
  - On 50 samples, only 64.6% (Refine-1) and 68.2% (Refine-2) of the VLM's answers were correct, and 26.6% / 19.3% were "Unclear" (§6, Table 9).
- **Ablations (Table 3, 100 samples)** [V]
  - Removing the renders from refinement: point-cloud distance 0.126 → 0.153.
  - Removing the few-shot question examples: 0.126 → 0.141.
  - Human expert feedback beat CADCodeVerify (0.120 vs 0.137 on 50 samples, Table 4).
- **Error taxonomy (App. C.2, 50 samples)** [V]
  - 48% structural-configuration errors and 18% logical errors.
  - "Dimensional" feedback grew from 20% to 26% of feedback between rounds (Fig. 7), as structural errors turned into dimensional ones.
  - The authors' limitations section says point-cloud/Hausdorff metrics are "noisy" and miss structural gaps (§7).

### 2. Programmatic-CAD benchmarks: which ones exist and what they measure

| Benchmark | Exists? | What it measures | Target / input | Key numbers | Source |
|---|---|---|---|---|---|
| **CADPrompt** | Yes [V] | Prompt → CadQuery. Point-cloud / Hausdorff / IoGT / compile rate, all scale-normalised | 200 text prompts | See §1 | [2410.05340](https://arxiv.org/abs/2410.05340) |
| **CADGenBench** | Yes, but it is a **Hugging Face leaderboard, not a paper** [V] | Engineering drawing → STEP (49 generation fixtures). STEP + instruction → edited STEP (32 editing fixtures). Validity gate, then 0.4·shape + 0.4·interface + 0.2·topology (Betti numbers) | Tool-agnostic STEP. Reference agent writes **build123d** (or CadQuery) | §3.1 | [github.com/huggingface/cadgenbench](https://github.com/huggingface/cadgenbench), [results.jsonl](https://huggingface.co/datasets/HuggingAI4Engineering/cadgenbench-submissions) |
| **BenchCAD** | Yes (arXiv 2605.10865, UVA/UCSD/Rice) [V] | 17,900 execution-verified CadQuery parts in 106 industrial families; 49% anchored to ISO/DIN/EN/ASME/IEC tables. Tasks: image→code, code edit, image QA, code QA | 4 orthographic views → CadQuery | §3.2 | [2605.10865](https://arxiv.org/abs/2605.10865) |
| **CADBench** (Doris et al., MIT DeCoDE) | Yes (arXiv 2605.10873) [V] | Reconstruction: mesh or image → CadQuery program. 18,000 samples, 5 input modalities, IoU/SIoU/CD/valid shape rate (VSR)/compactness | Mesh/image | Claude Opus 4.7 has the best VLM IoU at 0.412 (VSR 0.798); CADFit (mesh) 0.859 (Table 2) | [2605.10873](https://arxiv.org/abs/2605.10873) |
| **CADBench** (BlenderLLM) | **Name collision** — a different benchmark with the same name [V] | Text → **Blender Python** scripts | Text | — | [2412.14203](https://arxiv.org/abs/2412.14203) |
| **"CAD-Bench"** (hyphenated) | Not found as a distinct benchmark [U] | — | — | — | — |
| **Text2CAD** | Yes (NeurIPS 2024 Spotlight) [V] | A learned transformer producing DeepCAD sketch-extrude sequences. About 170K models / 660K text annotations, beginner→expert | Text → command sequence (not code) | Learned model underperforms prompted LLMs on newer benchmarks (Text2CAD-Bench Table 1; CADTests Table 3) | [2409.17106](https://arxiv.org/abs/2409.17106) |
| **Text2CAD-Bench** | Yes (arXiv 2605.18430) [V] | 600 human-curated tasks at levels L1–L4. CD / IoU / invalidity rate (IR) | Text → CadQuery | L3 IR 68–92% for general LLMs single-shot (Table 1) | [2605.18430](https://arxiv.org/abs/2605.18430) |
| **CAD-Recode** | Yes (a method plus a 1M-script procedural dataset, not a benchmark) [V abstract] | Point cloud → CadQuery | Point cloud | See §8 | [2412.14042](https://arxiv.org/abs/2412.14042) |
| **CADTestBench / CADTests** | Yes (arXiv 2605.07807, Luxembourg SnT) [V] | Executable **B-rep unit tests** derived from the prompt, hardened by mutation analysis. 5,937 tests over CADPrompt, about 15 per sample | Text → CadQuery | §3.3 | [2605.07807](https://arxiv.org/abs/2605.07807) |
| **MUSE** | Yes (arXiv 2605.28579) [V] | 106 manufacturable **assemblies**. Staged funnel: code → geometry validity (watertight, manifold, self-intersection, overlap) → design-intent rubric scored by a VLM judge | Design spec → CadQuery | §3.2 | [2605.28579](https://arxiv.org/abs/2605.28579) |
| **RealCADBench** | Yes (arXiv 2609.03773, JD Industrial) [V] | 12,632 industrial tasks; 1,770 evaluated. Executability, solid/surface IoU, VLM judge. Includes a **Claude Code** and a **Codex** agent | Text / drawing / photo / render → **FreeCAD** Python | §3.2 | [2609.03773](https://arxiv.org/abs/2609.03773) |
| **neuralCAD-Edit** | Yes (arXiv 2604.16170, Autodesk Research) [V] | Expert multimodal edit requests (video + speech + sketches) on STEP models; rated by human CAD experts | STEP → CadQuery edit | §3.2 | [2604.16170](https://arxiv.org/abs/2604.16170) |
| **Hephaestus-CCX** | Yes (inside arXiv 2605.17448) [V] | 50 engineering briefs → assembled STEP, checked by **CalculiX FEA** with typed pass/fail requirements | Brief → CadQuery / STEP | §4 | [2605.17448](https://arxiv.org/abs/2605.17448) |
| **HistCAD** | Yes (arXiv 2602.19171) [V abstract] | Constraint-aware history dataset (170,236 sequences). Scores whether *editability* is preserved (edit reachability, constraint satisfaction) | Text → constrained sequence | — | [2602.19171](https://arxiv.org/abs/2602.19171) |

### 3. The 2026 finding: valid, plausible-looking CAD still fails on dimensions and design intent

The brief refers to a single "reported 2026 finding". I did not find one paper that owns it. It is the shared headline of at least seven independent 2026 benchmarks, listed below, each measuring it a different way. [V for each]

#### 3.1 CADGenBench (Hugging Face) — live leaderboard data, read directly

- **Where the numbers come from** [V]
  - I parsed the public `results.jsonl` (595 rows, 548 completed, benchmark v0.1.0).
  - HF's own validated June baselines use their reference agent. That agent writes build123d, renders, reviews and repeats until the output is valid.
- **Near-100% validity with low shape scores (June 2026)** [V]
  - Claude Opus 4.8 produced 49/49 valid generation outputs (validity 1.0) but scored only **0.2738** on generation; aggregate 0.3451, editing 0.4543.
  - Other validated HF baselines scored 0.1677–0.4514 aggregate (Claude Fable 5 best, 0.4514), with validity 0.78–0.96.
- **Later submissions score much higher (Sept 2026)** [V]
  - The best rows reach 0.80–0.83 aggregate. Examples: "build123d-mcp 0.3.85 + Claude Opus 5.5 (max effort) r2" 0.8298; "Godela" 0.8113 (validated).
  - 524 of 548 rows are **unvalidated self-reports**.
  - Per-sample scores are returned to submitters, so the private test set can be hill-climbed by repeated submission. Several top rows share byte-identical generation sub-scores (e.g. 0.869, 0.4868, 0.6583), which suggests composite or reused outputs.
  - Treat leaderboard deltas under about 0.05 as noise. That threshold is my judgement; a "0.06 gap is meaningful" rule appears only in a search snippet [R] and I could not find it in the primary docs.
- **What the metric catches** [V, docs/metrics.md]
  - Shape similarity is blind to topology.
  - Topology (Betti numbers) is blind to feature position.
  - "Interface match" (keep-in/keep-out volumes on mating features) catches wrong hole position or size even when the bulk shape looks right. That is the dimensional and interface check that pictures miss.

#### 3.2 Other 2026 benchmarks

- **BenchCAD** ([2605.10865](https://arxiv.org/abs/2605.10865)) [V]
  - **Frontier models run but miss the shape.** In Table 10, image → CadQuery, frontier models run 67.5–94.0% of the time but reach voxel IoU of only 0.19–0.28. claude-opus-4.7 (no thinking): execution 94.0%, IoU 0.2740. gemini-3.1-pro (thinking): 79.8%, 0.2790.
  - **Industrial parameters are the weak spot.** The "Industrial Parametric Abstraction" QA axis tops out at 0.551 (Table 2).
  - **The authors' summary:** "The geometry passes the eye but fails the caliper" (§1).
  - **Failure examples (§5.2):**
    - a uniform helix instead of DIN 2095 closed-and-ground spring ends;
    - extrusion on the XY plane instead of XZ;
    - a twist-extrude replaced by two plain brackets.
  - **Renders cannot replace numbers in edits.** When the edit instruction is replaced by a target render, every model scores near zero. The paper explains that "a render specifies geometry but not numbers" (§5.1).
- **RealCADBench** ([2609.03773](https://arxiv.org/abs/2609.03773), FreeCAD Python) [V]
  - **Parts (Table 4):** across six frontier models, executability is 0.565–0.812 but conditional surface IoU only 0.112–0.217. GPT-5.5 executes 0.9311 of tasks with surface IoU 0.1393.
  - **Assemblies (RCB-Assm25, Table 5, n = 25):** GPT-5.4 and Codex + GPT-5.5 execute every task (1.0000) but reach surface IoU of only 0.1046 and 0.1161.
  - **Wrapping a model in a general coding agent barely helps.** Claude Code + Opus 4.8 changes the composite by +0.0006 over bare Opus 4.8, and surface IoU drops from 0.1058 to 0.0864.
  - **Coding agents fix execution, not identity.** The authors' conclusion: "execution alone is insufficient". Agents repair execution while product identity, fine structures and assembly placement stay weak (§4.4).
- **MUSE** ([2605.28579](https://arxiv.org/abs/2605.28579), assemblies from design specs) [V]
  - Table 2 shows a funnel. claude-opus-4.7: sandbox success 76.42% → overlap-free 60.38% → geometry-valid 58.49% → design-intent final score 39.47%. gpt-5.5: 77.36 → 68.87 → 52.36.
  - Overlap-free is the check that drops most, so multi-part spatial reasoning is the bottleneck.
  - This is single-shot generation with no feedback loop.
- **Text2CAD-Bench** ([2605.18430](https://arxiv.org/abs/2605.18430)) [V]
  - Three largely independent capabilities: executability, geometric similarity and feature-level design understanding.
  - Example: Gemini3-Flash has the lowest L4 invalidity (17%) but among the lowest feature scores (§4.3).
  - The authors warn that CD and IoU computed only on executed samples suffer survivorship bias (§4.4).
- **CADTests** ([2605.07807](https://arxiv.org/abs/2605.07807)) [V]
  - **Detailed prompts are harder than abstract ones.** On the detailed partition, which states exact dimensions, the best method passes all tests on 62.5% of samples (CADTests + Log, Claude-4.6-Sonnet, Table 3). ReAct + Claude reaches 58.0%.
  - **Dimensional, topological, volumetric and spatial tests fail most** (Fig. 3). Solid validity and geometry-type tests are easy.
- **neuralCAD-Edit** ([2604.16170](https://arxiv.org/abs/2604.16170), Autodesk Research) [V]
  - **Setup:** frontier models edit expert-requested STEP models through a CadQuery harness that lets them run scripts and inspect renders iteratively.
  - **Expert acceptance (Table 1), with outputs rated by 5 CAD experts:**

    | System | Acceptance | Validity |
    |---|---|---|
    | Human baseline | 0.78 | — |
    | GPT 5.2 | 0.25 | 0.99 |
    | Gemini-3-Pro | 0.10 | — |
    | Claude Sonnet 4.5 | **0.05** | 0.42 |

  - **Valid is not accepted:** GPT 5.2's validity is 0.99 against 0.25 acceptance.
  - **Models declare success on wrong edits.** For a drone edit, the models copied the rotors the right number of times but misplaced them, then declared the task finished (§4.3).
- **Hephaestus-CCX** ([2605.17448](https://arxiv.org/abs/2605.17448), FEA-graded) [V]
  - **No strict pass on first attempt.** Codex/GPT-5.5/5.4 and Claude Code/Opus-4.7/Sonnet-4.6 produce **0 strict-passing artifacts** in first-attempt runs across 20 single-part and 30 multi-part briefs (Table 2).
  - **Partial credit is low.** The best first-attempt mean requirement pass is 32.7% (Opus-4.7 xhigh, single-part).
- **Dimensional accuracy measured directly** — Pointer-CAD v2 ([2606.29301](https://arxiv.org/abs/2606.29301), ECCV 2026) [V]
  - **Metric:** tolerance-based vertex/edge/face accuracy on un-normalised geometry.
  - **Single-shot CadQuery edge accuracy (Table 4):** Claude Opus 4.5 52.77, GPT-5.2 63.55, Gemini 3 Pro 69.51, versus 89.26 for a 1.5B specialist trained in-distribution.
  - **Chamfer distance hides the gap.** The authors say normalised CD barely separates methods whose parameter accuracy differs (§4.5).
- **Design intent in edits** — HistCAD ([2602.19171](https://arxiv.org/abs/2602.19171)) [V abstract]
  - Reports that explicit constraints are essential to preserve design intent after parameter edits.
- **Wrong intent is worse than none** — "Wrong Design Intent Is Worse Than Never Conditioning" ([2607.23191](https://arxiv.org/abs/2607.23191)) [V abstract]
  - With a 1.5B LoRA model, a *wrong* intent header lowered adherence below the never-conditioned baseline.
  - Single author, narrow setup; I treat this as low-weight evidence.

#### 3.3 Why the older metrics hid this

- **Most papers normalise away absolute scale.** CADPrompt normalises to a unit cube (§5.2). CAD-Coder (DeCoDE) and CADBench normalise by inertia and principal axes. Most RL papers do the same.
- **Only a few benchmarks score millimetres.**
  - CADSmith scores in absolute mm.
  - Pointer-CAD v2 uses ε-tolerance.
  - CADGenBench aligns rigidly "never scale".
  - CADTests checks specified dimensions directly. [V]
- **CD agrees poorly with human judgement.** In CADTests' human study (125 generations, 2 experts, κ = 0.54), the AUC against the human label was (Table 4):

  | Metric | AUC vs human |
  |---|---|
  | Chamfer distance | 0.663 |
  | CLIP score | 0.665 |
  | LVM judge | 0.659 |
  | **CADTests requirement score** | **0.928** |

  [V]

### 4. Programmatic verification loops: the strongest evidence for "numbers beat pictures"

- **CADSmith** ([2603.26512](https://arxiv.org/abs/2603.26512), CMU, arXiv preprint) [V]
  - **Pipeline:** Planner (prompt → JSON spec with target bounding box and hole counts) → Coder (Claude Sonnet, with keyword RAG over 155 CadQuery API entries, 28 examples and 25 error→fix patterns) → sandboxed Executor → Validator → Refiner.
    - The Executor extracts OCCT volume, bounding box, centre of mass, face/edge/vertex counts and validity.
    - The Validator is Claude **Opus** (a different, stronger model: maker ≠ checker). It sees kernel metrics, code and a 3-view render. A hard gate rejects any invalid solid.
    - Loop budget: ≤3 execution-repair tries (inner loop), ≤5 geometric refinements (outer loop). From iteration 3 on, the Refiner is told to escalate to a different construction strategy.
  - **Results (Table I, 100 prompts with explicit mm dimensions, scored in absolute mm):**

    | Configuration | Exec % | Median IoU | Mean CD |
    |---|---|---|---|
    | Zero-shot | 95 | 0.8085 | 28.37 |
    | Full pipeline | 100 | 0.9629 | 0.74 |

    - 88/100 parts converged with no refinement; the mean was 0.13 refinements per part.
  - **Vision ablation:** without the render, mean CD is 18.19 overall. On T3 complex parts it is 49.68 vs 1.42 with vision (§IV-B). Kernel metrics alone suffice for T1/T2 parts but not T3, because of "false convergence" (right bounding box and volume, wrong structure).
  - **Failure both checks missed:** a quadcopter frame with gaps between arms and hub scored F1 0.963 / IoU 0.985 and passed both kernel checks and the judge (Fig. 6). A solid-count / connectivity check (Betti b0 = 1) would have caught it; that is my inference.
  - **Caveats:** own 100-prompt benchmark; no ablation isolates RAG or the Planner; the zero-shot baseline changes many things at once.
- **CADTests as a generation loop** ([2605.07807](https://arxiv.org/abs/2605.07807)) [V]
  - **Method:** the planner writes CadQuery *and* executable B-rep tests (face counts, bounding-box ratios, volumes, containment), then iterates ReAct-style on test failures.
  - **Results (Table 3), Claude-4.6-Sonnet pass rate (PR) / requirement score (RS):**

    | Method | Detailed PR | Detailed RS | Abstract PR | Abstract RS |
    |---|---|---|---|---|
    | 10-shot | 0.510 | — | — | — |
    | ReAct (execution errors only) | 0.580 | 0.874 | 0.715 | — |
    | CADTests + Log (tests + intermediate geometry logging) | 0.625 | 0.897 | 0.810 | 0.962 |

  - **Execution feedback removes invalid outputs.** ReAct cut Claude's invalid ratio from 0.155 (10-shot) to 0 (Table 3).
  - **Multi-view renders added nothing.** GPT-5.2 ReAct + Image scored the same as ReAct (abstract PR 0.695 for both), so the authors dropped it on token cost (§6 (v)).
  - **LLM-written tests need hardening.** From prompts alone, Claude-4.6-Opus/Sonnet wrote tests that were 98.3% / 97.8% valid but killed only 65.4% / 63.0% of seeded mutants (Table 1). Four rounds of refinement against mutants and augmented references raised mutation scores above 0.89 (Table 2).
- **CADGenBench practitioner evidence: build123d-mcp** ([pzfreo/build123d-mcp](https://github.com/pzfreo/build123d-mcp), [cadgenbench-build123d](https://github.com/pzfreo/cadgenbench-build123d))
  - **What it is** [V]
    - An MCP server with a persistent build123d session.
    - Tools: render PNG/SVG/DXF; measure volume, area, bounding box, topology and centre of mass; find holes and patterns; check printability, fit and export validity; save and restore snapshots.
    - Its recommended loop: build one feature at a time, render or measure after important steps, validate, then export.
  - **Tool vs no tool (my matched comparison, leaderboard rows)** [V]
    - Same submitter, same model and effort (Claude Opus 5.5 xhigh), same day and data revision (2026-09-23).
    - With build123d-mcp 0.3.84: 0.8049 aggregate, validity 1.0 (gen 0.8361, edit 0.7571).
    - "Official baseline prompt", no MCP: 0.7520, validity 0.9259 (gen 0.8011, edit 0.6768).
    - For Opus 5 xhigh the gap is smaller: 0.6391 vs 0.6268.
    - Single runs and unvalidated, so this is **weak-to-moderate evidence**: about +0.01–0.05 aggregate, with a consistent validity gain.
  - **README claim (June)** [V as a claim]: build123d-mcp raised one model from 0.360 to 0.457 and validity from 88% to 100%. Those numbers match leaderboard rows, but the two runs differ in data revision and effort setting (I checked the rows).
  - **The model matters more than the harness** [V, leaderboard rows]
    - HF June baselines were 0.31–0.37 for Claude Opus 4.6–4.8.
    - Opus 5.5 with the plain baseline prompt reached 0.7520 in September.
    - A same-model harness change moved the score about 0.05; model generations moved it about 0.4.
  - **Cost datum** [V, pzfreo comparison note]: one Opus 5 xhigh MCP sweep over 79 fixtures cost about $724.77 API-equivalent.

### 5. Physics-in-the-loop / FEA-feedback CAD agents

- **Self-Improving CAD Generation Agents with FEA as Feedback** ([2605.17448](https://arxiv.org/abs/2605.17448), May 2026, arXiv "work in progress") [V]
  - **Setup**
    - Hephaestus-CCX: 50 engineering briefs → assembled multi-part STEP. Each brief has CalculiX FEA kits and typed pass/fail requirements (stress/yield, deflection, buckling, modal, mass, interfaces).
    - The agents are Codex and Claude Code, run as production harnesses.
  - **First attempt (Table 2)**
    - 0 strict passes for every configuration.
    - Mean requirement pass is 6.2–32.7%.
  - **One FEA-feedback repair round**
    - Changes mean requirement pass by −1.3 to +30.9 points; the average is +13.4 (§7).
    - Claude Opus-4.7 xhigh single-part slightly *regressed* after feedback (32.7% → 31.4%).
    - GPT-5.5 high multi-part gained most (8.3% → 39.2%).
    - The authors separate "first-shot designer" and "repair agent" as distinct capabilities (§5.1).
  - **Longer loop** (§6, Fig. 1): Codex GPT-5.5/high, up to 10 attempts, with blueprint planning.
    - Rises from 38.8% to **60.5%** mean requirement pass with **9/50 strict passes**, at 68 min per item.
    - **Detailed numbers matter.** The second large jump came when FEA feedback moved from typed pass/fail verdicts to **failure margins plus the offending selector or load case**.
  - **Higher reasoning effort is not monotonic** (high sometimes beats xhigh; xhigh beats max). Compute spent looping against an external evaluator beats compute spent deliberating.
  - **Rich-view image judge (21 renders)**
    - Raises GPT mean requirement pass by 6.3 points on average.
    - For Claude Opus-4.7, the gains were "smaller or mixed" (Table 3). 7 views sometimes matched or beat 21 (Tables 6–7).
  - **Contract repairs and gaming risk.** Of 9 strict-pass flips, several were checker-contract repairs: metric aliases, mass fields, selector bindings (Table 4).
    - One (an ECSS spacecraft panel) fixed a mass-property error worth more than 10× that no render would reveal.
    - This is both a gaming risk (passing the checker by editing metadata) and evidence that numeric checks catch what pictures cannot.
  - **The harness is part of the measured system.** GPT-5.5/high scored differently under OpenCode than under Codex (App. A).

- **Physics-in-the-Loop** ([2605.19717](https://arxiv.org/abs/2605.19717); arXiv comment says IJCAI-ECAI 2026 AI4Tech track) [V, sub-researcher]
  - **The loop:** LangGraph agents write CadQuery. torch-fem FEA returns the safety factor, stress hotspots and over-engineering flags.
  - **The ablation that isolates physics:** the VLM visual review is kept and only the FEA tools are removed. Share of designs in the target safety-factor band: **49/83 (59.0%) with FEA vs 6/27 (22.2%) without**, Fisher p = 0.0008 (Table 4).
  - Without FEA, 50–80% of designs were over-built (safety factor above 5).
  - **Caveats:** small, unequal samples; abstract and body disagree on the complexity numbers.
- **Code-compliant structural design** ([2608.07978](https://arxiv.org/abs/2608.07978)) [V, sub-researcher]
  - OpenSeesPy FE plus a building-code checker, with violations turned into hard constraints.
  - Compliance **56.8% (all open-loop variants) → 98.6% (closed loop)**; McNemar p below 10⁻⁵ (Tables 5–6).
  - Covers beams, trusses and frames, not free-form CAD.
- **MechStyle** ([2509.20571](https://arxiv.org/abs/2509.20571), ACM SCF '25) [V, sub-researcher]
  - Not an LLM system. FEA-damped stylization kept 80.2–100% of 180 stylized parts structurally viable, vs 25.55% without FEA.
- **Negative result: IterSIMP-σ** ([2605.19110](https://arxiv.org/abs/2605.19110)) [V, sub-researcher]
  - An LLM reading stress-field *images* to guide topology optimization gave no significant gain (p = 0.382).
  - LLMs plateau when asked to optimize numbers themselves (RocketBench, [2504.19394](https://arxiv.org/abs/2504.19394)).
  - The best results hand the numerics to solvers or optimizers. The LLM chooses topology and interprets results; a solver or optimizer sets the values.
- **What is still missing:**
  - No LLM-CAD agent with a CFD, thermal or kinematic loop and a clean no-physics ablation.
  - No human-user study.
  - Most "no-physics" baselines are also "no-iteration" baselines, which confounds the comparison.

### 6. MIT DeCoDE Lab (Faez Ahmed)

Sub-researcher read the PDFs; I spot-checked CAD-Coder Table 2 and DesignQA Table 2.

- **CAD-Coder** (Doris, Alam, Heyrani Nobari, Ahmed; [2505.14646](https://arxiv.org/abs/2505.14646); IDETC 2025 and JMD 2026) [V]
  - **Model and data:** a LLaVA-1.5 / Vicuna-13B VLM fine-tuned on GenCAD-Code, 163,671 image → CadQuery pairs (line / arc / circle / extrude only).
  - **Results (Table 2, only 100 test samples), valid syntax rate / IoU_best:**

    | Model | VSR | IoU_best |
    |---|---|---|
    | CAD-Coder | 100% | 0.675 |
    | GPT-4.5 | 84% | 0.524 |

    IoU_best is scale-normalised and computed only on scripts that execute.
  - **Failure modes:**
    - Wrong aspect ratio on real photos.
    - Parts that need several extrudes fail.
    - It cannot produce fillets; fine-tuning erased CadQuery knowledge the base model had (§4.3.2).
- **DesignQA** (Doris et al.; [2404.07917](https://arxiv.org/abs/2404.07917); JCISE 2025) [V]
  - **What it is:** 1,451 questions checking MIT Motorsports CAD and renders against the Formula SAE rulebook. This is the lab's most verification-relevant result.
  - **Dimension-compliance accuracy (Table 2):**
    - GPT-4o with the full rulebook in context: 0.825.
    - Under simple RAG: GPT-4o 0.675, Claude-Opus 0.508, **GPT-4 0.300** (the naive baseline is 0.5).
    - Retrieval-task F1 under RAG: only 0.17–0.19.
  - **Scale bars (Table 5):** GPT-4 with the full rulebook scores 0.66 on direct dimensions but 0.28 when the dimension must be read from a scale bar.
  - **Failure modes (§4.2):** misreading the scale bar; needing the sum or difference of two dimensions; misidentifying which components a dimension spans.
- **MCERF** ([2604.09552](https://arxiv.org/abs/2604.09552); JMD 2026) [V]
  - Multimodal retrieval over DesignQA. Dimension accuracy 0.82 using "Vision2Text": convert drawings and tables to structured text, then do the arithmetic.
  - The Compilation task (listing every rule that applies) reached only 0.56.
- **VideoCAD** ([2505.24838](https://arxiv.org/abs/2505.24838); NeurIPS 2025) [V]
  - **Data:** more than 41K *synthetic* bot-generated Onshape UI videos.
  - **Agents driving the CAD GUI:** GPT-4.1, Claude-3.7 and Gemini-2.5, controlling the Onshape UI through BrowserGym, completed **no** full CAD build (§5.2).
  - **Visual QA:** extrusion counting at best 47.0 (Table 5); symmetry detection 12.0–27.9 (Table 8).
- **"From Concept to Manufacturing"** ([2311.12668](https://arxiv.org/abs/2311.12668); AI Review 2025) [V]
  - GPT-4V's first CAD attempt was correct in 1/9 runs.
  - Iterating with rendered views did **not** improve the CAD (Table 6).
- **CADBench** (§2) and **CADFit** ([2605.01171](https://arxiv.org/abs/2605.01171); ICML 2026) [V]
  - CADFit is kernel-validated, IoU-driven program optimisation from meshes: DeepCAD IoU 0.964 with no invalid outputs (Table 1). It takes minutes per shape and fails on lofts and sweeps.
- **Intrinsic Selection** ([2606.08850](https://arxiv.org/abs/2606.08850)) [V]
  - For the same CAD-Coder model, best-of-128 IoU is far above pass@1: Fusion360 0.41 → 0.83 (Table 3).
  - The authors' verifier-free selector reaches only 0.45.
  - Kernel execution plus IoU takes up to 40% of loop time.
- **Naming checks**
  - **LLM4CAD is *not* DeCoDE.** It is Li, Sun and Sha (UT Austin; JCISE 2025, JMD 2025) [V CADSmith refs and sub-researcher].
  - **CAD-Llama is Fudan** (CVPR 2025) [V].
  - There is no DeCoDE "design intent" paper and no DeCoDE text-to-CAD benchmark [V lab page, per sub-researcher].

### 7. Post-execution critique for text-to-CAD

A sub-researcher read these papers; I independently verified CADCodeVerify, CADSmith, CADTests, Query2CAD and the FEA-feedback agents.

- **Reference-free programmatic checks have the best support** [V]
  - **ReliCAD** ([2609.22325](https://arxiv.org/abs/2609.22325)): kernel and runtime evidence-driven checking vs visual-only checking (Table III):

    | Checking | Validity | IoU | CD |
    |---|---|---|---|
    | Evidence-driven | 99.8% | 87.53 | 0.12 |
    | Visual-only | 92.3% | 85.91 | 30.77 |

    Visual-only checking needed fewer repairs *because it missed errors*.
  - **CAD-Assistant** ([2412.13810](https://arxiv.org/abs/2412.13810), ICCV 2025), autoconstraining (Table 5): adding a programmatic constraint checker raised PF1 from 0.747 to **0.979**. Adding renders plus a JSON view gave only 0.726 → 0.747.
  - **Consensus selection** ([2608.09706](https://arxiv.org/abs/2608.09706), Siemens), on identical CADPrompt candidate pools (Table 1):

    | Selector | CD |
    |---|---|
    | Random | 0.0631 |
    | VLM + reasoning verifier | 0.0627 |
    | **Geometric medoid** | **0.0610** |

    Gains level off near N ≈ 9 samples. It fails when most samples share the same error.
- **Execution-error loops fix validity, not geometry** [V]
  - **CAD-Judge** ([2508.04002](https://arxiv.org/abs/2508.04002), ICASSP 2026), repair iterations 0 → 3 (Table 5): IR 2.62 → 1.38, CD flat (53.11 → 51.72).
  - **CIT-CAD** ([2609.07434](https://arxiv.org/abs/2609.07434)): constraint-tree checks raised constraint satisfaction from 16.7 to 31.8%, but IoU only from 32.6 to 32.8% (Table II). Constraint satisfaction is scored against its own inferred tree, which is circular.
- **Trained same-model critique** — **RA-CAD** ([2608.05714](https://arxiv.org/abs/2608.05714)) [V]
  - The critique reads execution state (pass/fail, error location, structure counts), not renders. CD falls from 44.24 (RL, no critique) to 35.44 (full) (Table 3).
  - Critique accuracy and per-round data are not reported.
- **Separate VLM critic on renders** — **Seek-CAD** ([2605.17702](https://arxiv.org/abs/2605.17702), ICLR 2026) [V]
  - Gemini-2.0 critiques DeepSeek-R1's step-wise renders.
  - Geometry improves, but compile rate falls every round: Pass@2 0.77 → 0.72 → **0.55** (Table 2).
- **Feedback can make things worse. Documented cases** [V]:
  - 3D-PreMise-style image feedback (GPT-4 compile 92.0 → 89.5%, CADCodeVerify Table 5).
  - Seek-CAD round 2.
  - CADFusion ([2501.19054](https://arxiv.org/abs/2501.19054), ICML 2025) trained on visual feedback alone: IR 88.87%.
  - Opus-4.7 with a 21-view judge and with one FEA retry (§5).
  - Weak clarifiers in ProCAD make mean CD *worse* than no clarification (11.56 vs 7.80 for Claude Sonnet 4.5 alone, Table 4).
- **VLM judges are poor substitutes for humans or numbers** [V]
  - neuralCAD-Edit (Table 2): Claude Sonnet 4.5 rated its own edits' acceptance at 0.53; human experts gave 0.05.
  - Every VLM evaluator narrowed the human-vs-AI gap relative to human raters.
  - CADCodeVerify's VLM answered only 64.6–68.2% of its own verification questions correctly.
- **Clarify before generating** — ProCAD ([2602.03045](https://arxiv.org/abs/2602.03045), ICML 2026) [V]
  - Claude Sonnet 4.5 alone: mean CD ×10³ 7.80, IR 14.6%. With a trained clarifier plus coder: 0.63 and 0.9% (Table 4).
  - The test set was filtered to prompts where ambiguity breaks the coder, and answers came from a simulated user.
- **How many rounds are worth it** [V]
  - Most gain comes in round 1: Query2CAD 53.6 → 73.2 → 76.7 → 76.7% (Table 2); Seek-CAD; CAD-Judge; CADCodeVerify.
  - Loops level off after 3–4 rounds (CIT-CAD).
  - They keep improving only when feedback gets *more specific* (Hephaestus, §5).
- **Maker ≠ checker** [V]
  - No paper runs the controlled comparison (separate critic vs self-critique with everything else fixed).
  - Indirect evidence says *what is checked* (kernel numbers) matters more than *who checks*.
  - The self-grading inflation in neuralCAD-Edit is the strongest direct argument against the maker grading its own output.

### 8. Training-based methods (RL with geometric rewards) — what they show

Sub-researcher read the PDFs; I spot-checked Pointer-CAD v2 Table 4.

- **Validity is essentially solved by any execution-feedback route.** The invalid rate (IR) falls to about 0–1% [V]:
  - cadrille ([2505.22914](https://arxiv.org/abs/2505.22914), ICLR 2026 Oral): RL with a reward of 10×IoU, or −10 if invalid. CC3D IR 5.9 → 0.2 (Table 3).
  - CADEvolve ([2602.16317](https://arxiv.org/abs/2602.16317)): IR after SFT is 19.0 / 18.2 / 32.0; after RL, 0.2 / 0.5 / 2.3 (Table 1).
  - CAD-Recode ([2412.14042](https://arxiv.org/abs/2412.14042), ICCV 2025): sample 10 candidates and keep the lowest CD. Without it, IR is 4.9–16.8 (Table 3).
  - CADReasoner ([2603.29847](https://arxiv.org/abs/2603.29847)): iterative editing with no RL; DeepCAD IR 1.5 → 0.2 over 5 steps (Table 2).
- **Accuracy gains are real but moderate, and nearly all are measured scale-normalised** [V]
  - cadrille RL adds +3–9 IoU points.
  - CAD-Coder (Guan; [2505.19713](https://arxiv.org/abs/2505.19713), NeurIPS 2025): GRPO with a Chamfer reward cut mean CD from 74.55 (SFT) to 6.54 (Table 2).
    - Appendix F reports **reward hacking** on thin or hollow parts, because the CD reward samples points sparsely.
  - CAD-RL ([2508.10118](https://arxiv.org/abs/2508.10118), AAAI 2026): IoU 63.9 → 72.3 and execution 94.66 → 99.63 from RL (Table 2). The authors say sizes stay imprecise.
- **The weak frontier baselines in these papers are single-pass with no execution feedback** [V]
  - Claude-3.7 IR 47.03 and GPT-4o 93.00 (CAD-Coder Table 1).
  - With engine feedback, prompted GPT-4o + ReAct reached 62.7% success, about the same as RL-trained TOOLCAD at 63.9% (TOOLCAD [2604.07960](https://arxiv.org/abs/2604.07960), ACL 2026, Table 1).
  - TOOLCAD's Table 3: CAD-engine feedback beat visual feedback on parts with 5 or more components (29.7 vs 20.8).
- **Explicit dimensions help** [V]
  - CADFS ([2605.01925](https://arxiv.org/abs/2605.01925), CVPR 2026): putting the target bounding box in the prompt cut CD from 0.58 to 0.14 and IR from 14 to 9 (Table 7).
  - ProCAD / "Clarify Before You Draw" ([2602.03045](https://arxiv.org/abs/2602.03045), ICML 2026): the abstract says auditing an ambiguous spec and asking clarifying questions before coding cut mean CD by 79.9% vs Claude Sonnet 4.5, and IR from 4.8% to 0.9%.
- **Relevance to Forge:** none of these papers use build123d. The training-free mechanisms reproduce most of RL's *validity* gains: execute-and-repair, sample-and-select by measured geometry, explicit numeric specs. RL's accuracy gains don't transfer to a prompted Claude agent without fine-tuning. [inference]

### 9. Target language, doc retrieval, repair iterations, stepwise vs one-shot

Sub-researcher read the PDFs and leaderboard data; items marked "mine" I read myself.

- **Target language**
  - **CADDesigner** ([2508.01031](https://arxiv.org/abs/2508.01031), Table 5) is the only controlled comparison that includes build123d. [V]
    - Setup: Claude-4-Sonnet in the same ReAct agent for each language, with RAG over each library's docs, on 200 DeepCAD models.
    - build123d vs CadQuery: success 96.0% vs 87.5%; Pass@1 0.59 vs 0.50; latency 363 s vs 541 s.
    - But IoU is lower for build123d: 0.2617 vs 0.2827.
    - The authors' explicit CadQuery wrapper (ECIP) scored best (IoU 0.3041, success 100%).
  - **P3D-Bench** ([2606.11152](https://arxiv.org/abs/2606.11152), Table 3), single-shot, OpenSCAD vs CadQuery. [V]
    - OpenSCAD validity is higher: Claude Opus 4.6 image-to-3D 1.000 vs 0.926.
    - "Bad argument" errors are about 55% of CadQuery failures.
    - Maximum thinking *lowered* CadQuery validity for 4 of 5 models (Table 4).
    - OpenSCAD is CSG/mesh, so it cannot give Forge parametric STEP.
  - **AIDL** ([2502.09819](https://arxiv.org/abs/2502.09819)): GPT-4o almost never wrote valid FeatureScript, even with docs. [V]
  - **Text2CAD-Bench:** Python CAD code beats DeepCAD-style command sequences on validity (mine, §2). [V]
  - **Not found:** a peer-reviewed build123d-vs-OpenSCAD study, or any KCL evaluation.
  - **Mis-cited:** Machado et al. 2019 is a *human-user* study that CADSmith cites as LLM context (mine). [V]
- **Doc retrieval**
  - **Decisive for APIs the model doesn't know.** [V]
    - CADDesigner Table 3: removing API annotations from the custom API → 0 valid models.
    - Seek-CAD Table 3: without the retrieval corpus nothing compiled; Pass@1 was 0.68 with hybrid retrieval.
  - **Modest for known libraries.** [V]
    - CADCodeVerify few-shot doc examples: GPT-4 compile 92.0 → 96.0% (Table 2).
    - CADTests "Skilled" (guidelines in context) ≈ 10-shot (mine).
  - **No doc-retrieval ablation exists for build123d or CadQuery.**
  - The CADGenBench reference agent injects a static 225-line build123d cheat sheet. [V]
- **Execution-error feedback and repair counts** [V]
  - **Validity.** Execution feedback reliably fixes it:
    - CADTests: Claude IR 0.155 → 0 (mine).
    - CADSmith: 95 → 100% (mine).
    - IterCAD-Hu: GPT-5 IR 28.10% → 5.30% (Table 1).
    - TOOLCAD: GPT-4o IR 20.49 → 9.12, success 48.4 → 62.7%.
    - CADDesigner: removing structured error messages drops success 100 → 81.5%.
  - **Geometry.** It barely moves (CAD-Judge CD flat, mine).
  - **Where gains stop.** Round 1 gives most of the gain: Query2CAD 53.6 → 73.2 → 76.7 → 76.7%; Seek-CAD caps at 1 round; CIT-CAD levels off at 28.9% after about 4.
  - **Weaker models benefit more from turns.** P3D-Bench Table 5: GPT-5.5 averaged 1.5 turns for about +0.002; Gemini 3.1 Pro 7.9 turns for +0.03.
  - **Common caps:** 3–5.
- **Stepwise vs one-shot** [V]
  - **Intermediate state helps.**
    - Seek-CAD: dropping intermediate renders cost more (IoGT 0.6713) than dropping the final render (0.7036).
    - CADTests + Log > CADTests (mine).
    - CADReasoner MCB: IR 21.9 → 4.0 from t = 1 to t = 5.
  - **The only direct build123d incremental-build evidence** is the CADGenBench build123d-mcp pair (§4). It is unvalidated.
  - No paper separates "stepwise" from "more feedback".

### 10. Independent tests of commercial text-to-CAD tools

A sub-researcher gathered these sources; the benchmark rows are my own reading.

- **No public benchmark evaluates any commercial text-to-CAD product** [V]
  - No benchmark I found (BenchCAD, CADBench, MUSE, RealCADBench, Text2CAD-Bench, CADTests, neuralCAD-Edit) runs Zoo, Adam, Backflip, Autodesk neural CAD or Leo AI.
  - None of them appears on the CADGenBench leaderboard. CADGenBench accepts any tool's STEP output, so vendors could submit; they haven't.
  - CADSmith notes that Zoo offers text-to-CAD "without published methods or reproducible benchmarks" (§II-A).
- **The only independent product tests are small hands-on write-ups.** Methodology is **Low** throughout: 1–6 prompts per tool, single attempts, no blinding, and almost no measured dimensions.
  - **Xometry Pro, "We Tested 7 Text-to-CAD Tools"** (Aug 2025) [V, sub-researcher]
    - Zoo: the simple tube was fine; the 24-tooth gear was not accurate; the manifold block failed.
    - Adam: the manifold was simplified.
    - Leo AI returned images only.
    - Vondy's downloads failed.
    - CADScribe got the gear wrong.
  - **Mechanomy** (Feb 2024) is the only test that measured dimensions, on an early Zoo build [V, sub-researcher]:
    - A "24 tooth spur gear" came out 26 mm OD with a 10 mm bore.
    - The tool never asked for the missing parameters.
  - **HN launch thread for Adam** (Jun 2026) [V anecdotes]
    - A connector built from a datasheet had the wrong pitch and pin positions.
    - An engine mount was declared "done" without its real specs.
  - Competitor-written comparisons (Leo AI, TexoCAD) contain factual errors about rivals' output formats, which lowers their credibility.
- **Vendor claims have no disclosed method** [V as claims]
  - Zoo: error rate cut "from 50% to 16%" for KCL generation (Aug 2025 blog).
  - Backflip: about 10% of parts "really well" (Apr 2025).
  - Autodesk: 80–90% automation of routine work; neural CAD shown only as keynote demos of pre-beta software.
  - Leo: "96% accuracy" [R].
- **Autodesk Research's neuralCAD-Edit is the strongest vendor-affiliated evaluation** [V]
  - It tests general LLMs, not Autodesk's own product.
  - Best acceptance was 0.25 (GPT 5.2) against 0.78 for the human baseline (§3.2).
- **Failure patterns repeated across products and benchmarks** [V/R mix]:
  1. A complexity cliff: primitives work, multi-feature parts fail or get simplified.
  2. **Silent assumptions**: tools don't ask about missing parameters and declare "done".
  3. Features are omitted or replaced by simpler ones (holes, sweeps and lofts become extrudes).
  4. Spatial and assembly errors: overlaps, misplacement, missing mates. Zoo's FAQ says assembly mates are on the roadmap; Leo's assemblies are not mated automatically.
  5. Datasheet fidelity: pitch and pin positions.
- **Discrepancy:** MUSE's own text (§4.3 RQ3) says the best closed models reach "about 19–21%" on the fine-grained criteria. Its Table 3 shows GPT-5.5 at 54.72 / 48.58 / 53.77% and Claude Opus 4.7 at 42.92 / 36.79 / 38.68%. The secondary report repeated the text figure; I cite the table.

### 11. Deliverable (a): method → intervention → measured effect → applicability

| Method / paper | Intervention | Measured effect (metric, dataset, table) | Applicability to Claude Code + build123d |
|---|---|---|---|
| CADCodeVerify (ICLR'25) | VLM writes yes/no questions, answers them from 4 renders, refines code | GPT-4 few-shot PC-dist 0.155→0.127 "Best Refine", compile 96.0→96.5% (CADPrompt, T2). Answer accuracy 64.6–68.2% (T9). Round 2 often worse (T5–7) | Medium. Use questions as a *checklist generator*, not as a judge. Keep numeric checks primary |
| CADCodeVerify geometric-solver baseline | Feed back 13 measured properties vs target | Best PC-dist in every GPT-4/Gemini setting (0.103 vs 0.127, T2). Hurts CodeLlama | **High.** Forge has spec targets; measured-vs-spec deltas are the Forge equivalent |
| CADSmith | Kernel metrics + 3-view render + separate Opus judge + RAG + escalation | Median IoU 0.8085→0.9629; mean CD 28.37→0.74; exec 95→100% (own 100 prompts, T-I). Vision needed for complex parts (T3 mean CD 49.68 without vs 1.42 with) | **High.** Nearly the Forge architecture already (CadQuery → build123d) |
| CADTests (+Log) | Executable B-rep tests from the prompt, ReAct on failures, log intermediate state | Claude PR (detailed) 0.580 (ReAct) → 0.625; RS 0.874→0.897 (CADPrompt, T3). Test AUC vs humans 0.928 vs CD 0.663 (T4) | **Very high.** This is "requirements as executable tests". Harden tests with mutants |
| ReAct / execution-error feedback | Feed tracebacks back | Claude IR 0.155→0 (CADTests T3); CAD-Judge IR 2.62→1.38, CD flat (T5) | High for validity; no effect on accuracy |
| Multi-view render feedback | Add renders to the loop | CADTests: none (abstract PR 0.695 = 0.695). Hephaestus: Opus mixed, GPT +6.3 pts req-pass. CADSmith: essential on complex parts | Medium. Use for structure / identity on complex parts, not for dimensions |
| Separate VLM critic (Seek-CAD, ICLR'26) | Gemini critiques R1's step renders | IoGT 0.6183→0.7347, but Pass@2 0.77→0.55 over 2 rounds (T2) | Low–medium. Guard compile validity; cap rounds |
| Consensus selection | Sample N, pick geometric medoid | CD 0.0610 vs VLM verifier 0.0627 vs random 0.0631 (CADPrompt, T1); plateaus near N≈9 | Medium. Cheap fallback when there is no spec check; costs N× tokens |
| Programmatic constraint checker (CAD-Assistant, ICCV'25) | Add a checker tool | PF1 0.747→0.979 (T5) | High. Build a sketch/constraint checker |
| Evidence-driven checking (ReliCAD) | Kernel/runtime evidence vs visual-only | Validity 99.8 vs 92.3%; CD 0.12 vs 30.77 (T-III) | High |
| FEA feedback (Hephaestus-CCX) | CalculiX typed pass/fail → margins + load case | Req-pass +13.4 pts avg per round (−1.3 to +30.9); long loop 38.8→60.5%, 9/50 strict (Fig. 1). 0 strict on first attempt (T2) | **High** for Forge's physics-in-the-loop. Return margins, not verdicts |
| FEA vs vision only (Physics-in-the-Loop) | Remove FEA, keep VLM review | In-band safety factor 59.0% vs 22.2%, p=0.0008 (T4) | High. Vision review cannot replace analysis |
| Code-compliance checker (structural) | FE + code checker → hard constraints | Compliance 56.8→98.6% (T5–6) | High pattern (checker → hard constraint) |
| Clarify before generating (ProCAD, ICML'26) | Audit spec, ask targeted questions | Mean CD ×10³ 7.80 (Claude Sonnet 4.5) → 0.63; IR 14.6→0.9% (T4). Weak clarifiers worse | **High.** A spec gate before CAD; the clarifier must be strong |
| Explicit dimensions / bbox in prompt (CADFS, CVPR'26) | Give target bbox | CD 0.58→0.14; IR 14→9 (T7) | High. Put numbers in the spec |
| build123d-mcp (CADGenBench) | Stepwise build, measure, validate, snapshots | Opus 5.5 xhigh 0.7520→0.8049, validity 92.6→100% (single unvalidated runs) | High relevance, weak-moderate evidence |
| RL with geometric reward (cadrille, CAD-Coder, CAD-RL) | Train on IoU/CD/exec rewards | IR→≈0–1%; +3–9 IoU (cadrille T3); CD reward hacking on thin parts (CAD-Coder App. F) | Low (no fine-tuning in Forge). Lesson: reward/metric gaming is real |
| Harness wrap (Claude Code on RealCADBench) | General coding agent vs bare model | PA +0.0006; surface IoU 0.1058→0.0864 (T5, n=25) | Caution: a generic agent loop without CAD-specific checks adds ~nothing |

### 12. Deliverable (b): what actually improves outcomes (ranked, evidence-backed)

1. **Check the numbers against the spec, with executable geometry tests, and treat them as the acceptance gate.**
   - B-rep tests for dimensions, counts, volumes, positions and connectivity. Evidence: CADTests (AUC 0.928 vs CD 0.663); CADSmith; ReliCAD; CAD-Assistant (0.747 → 0.979); CADCodeVerify's geometric-solver baseline beating visual QA.
   - Strength: **strong and consistent** across ≥5 independent groups.
2. **Feed execution errors back until the code runs (≤3 tries), and never count "it runs" as success.**
   - Invalid rate reaches about 0 in CADTests, CADSmith and CAD-Judge.
   - BenchCAD, RealCADBench, MUSE and CADGenBench all show validity is necessary but far from sufficient.
   - Strength: **strong**.
3. **Resolve the spec before generating: extract numbers, ask about what is missing or conflicting, and put explicit dimensions in the brief.**
   - ProCAD (CD ×10³ 7.80 → 0.63); CADFS (bbox in prompt: CD 0.58 → 0.14); wrong-intent conditioning hurts (low weight).
   - Strength: **moderate-strong**, from filtered test sets.
4. **Return quantitative, localised feedback (margins, offending feature or load case), not pass/fail.**
   - Hephaestus: the second large jump came when feedback switched to margins plus location (confounded with attempt number).
   - Physics-in-the-Loop: safety factor plus hotspots. Geometric-solver numbers beat VLM Q&A.
   - Strength: **moderate**.
5. **Physics in the loop for any requirement that is physical (stress, deflection, modal, mass).**
   - FEA vs no FEA: 22% → 59% in-band. First attempts pass 0 of 50 briefs strictly. Loops reach 9/50 strict passes after about 68 min per item.
   - Strength: **moderate**, from small samples. The payoff grows with how specific the feedback is.
6. **Build in steps and inspect intermediate state.**
   - CADTests + Log beats CADTests (PR 0.590 → 0.625).
   - build123d-mcp's stepwise loop is associated with a validity gain.
   - CADReasoner and RA-CAD use state-aware iteration.
   - Strength: **moderate / suggestive**; not isolated from "more feedback".
7. **Use render inspection for structure and identity on complex parts, driven by questions or a checklist and judged by a separate model — never for dimensions.**
   - CADSmith needed vision for T3 false convergence.
   - CADCodeVerify: removing renders hurt (0.126 → 0.153).
   - CADTests and Hephaestus-Opus show little or mixed gain from renders.
   - Strength: **mixed**, dependent on part complexity.
8. **Cap refinement rounds (about 2–3 without new information), keep the best-so-far, and escalate strategy rather than repeat.**
   - Gains level off after round 1 (Query2CAD, Seek-CAD, CAD-Judge).
   - Round 2 is often worse (CADCodeVerify T5–7; Seek-CAD Pass@2 → 0.55).
   - CADSmith escalates to a new strategy at iteration 3.
   - Strength: **strong** for "cap and keep best"; weak for "escalate".
9. **Keep maker ≠ checker, especially for any VLM judgement.**
   - VLM self-grading inflation: Claude Sonnet 4.5 rated its own acceptance 0.53 vs human 0.05 (neuralCAD-Edit).
   - No controlled maker-vs-self study exists. Indirect evidence says *what* is checked (numbers) matters more than *who* checks.
   - Strength: **moderate**.
10. **Snapshot before risky operations.**
    - Supported by practice (build123d-mcp save/restore; CADReasoner and CIT-CAD keep the best or reject regressions via monotonic acceptance).
    - No measured ablation. Strength: **weak / engineering hygiene**. Cheap, so adopt it.

### 13. Deliverable (c): what doesn't help, or has weak evidence

- **Same-model visual self-critique without numbers:**
  - 3D-PreMise-style feedback *lowered* compile rate (92.0 → 89.5%).
  - VLM Q&A answers are about 65% correct.
  - GPT-4V iterating on renders did not improve CAD ("From Concept to Manufacturing").
  - LLM reading stress-field images added no significant gain (IterSIMP-σ, p = 0.382).
- **More views:** 7 views often match 21 (Hephaestus T6–7). Render feedback gave no gain in CADTests.
- **More reasoning effort:** not monotonic (Hephaestus: high > xhigh; xhigh > max).
- **Generic agent wrappers with no CAD-specific checks:** Claude Code + Opus 4.8 on RealCADBench, PA +0.0006.
- **Doc retrieval or "skill" guideline files for code accuracy:** no clean ablation; CADTests "Skilled" ≈ 10-shot.
- **Chamfer distance / normalised IoU as acceptance metrics:** blind to absolute scale and poorly aligned with humans. It is also exploitable (reward hacking on thin parts).
- **Fine-tuned specialist models outside their distribution:**
  - Text2CAD underperforms prompted LLMs.
  - cadrille produced degenerate outputs on CADTestBench.
  - CAD-Coder lost fillet ability.
- **Driving a CAD GUI instead of writing code:** 0 complete builds in VideoCAD.

### 14. Deliverable (d): open risks for Forge

1. **Checker gaming.** Agents pass checkers by fixing metadata or aliases rather than physics (Hephaestus T4) and by reward hacking (CAD-Coder App. F). Mitigations:
   - Checkers must be independent of the maker.
   - Test suites need mutation testing.
   - Physics checks must bind to geometry, not declared fields.
2. **Checks with coverage gaps.** LLM-written tests killed only about 63–65% of mutants before hardening (CADTests T1). The CADSmith quadcopter passed every check with disconnected arms. Mitigations:
   - Run mandatory invariant checks on every part: single solid / connectivity, watertight, no overlaps.
   - Mutation-score each requirement suite.
3. **Assemblies and interfaces are the weakest area.** Evidence: MUSE overlap-free is the biggest drop; RealCADBench assembly IoU 0.2290; zero strict FEA passes on multi-part briefs; vendors lack mates. Forge needs explicit interface / keep-out checks (CADGenBench-style interface match) and clearance checks.
4. **Industrial parametrics.** Standards-driven features such as spring ends, involute gears and threads fail (BenchCAD). Forge should prefer vetted parametric libraries (e.g. bd_warehouse-type components) over free-form generation for standard parts. That is my inference [U]; no source measured it.
5. **Benchmark overfitting and weak external validity.** Most evidence is on toy or DeepCAD-like parts. CADGenBench top rows are unvalidated and the test set can be hill-climbed. Forge needs its own held-out regression suite with measured tolerances.
6. **Cost and latency.**
   - About $725 API-equivalent per 79-fixture Opus 5 sweep.
   - About 68 min per item for the best FEA loop.
   - Kernel checking takes up to 40% of loop time (Intrinsic Selection).
   - Budget accordingly and stop loops when they stop gaining.
7. **Model-version drift dominates harness effects.** CADGenBench: model generations moved scores about 0.4; harness changes about 0.05. Forge must re-run its regression suite on every model change and not bake in model-specific assumptions.
8. **Name collisions.**
   - "Forge" (satvikOS/Forge, a CAD app; "Archie in Forge" is on CADGenBench), ForgeCAD and IndustryForge already exist in this space.
   - Paper names collide too: two "CAD-Coder" papers, two "CADBench" benchmarks, two "IterCAD" papers.

## Implications for Forge

1. **Acceptance = executable requirement tests (build123d/OCCT measurements) + mandatory invariants**, never "it runs" or "it looks right".
   - Invariants: valid, watertight, one connected solid unless the spec says otherwise, no overlaps.
   - Tests are written from the spec before the CAD, by a different agent from the maker, and mutation-hardened (seeded wrong dimensions, missing holes) before they are trusted.
2. **Numbers first, pictures second.** Every check emits measured vs specified values with tolerance and margin. Renders feed a separate structure / identity review, never dimensional acceptance.
3. **Spec gate before any CAD.** Extract a numeric spec (dimensions, tolerances, interfaces, loads, materials). A strong model asks targeted clarification questions for missing or conflicting values and records its assumptions. No generation proceeds on an ambiguous spec.
4. **Build → measure loop per feature.** After each feature: execute, measure, compare with the spec slice. Snapshot before booleans, fillets and shells. Roll back on regression (monotonic acceptance).
5. **Repair budgets.** At most 3 execution-repair attempts per step. At most 2–3 geometric refinement rounds without new evidence. Keep best-so-far. After a repeated failure, escalate to a different construction strategy or to a human; don't loop.
6. **Physics as a checker with rich feedback.** For load-bearing parts, run FEA (e.g. CalculiX) as an independent checker that returns margins, locations and load cases. Numeric optimization (sizing) goes to a solver or optimizer, not the LLM.
7. **Assemblies need interface contracts.** Keep-in / keep-out volumes, hole-pattern alignment, clearance and interference checks for mating parts (CADGenBench-style interface match).
8. **Separate maker and checker.** VLM judgements must never be self-graded. Log checker verdicts as artifacts, so verification is itself the product.
9. **Forge's own regression benchmark.** Held-out parts with tolerance-based metrics, not scale-normalised CD. Consider submitting to CADGenBench as an external sanity check, but don't tune on it.
10. **Prefer build123d with an MCP-style measuring toolset.** Precedent: build123d-mcp and the CADGenBench reference agent. Reuse vetted parametric part libraries for standard components.

## Not found / discrepancies

- **"CADGenBench"** exists, but as a Hugging Face benchmark and leaderboard (GitHub huggingface/cadgenbench, created 2026-05-27), **not a paper** [V].
- **"BenchCAD"** exists (arXiv 2605.10865) [V].
- **"CADBench"** is two unrelated benchmarks: BlenderLLM (2412.14203, Blender Python) and Doris et al. / MIT (2605.10873). **"CAD-Bench"** (hyphenated) was not found.
- **The single "2026 valid-but-wrong paper"** was not found. The finding is spread across BenchCAD, RealCADBench, MUSE, Text2CAD-Bench, CADTests, neuralCAD-Edit, Hephaestus-CCX, CADGenBench and Pointer-CAD v2 (§3).
- **CADCodeVerify**
  - The arXiv listing abstract says "5.0% improvement in success rate"; the v2 PDF says "5.5% … compile rate". Both headline gains are relative to 3D-Premise, not to unrefined output.
  - "Best Refine" is undefined, so oracle selection is possible [U].
- **MUSE:** text (§4.3, "about 19–21%") contradicts its Table 3 (GPT-5.5 about 49–55%).
- **Text2CAD-Bench:** CD/IoU computed on executed samples only (survivorship bias; the authors flag it). Some Table 1 values repeat across cells (e.g. 88.57, 12.8%), which is possibly a typo.
- **Physics-in-the-Loop (2605.19717):** abstract vs body disagree (4.2× vs about 3.4× complexity; 3.5% vs 3.4%) [V, sub-researcher].
- **LLM4CAD** is by Li, Sun and Sha (UT Austin), not DeCoDE. CAD-Llama is Fudan. No DeCoDE design-intent or text-to-CAD benchmark paper exists.
- **Name collisions**
  - Two "CAD-Coder" papers (Doris et al. 2505.14646, image→CadQuery; Guan et al. 2505.19713, text→CadQuery with GRPO).
  - Two "IterCAD" papers (2606.13368; 2608.24020, ACM MM 2026).
  - CAD-RL is the method; ExeCAD is the dataset (2508.10118).
- **Other paper discrepancies** [V, sub-researchers]
  - RA-CAD quotes CADFusion's IR as 21.98 vs CADFusion's own 6.20.
  - CAD-Judge Table 3 vs Table 5 mismatch.
  - ProCAD's abstract says 79.9%; the table gives 79.7%.
  - VideoCAD mislabels a symmetry score as depth estimation.
- **Leaderboard / tool claims**
  - The "0.06 gap is meaningful" CADGenBench rule appears only in a search snippet [R], not in the primary docs.
  - build123d-mcp's "0.360 → 0.457" claim compares runs on different data revisions and effort settings.
- **Not found at all**
  - Any public benchmark of Zoo, Adam, Backflip, Autodesk neural CAD or Leo.
  - Any head-to-head LLM study of build123d vs CadQuery vs OpenSCAD.
  - Any clean doc-retrieval ablation for CAD code.
  - Any CFD, thermal or kinematic CAD agent with a no-physics control.
  - Any controlled maker-vs-self-critic study.
- **Other discrepancies found**
  - Text2CAD-Bench says PythonOCC is built on the "OpenSCAD kernel"; it is built on OpenCASCADE.
  - CADDesigner gives ECIP Pass@1 as 0.45 in one table and 0.46 in another [V, sub-researcher].
- **Process limits:** the web search budget ran out and the arXiv API rate-limited partway through the research. Coverage of Katalyst, PTC Creo AI, and CFD/thermal agents is thin.

## Sources

| # | Title | Authors | Venue / year | ID / URL | Type | Accessed |
|---|---|---|---|---|---|---|
| 1 | Generating CAD Code with Vision-Language Models for 3D Designs (CADCodeVerify, CADPrompt) | Alrashedy, Tambwekar, Zaidi et al. | ICLR 2025 | [2410.05340](https://arxiv.org/abs/2410.05340) | paper | 2026-09-25 |
| 2 | BenchCAD | Zhang, Liu, Chen et al. | arXiv 2026 | [2605.10865](https://arxiv.org/abs/2605.10865) | paper | 2026-09-25 |
| 3 | CADGenBench (repo, metrics docs, leaderboard results.jsonl) | Hugging Face (HuggingAI4Engineering) | 2026 | [github](https://github.com/huggingface/cadgenbench), [HF data](https://huggingface.co/datasets/HuggingAI4Engineering/cadgenbench-submissions) | benchmark / data | 2026-09-25 |
| 4 | CADBench: Multimodal Benchmark for AI-Assisted CAD Program Generation | Doris, Sony, Nehme, …, Ahmed | arXiv 2026 | [2605.10873](https://arxiv.org/abs/2605.10873) | paper | 2026-09-25 |
| 5 | BlenderLLM (CADBench, Blender) | Du, Chen, Zan et al. | arXiv 2024 | [2412.14203](https://arxiv.org/abs/2412.14203) | paper | 2026-09-25 |
| 6 | Text2CAD | Khan, Sinha, Sheikh et al. | NeurIPS 2024 | [2409.17106](https://arxiv.org/abs/2409.17106) | paper | 2026-09-25 |
| 7 | Text2CAD-Bench | Wang, Meng, Xiang et al. | arXiv 2026 | [2605.18430](https://arxiv.org/abs/2605.18430) | paper | 2026-09-25 |
| 8 | Text-to-CAD Evaluation with CADTests | Mallis, Wang, Karadeniz et al. | arXiv 2026 | [2605.07807](https://arxiv.org/abs/2605.07807) | paper | 2026-09-25 |
| 9 | MUSE | Dong, Li, Wu | arXiv 2026 | [2605.28579](https://arxiv.org/abs/2605.28579) | paper | 2026-09-25 |
| 10 | RealCADBench | Li, Huang, Yu et al. | arXiv 2026 | [2609.03773](https://arxiv.org/abs/2609.03773) | paper | 2026-09-25 |
| 11 | neuralCAD-Edit | Perrett, Bouchard, McCarthy (Autodesk Research) | arXiv 2026 | [2604.16170](https://arxiv.org/abs/2604.16170) | paper | 2026-09-25 |
| 12 | Self-Improving CAD Generation Agents with FEA as Feedback | Son, Park, Park et al. | arXiv 2026 (WIP) | [2605.17448](https://arxiv.org/abs/2605.17448) | paper | 2026-09-25 |
| 13 | CADSmith | Barkley, Loghmani, Barati Farimani | arXiv 2026 | [2603.26512](https://arxiv.org/abs/2603.26512) | paper | 2026-09-25 |
| 14 | Pointer-CAD v2 | Qi, Wang, Xu et al. | ECCV 2026 | [2606.29301](https://arxiv.org/abs/2606.29301) | paper | 2026-09-25 |
| 15 | HistCAD | Dong, Li, Zheng et al. | arXiv 2026 | [2602.19171](https://arxiv.org/abs/2602.19171) | paper (abstract) | 2026-09-25 |
| 16 | Wrong Design Intent Is Worse Than Never Conditioning | Xiao | arXiv 2026 | [2607.23191](https://arxiv.org/abs/2607.23191) | paper (abstract) | 2026-09-25 |
| 17 | Query2CAD | Badagabettu, Yarlagadda, Barati Farimani | arXiv 2024 | [2406.00144](https://arxiv.org/abs/2406.00144) | paper | 2026-09-25 |
| 18 | CAD-Recode | Rukhovich, Dupont, Mallis et al. | ICCV 2025 | [2412.14042](https://arxiv.org/abs/2412.14042) | paper | 2026-09-25 |
| 19 | cadrille | Kolodiazhnyi, Tarasov, Zhemchuzhnikov et al. | ICLR 2026 | [2505.22914](https://arxiv.org/abs/2505.22914) | paper | 2026-09-25 |
| 20 | CAD-Coder (text, GRPO) | Guan, Wang, Xing et al. | NeurIPS 2025 | [2505.19713](https://arxiv.org/abs/2505.19713) | paper | 2026-09-25 |
| 21 | From Intent to Execution (CAD-RL / ExeCAD) | Niu, Yu, Chen et al. | AAAI 2026 | [2508.10118](https://arxiv.org/abs/2508.10118) | paper | 2026-09-25 |
| 22 | TOOLCAD | Gong, Wu, Liu, Tu | ACL 2026 | [2604.07960](https://arxiv.org/abs/2604.07960) | paper | 2026-09-25 |
| 23 | CADReasoner | Kabisov, Kirichuk, Volkov et al. | arXiv 2026 | [2603.29847](https://arxiv.org/abs/2603.29847) | paper | 2026-09-25 |
| 24 | CADEvolve | Elistratov, Barannikov, Ivanov et al. | arXiv 2026 | [2602.16317](https://arxiv.org/abs/2602.16317) | paper | 2026-09-25 |
| 25 | CADFS | Pyatov, Bobrovskikh, Galochkin et al. | CVPR 2026 | [2605.01925](https://arxiv.org/abs/2605.01925) | paper | 2026-09-25 |
| 26 | CAD-Coder (image, open-source VLM) | Doris, Alam, Heyrani Nobari, Ahmed | IDETC 2025 / JMD 2026 | [2505.14646](https://arxiv.org/abs/2505.14646) | paper | 2026-09-25 |
| 27 | DesignQA | Doris, Grandi, Tomich et al. | JCISE 2025 | [2404.07917](https://arxiv.org/abs/2404.07917) | paper | 2026-09-25 |
| 28 | MCERF | Naghavi Khanghah, Nguyen, Doris et al. | JMD 2026 | [2604.09552](https://arxiv.org/abs/2604.09552) | paper | 2026-09-25 |
| 29 | VideoCAD | Man, Nehme, Alam et al. | NeurIPS 2025 | [2505.24838](https://arxiv.org/abs/2505.24838) | paper | 2026-09-25 |
| 30 | From Concept to Manufacturing | Picard, Edwards, Doris et al. | AI Review 2025 | [2311.12668](https://arxiv.org/abs/2311.12668) | paper | 2026-09-25 |
| 31 | CADFit | Nehme, Whalen, Ahmed | ICML 2026 | [2605.01171](https://arxiv.org/abs/2605.01171) | paper | 2026-09-25 |
| 32 | Intrinsic Selection and Particle Resampling | Giannone, Eyceoz, Baig et al. | arXiv 2026 | [2606.08850](https://arxiv.org/abs/2606.08850) | paper | 2026-09-25 |
| 33 | RA-CAD | Yan, He, Hu et al. | arXiv 2026 | [2608.05714](https://arxiv.org/abs/2608.05714) | paper | 2026-09-25 |
| 34 | CAD-Assistant | Mallis, Karadeniz, Cavada et al. | ICCV 2025 | [2412.13810](https://arxiv.org/abs/2412.13810) | paper | 2026-09-25 |
| 35 | Seek-CAD | Li, Li, Song et al. | ICLR 2026 | [2505.17702](https://arxiv.org/abs/2505.17702) | paper | 2026-09-25 |
| 36 | CAD-Judge | Zhou, Han, Du et al. | ICASSP 2026 | [2508.04002](https://arxiv.org/abs/2508.04002) | paper | 2026-09-25 |
| 37 | Test-Time Scaling via Verifier-Free Consensus Selection | Haag, Kacan, Fuchs et al. | arXiv 2026 | [2608.09706](https://arxiv.org/abs/2608.09706) | paper | 2026-09-25 |
| 38 | CIT-CAD | Du, Sun, Xi et al. | arXiv 2026 | [2609.07434](https://arxiv.org/abs/2609.07434) | paper | 2026-09-25 |
| 39 | CADFusion (Text-to-CAD via Visual Feedback) | Wang, Yuan, Sun, Bian | ICML 2025 | [2501.19054](https://arxiv.org/abs/2501.19054) | paper | 2026-09-25 |
| 40 | 3D-PreMise | Yuan, Lan, Zou et al. | arXiv 2024 | [2401.06437](https://arxiv.org/abs/2401.06437) | paper | 2026-09-25 |
| 41 | ExpConCAD | Liu, Tang, Huang et al. | arXiv 2026 | [2608.24760](https://arxiv.org/abs/2608.24760) | paper | 2026-09-25 |
| 42 | Clarify Before You Draw (ProCAD) | Yuan, Zhao, Molodyk et al. | ICML 2026 | [2602.03045](https://arxiv.org/abs/2602.03045) | paper | 2026-09-25 |
| 43 | ReliCAD | Zheng, Dong, Li et al. | arXiv 2026 | [2609.22325](https://arxiv.org/abs/2609.22325) | paper | 2026-09-25 |
| 44 | IterCAD (agent) | Hu, Ai, Wen et al. | arXiv 2026 | [2606.13368](https://arxiv.org/abs/2606.13368) | paper | 2026-09-25 |
| 45 | Physics-in-the-Loop: Hybrid Agentic Architecture | Berger, Usama, Mehlstäubl | IJCAI-ECAI 2026 (per arXiv) | [2605.19717](https://arxiv.org/abs/2605.19717) | paper | 2026-09-25 |
| 46 | Verification-driven closed-loop structural design | Luo, Lin, Lin | arXiv 2026 | [2608.07978](https://arxiv.org/abs/2608.07978) | paper | 2026-09-25 |
| 47 | MechStyle | Faruqi, Abdel-Rahman, Nisser et al. | ACM SCF 2025 | [2509.20571](https://arxiv.org/abs/2509.20571) | paper | 2026-09-25 |
| 48 | IterSIMP-σ | Yang, Wang, Wang | arXiv 2026 | [2605.19110](https://arxiv.org/abs/2605.19110) | paper | 2026-09-25 |
| 49 | RocketBench (LLMs for Engineering) | Simonds | arXiv 2025 | [2504.19394](https://arxiv.org/abs/2504.19394) | paper | 2026-09-25 |
| 50 | build123d-mcp; cadgenbench-build123d | P. Fremantle (pzfreo) | GitHub 2026 | [build123d-mcp](https://github.com/pzfreo/build123d-mcp), [cadgenbench-build123d](https://github.com/pzfreo/cadgenbench-build123d) | practitioner tool | 2026-09-25 |
| 51 | We Tested 7 Text-to-CAD Tools | U. Krayneva, Xometry Pro | 2025 | xometry.pro/en-eu/articles/text-to-cad-tools-test/ | independent test [via sub-researcher] | 2026-09-25 |
| 52 | Text to CAD? | Mechanomy (Substack) | 2024 | mechanomy.substack.com/p/text-to-cad | independent test [via sub-researcher] | 2026-09-25 |
| 53 | Launch HN: Adam (YC W25) | HN thread | 2026 | news.ycombinator.com/item?id=48572553 | anecdotes [via sub-researcher] | 2026-09-25 |
| 54 | Zoo blog / FAQ (Text-to-CAD, KCL error rate) | Zoo | 2023–2026 | zoo.dev | vendor claim [via sub-researcher] | 2026-09-25 |
| 55 | Autodesk shows its AI hand; Is neural CAD worth getting excited about? | G. Corke (DEVELOP3D); M. Alba (Engineering.com) | 2025 | develop3d.com; engineering.com | reported demo / opinion [via sub-researcher] | 2026-09-25 |
| 56 | CADDesigner: Conceptual CAD Model Generation with a General-Purpose Agent | Fan, Ni, Yin et al. | arXiv 2026 | [2508.01031](https://arxiv.org/abs/2508.01031) | paper [via sub-researcher] | 2026-09-25 |
| 57 | P3D-Bench | Yang, Hu, Lin et al. | arXiv 2026 | [2606.11152](https://arxiv.org/abs/2606.11152) | paper [via sub-researcher] | 2026-09-25 |
| 58 | A Solver-Aided Hierarchical Language for LLM-Driven CAD Design (AIDL) | Jones, Hähnlein, Zhang et al. | arXiv 2025 | [2502.09819](https://arxiv.org/abs/2502.09819) | paper [via sub-researcher] | 2026-09-25 |
| 59 | IterCAD: Iterative Program Repair for CAD Code Generation from Orthographic Views | Wu, Niu, Yu et al. | ACM MM 2026 | [2608.24020](https://arxiv.org/abs/2608.24020) | paper [via sub-researcher] | 2026-09-25 |
