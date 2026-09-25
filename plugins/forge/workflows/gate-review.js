export const meta = {
  name: 'gate-review',
  description: 'Parallel specialist gate review -- forge:verification-evaluator, forge:red-team and any named specialists, each in a fresh context -- reconciled into one reviews/Gx.md record with a blank human sign-off line.',
  whenToUse: 'Invoked by the reviewing-designs skill when asked to review a project for a stage gate (G0-G6). Never passes a gate itself: it only produces the reconciled report and a recommendation for a human to sign.',
  phases: [
    { title: 'Review', detail: 'verification-evaluator, red-team and specialists review in parallel, each in a fresh context' },
    { title: 'Reconcile', detail: 'merge verdicts into one Gx.md gate record with a blank human sign-off line' },
  ],
}

// ---- inputs -----------------------------------------------------------
// args: {
//   project: string,          // path to the product repo being reviewed
//   gate: string,              // "G0".."G6"
//   specialists?: string[],    // extra forge:<name> agents to run in review mode (e.g. "mechanical-engineer")
//   subject?: string,          // short human label for what's under review (default: gate + project)
// }

const project = args && args.project
const gate = args && args.gate
const specialists = (args && Array.isArray(args.specialists)) ? args.specialists : []
const subject = (args && args.subject) || `${gate || '?'} review of ${project || '?'}`

if (!project || !gate) {
  throw new Error('gate-review requires args: { project: "<path>", gate: "G0".."G6", specialists?: [...] }')
}
if (!/^G[0-6]$/.test(gate)) {
  throw new Error(`gate-review: gate must be one of G0..G6, got ${JSON.stringify(gate)}`)
}

// ---- phase 1: parallel reviews, each in a fresh context ----------------
phase('Review')

// Mirrors plugins/forge/schemas/verdict.schema.json (forge.verdict/1) exactly, field for
// field, so a reviewer's structured output here is already shaped the way the real
// SubagentStop hook will re-validate it -- this workflow's own schema is a convenience,
// not the enforcement point.
const VERDICT_SCHEMA = {
  type: 'object',
  required: ['schema', 'reviewer', 'gate', 'subject', 'criteria', 'overall', 'summary', 'not_checked'],
  properties: {
    schema: { const: 'forge.verdict/1' },
    reviewer: { type: 'string', minLength: 2 },
    gate: { type: 'string', enum: ['G0', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'adhoc'] },
    subject: { type: 'string', minLength: 2 },
    criteria: {
      type: 'array',
      minItems: 1,
      items: {
        type: 'object',
        required: ['id', 'verdict', 'evidence', 'finding'],
        properties: {
          id: { type: 'string', minLength: 2 },
          verdict: { type: 'string', enum: ['PASS', 'FAIL', 'BLOCKED'] },
          evidence: { type: 'array', items: { type: 'string' } },
          finding: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          affects: {
            type: 'array',
            minItems: 1,
            items: { type: 'string', enum: ['requirements', 'safety', 'fit', 'function', 'manufacturability', 'cost'] },
          },
        },
      },
    },
    overall: { type: 'string', enum: ['PASS', 'FAIL', 'BLOCKED'] },
    summary: { type: 'string' },
    not_checked: { type: 'array', items: { type: 'string' } },
  },
}

function reviewPrompt(role) {
  return (
    `You are reviewing the project at "${project}" for stage gate ${gate} ("${subject}"), in REVIEW MODE ONLY. ` +
    `You are NOT the agent that built this -- read requirements/requirements.md, requirements/trace.json, ` +
    `evidence/manifest.json, out/verify/*.json, params/params.toml, and the relevant domain directories ` +
    `(cad/, ecad/, firmware/, analysis/, mfg/, bom/, compliance/) with read-only tools. Never write or edit ` +
    `anything, and never run a build or a tool that mutates a file. ` +
    `Judge against gate ${gate}'s pass criteria (docs/standards/gates.md if present) and each requirement's ` +
    `stated Verify method. Every criterion you report MUST cite at least one evidence file path that actually ` +
    `exists (an out/verify/*.json check result or an evidence/manifest.json entry id) -- a claim with no ` +
    `evidence file is BLOCKED, never PASS. Report only defects that affect requirements, safety, fit, ` +
    `function, manufacturability or cost; put style-only notes in the summary, never as a criterion. ` +
    `List anything you could not check in 'not_checked' rather than silently skipping it. ` +
    `Your role in this review: ${role}. ` +
    `Finish your final message with exactly one fenced \`\`\`json block matching plugins/forge/schemas/` +
    `verdict.schema.json (forge.verdict/1) exactly: {schema: "forge.verdict/1", reviewer: "${role}", ` +
    `gate: "${gate}", subject: "${subject}", criteria: [{id, verdict, evidence, finding, severity, affects}], ` +
    `overall, summary, not_checked}. Every criterion needs a non-empty 'evidence' array (cite the file paths); ` +
    `a FAIL criterion additionally needs 'severity' and a non-empty 'affects'. Include 'not_checked' as an ` +
    `array even when empty. 'overall' is PASS only if every criterion is PASS.`
  )
}

const reviewers = [
  { role: 'verification-evaluator', agentType: 'forge:verification-evaluator' },
  { role: 'red-team', agentType: 'forge:red-team' },
  ...specialists.map((s) => ({ role: s, agentType: `forge:${s}` })),
]

const verdicts = (await parallel(
  reviewers.map((r) => () => agent(
    reviewPrompt(r.role),
    { phase: 'Review', schema: VERDICT_SCHEMA, agentType: r.agentType, label: r.role }
  ))
)).filter(Boolean)

if (!verdicts.length) {
  throw new Error('gate-review: every reviewer failed or returned nothing; nothing to reconcile')
}

log(`${verdicts.length}/${reviewers.length} reviewer(s) returned a forge.verdict/1 block.`)

// ---- phase 2: reconcile into one gate record, sign-off left blank ------
phase('Reconcile')

const reconcilePrompt = (
  `Reconcile these ${verdicts.length} reviewer verdicts for "${project}" gate ${gate} ("${subject}") into one ` +
  `gate record.\n\nVerdicts (JSON): ${JSON.stringify(verdicts)}\n\n` +
  `Read templates/project/reviews/_gate-template.md relative to the Forge plugin/repo root if it exists; ` +
  `otherwise use plugins/forge/skills/reviewing-designs/references/gate-record-template.md as the template. ` +
  `Write the merged report to reviews/${gate}.md inside "${project}" with: a criteria table that is the union ` +
  `of every reviewer's criteria (each row shows its verdict and which reviewer(s) raised it -- if reviewers ` +
  `disagree on the same criterion id, show both verdicts, don't silently pick one), evidence links, the ` +
  `verification-evaluator verdict JSON block verbatim, the red-team verdict JSON block verbatim, any ` +
  `specialist verdicts verbatim, an "Open risks" section drawn from every "FAIL"/"BLOCKED" criterion and every ` +
  `red-team finding, and a one-paragraph recommendation (PASS/FAIL/BLOCKED) that is explicitly a ` +
  `recommendation, not a decision. End the file with EXACTLY this literal line, left blank -- ` +
  `never fill in a name, date or decision yourself, under any circumstance: ` +
  `"Human sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL". ` +
  `Return the path you wrote and the overall recommendation you put in it.`
)

const reconciliation = await agent(reconcilePrompt, { phase: 'Reconcile', label: 'reconcile' })

const anyFail = verdicts.some((v) => v.overall === 'FAIL')
const anyBlocked = verdicts.some((v) => v.overall === 'BLOCKED')
const overallRecommendation = anyFail ? 'FAIL' : anyBlocked ? 'BLOCKED' : 'PASS'

log(`Gate review reconciled: recommendation ${overallRecommendation} (${verdicts.length} reviewer(s)). ` +
  'The sign-off line was left blank -- only a human can pass this gate.')

return {
  schema: 'forge.gate_review/1',
  project,
  gate,
  subject,
  reviewers: reviewers.map((r) => r.role),
  verdicts,
  overall_recommendation: overallRecommendation,
  reconciliation,
}
