export const meta = {
  name: 'concept-tournament',
  description: 'Generate N candidate concepts in parallel, score them independently on a weighted Pugh matrix (judges blind to authorship), and reconcile into a top-2 report.',
  whenToUse: 'Use from exploring-concepts for a G1/PDR-style design exploration. Returns a forge.pugh/1-shaped object -- the caller (main thread) writes it to concepts/pugh.json and runs exploring-concepts/scripts/verify.py to gate it. This workflow never writes files and never picks a winner; it only generates, judges and reconciles.',
  phases: [
    { title: 'Generate concepts', detail: 'independent agents each propose one distinct approach from the brief' },
    { title: 'Judge', detail: 'independent judges score every concept against the weighted criteria, blind to which agent wrote which' },
    { title: 'Reconcile', detail: 'average judge scores, rank, run the sensitivity check, and build the top-2 report' },
    { title: 'Pairwise compare', detail: 'a fresh judge directly compares the top-2 head-to-head as a sanity check on the matrix ranking' },
  ],
}

// ---- inputs -----------------------------------------------------------
// args: {
//   brief: string,                       // what problem the concepts solve
//   criteria: [{name, weight}],          // Pugh matrix criteria
//   datum: {name, description},          // baseline concept description (scored 0 by construction)
//   conceptCount?: number,               // default 4
//   judgeCount?: number,                 // default 3
//   topN?: number,                       // default 2
//   timestamp?: string,                  // caller-supplied; the script never calls a clock
// }

const brief = args && args.brief
const criteria = (args && args.criteria) || []
const datum = (args && args.datum) || { name: 'datum', description: 'the current baseline / do-nothing option' }
const conceptCount = (args && args.conceptCount) || 4
const judgeCount = (args && args.judgeCount) || 3
const topN = (args && args.topN) || 2
const timestamp = (args && args.timestamp) || 'unspecified'

if (!brief || !criteria.length) {
  throw new Error("concept-tournament needs args.brief and a non-empty args.criteria [{name, weight}]")
}

const criteriaNames = criteria.map(c => c.name)
const LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
const conceptLabels = Array.from({ length: conceptCount }, (_, i) => `Concept ${LABELS[i] || i + 1}`)

const scoreShape = {}
for (const name of criteriaNames) {
  scoreShape[name] = { type: 'integer', minimum: -2, maximum: 2 }
}

const CONCEPT_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    approach: { type: 'string' },
    summary: { type: 'string' },
  },
  required: ['name', 'approach', 'summary'],
}

const judgeScoreProps = {}
for (const label of conceptLabels) {
  judgeScoreProps[label] = {
    type: 'object',
    properties: scoreShape,
    required: criteriaNames,
  }
}
const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    scores: { type: 'object', properties: judgeScoreProps, required: conceptLabels },
    notes: { type: 'string' },
  },
  required: ['scores'],
}

// ---- phase 1: generate concepts in parallel, each from a distinct angle ----
phase('Generate concepts')

const angles = [
  'lowest cost / simplest possible approach, even if it trades off capability',
  'most manufacturable at volume, optimising for process fit and tolerances',
  'best user experience / ergonomics, even at some cost or complexity premium',
  'most robust / lowest-risk approach, minimising novel technology and single points of failure',
  'most differentiated / innovative approach worth a real trade-off to get',
  'fastest to build and validate, minimising schedule risk',
]

const criteriaSummary = criteria.map(c => `${c.name} (weight ${c.weight})`).join(', ')

const generated = (await parallel(
  Array.from({ length: conceptCount }, (_, i) => () => agent(
    `You are one of ${conceptCount} independent concept designers exploring solutions to this brief:\n\n` +
    `${brief}\n\n` +
    `The concepts will be judged on: ${criteriaSummary}, against this datum/baseline: ` +
    `"${datum.name}" -- ${datum.description}.\n\n` +
    `Propose ONE genuinely distinct concept, leaning toward this angle: ${angles[i % angles.length]}. ` +
    `Do not hedge into a generic middle-of-the-road option -- commit to a real, distinct approach. ` +
    `Give it a short descriptive name (not "Concept 1"), a one-paragraph approach, and a one-paragraph summary ` +
    `of its key trade-offs against the datum.`,
    { schema: CONCEPT_SCHEMA, phase: 'Generate concepts', label: `generate-${i + 1}` }
  ))
)).filter(Boolean)

if (generated.length < 2) {
  throw new Error(`only ${generated.length} concept(s) generated successfully; need at least 2 to judge`)
}

// Anonymize: judges see label + content only, never which agent/index produced it
// beyond the label itself, and never a generation-order hint in the prompt text.
const labeled = generated.map((c, i) => ({ label: conceptLabels[i] || `Concept ${i + 1}`, ...c }))
const conceptBriefText = labeled
  .map(c => `### ${c.label}\nApproach: ${c.approach}\nSummary: ${c.summary}`)
  .join('\n\n')

// ---- phase 2: independent judges, blind to authorship ----
phase('Judge')

const judged = (await parallel(
  Array.from({ length: judgeCount }, (_, i) => () => agent(
    `You are an independent design judge. You do NOT know which agent or person wrote which concept -- ` +
    `judge only the content below. Score every concept against the datum "${datum.name}" ` +
    `(${datum.description}) on each criterion, on a -2..+2 scale (-2 = much worse than datum, ` +
    `0 = same as datum, +2 = much better than datum). Criteria: ${criteriaSummary}.\n\n` +
    `Original brief: ${brief}\n\n${conceptBriefText}\n\n` +
    `Return a score object per concept label, one entry per criterion. Be willing to disagree with ` +
    `what you'd guess other judges think -- independent judgement is the point.`,
    { schema: JUDGE_SCHEMA, phase: 'Judge', label: `judge-${i + 1}`, agentType: 'general-purpose' }
  ))
)).filter(Boolean)

if (judged.length < 1) {
  throw new Error('no judge returned a usable score -- cannot reconcile')
}

// ---- phase 3: reconcile (average judges, rank, sensitivity check) ----
phase('Reconcile')

function averageScores(label) {
  const out = {}
  for (const name of criteriaNames) {
    const vals = judged
      .map(j => j.scores && j.scores[label] && j.scores[label][name])
      .filter(v => typeof v === 'number')
    out[name] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
  }
  return out
}

const reconciledConcepts = labeled.map(c => ({
  name: `${c.label}: ${c.name}`,
  approach: c.approach,
  summary: c.summary,
  scores: averageScores(c.label),
}))

function normalizeWeights() {
  const total = criteria.reduce((a, c) => a + c.weight, 0)
  if (total <= 0) throw new Error('criteria weights must sum to a positive number')
  const w = {}
  for (const c of criteria) w[c.name] = c.weight / total
  return w
}

function weightedTotal(scores, weights) {
  let t = 0
  for (const name of criteriaNames) t += (weights[name] || 0) * (scores[name] || 0)
  return t
}

function rankConcepts(concepts, weights) {
  return concepts
    .map(c => ({ name: c.name, total: weightedTotal(c.scores, weights) }))
    .sort((a, b) => b.total - a.total)
}

function topNames(ranked, n) {
  return ranked.slice(0, n).map(r => r.name)
}

function perturb(weights, criterionName, factor) {
  const others = criteriaNames.filter(n => n !== criterionName)
  const out = { ...weights }
  const oldW = weights[criterionName]
  const newW = Math.max(0, oldW * factor)
  const delta = oldW - newW
  out[criterionName] = newW
  const othersTotal = others.reduce((a, n) => a + weights[n], 0)
  if (othersTotal > 0) {
    for (const n of others) out[n] = weights[n] + delta * (weights[n] / othersTotal)
  }
  return out
}

const baseWeights = normalizeWeights()
const baseRanked = rankConcepts(reconciledConcepts, baseWeights)
const baseTop = new Set(topNames(baseRanked, topN))

const flips = []
for (const c of criteria) {
  for (const [dir, factor] of [['+', 1.25], ['-', 0.75]]) {
    const pw = perturb(baseWeights, c.name, factor)
    const pr = rankConcepts(reconciledConcepts, pw)
    const pTop = new Set(topNames(pr, topN))
    const same = pTop.size === baseTop.size && [...pTop].every(n => baseTop.has(n))
    if (!same) {
      flips.push({ criterion: c.name, direction: dir, base_top: [...baseTop], perturbed_top: [...pTop] })
    }
  }
}

log(`Reconciled ${reconciledConcepts.length} concept(s) from ${judged.length} judge(s). ` +
  `Top-${topN}: ${topNames(baseRanked, topN).join(', ')}. Stable: ${flips.length === 0}.`)

// ---- phase 4: pairwise sanity check on the top 2 ----
phase('Pairwise compare')

let pairwiseTop2 = null
const top2Names = topNames(baseRanked, 2)
if (top2Names.length === 2) {
  const c1 = reconciledConcepts.find(c => c.name === top2Names[0])
  const c2 = reconciledConcepts.find(c => c.name === top2Names[1])
  const PAIRWISE_SCHEMA = {
    type: 'object',
    properties: {
      preferred: { type: 'string', enum: [top2Names[0], top2Names[1], 'too close to call'] },
      reasoning: { type: 'string' },
    },
    required: ['preferred', 'reasoning'],
  }
  pairwiseTop2 = await agent(
    `Compare these two top-ranked concepts head-to-head against the brief and criteria -- ignore ` +
    `their weighted-matrix scores, judge the actual substance.\n\nBrief: ${brief}\nCriteria: ${criteriaSummary}\n\n` +
    `### ${top2Names[0]}\n${c1 ? c1.approach : ''}\n${c1 ? c1.summary : ''}\n\n` +
    `### ${top2Names[1]}\n${c2 ? c2.approach : ''}\n${c2 ? c2.summary : ''}\n\n` +
    `State which you'd prefer, or "too close to call", and why in 2-3 sentences. This is input for a ` +
    `human decision, not a final answer.`,
    { schema: PAIRWISE_SCHEMA, phase: 'Pairwise compare', label: 'pairwise-top2' }
  )
}

return {
  schema: 'forge.pugh/1',
  generated_at: timestamp,
  minimum_concepts: conceptCount,
  top_n: topN,
  sensitivity_reviewed_by: '',
  criteria,
  concepts: [
    { name: datum.name, datum: true, scores: Object.fromEntries(criteriaNames.map(n => [n, 0])) },
    ...reconciledConcepts,
  ],
  ranking: baseRanked,
  sensitivity: { stable: flips.length === 0, flips, top_n: topN },
  pairwise_top2: pairwiseTop2,
  judge_count: judged.length,
  concept_count: reconciledConcepts.length,
}
