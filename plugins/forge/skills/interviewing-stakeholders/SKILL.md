---
name: interviewing-stakeholders
description: Turn a fuzzy product idea into a structured SPEC.md through a real stakeholder interview -- user needs, jobs-to-be-done, success metrics, constraints and explicit non-goals -- using AskUserQuestion rather than guessing. Use at the very start of a new project, when the user describes a product idea in a paragraph and asks "help me figure out what to build", or when SPEC.md is missing or stale. Do NOT use once SPEC.md exists and is current (go straight to writing-requirements), and do NOT use this to write EARS requirements yourself -- that is writing-requirements's job, downstream of this interview.
allowed-tools: Read, Write, Edit, AskUserQuestion, Glob
---

# Interviewing stakeholders

**Non-negotiable rules, read first:**
1. Never invent user needs, success metrics or constraints. If the brief doesn't say, **ask** — that's what `AskUserQuestion` is for. The brief's own operating principle: "when a requirement is ambiguous, conflicting or missing a number, ask before designing."
2. Capture **non-goals** as explicitly as goals. A scope that only lists what's in is a scope that will quietly grow.
3. Every claimed need traces to something the stakeholder actually said (quote or close paraphrase) — not to what sounds plausible for "a product like this."
4. This skill produces `SPEC.md`, not `requirements/requirements.md`. Hand off to `writing-requirements` once SPEC.md is stable; don't try to write EARS sentences mid-interview.

## Interview structure

Work through these areas with `AskUserQuestion`, one focused batch of questions at a time (don't dump 20 questions at once):

1. **Who and why.** Who is the user? What job are they trying to get done? What do they do today without this product?
2. **Success metrics.** How will the stakeholder know this worked? Prefer numbers (cost target, time-to-X, adoption target) over adjectives.
3. **Constraints.** Budget ceiling, timeline, regulatory context (any medical/safety/radio claim triggers `mapping-compliance` later), must-use or must-avoid components/vendors, physical constraints (size, weight, power source).
4. **Scope.** What's explicitly in v1. What's explicitly **out** (non-goals) — write these down even if the stakeholder waves them off as "obviously not."
5. **Risks the stakeholder already knows about.** Anything they're worried could go wrong, technically or commercially.
6. **Open questions.** Anything neither of you can answer yet — record it in `ASSUMPTIONS.md`, not as a silently-resolved requirement.

## `SPEC.md` output (template in `references/spec-template.md`)

Sections: Problem & users, Jobs-to-be-done, Success metrics, Constraints, Scope (in/out), Known risks, Open assumptions, Stakeholder quotes (attribution for each captured need). Keep it prose plus short lists — this is not the requirements document.

## Workflow

1. Read any existing brief, prior SPEC.md, or linked material first — don't re-ask what's already written down.
2. Run the interview via `AskUserQuestion`, area by area, adapting follow-ups to what you hear rather than reading a fixed script.
3. Draft `SPEC.md` and read it back to the stakeholder (as text in the conversation) before treating it as final — a written misunderstanding compounds downstream.
4. Log anything genuinely unresolved in `ASSUMPTIONS.md` with an owner and a "resolve by" trigger (a gate, a date, or "before G0").
5. Hand off explicitly: tell the user requirements-writing starts next, via `writing-requirements`.

## What this skill refuses

- Writing a SPEC.md from a one-line prompt without asking anything. A single paragraph is a starting point for an interview, not a finished brief.
- Resolving a genuine unknown by picking the "reasonable default" and moving on silently. State the assumption in `ASSUMPTIONS.md` and flag it — don't let it disappear into the design.
- Writing requirements, choosing an architecture, or scoring concepts here — those are `writing-requirements`, `systems-engineer`'s SysML model, and `exploring-concepts`'s job respectively.
