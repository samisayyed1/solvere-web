export const meta = {
  name: 'standards-research',
  description: 'Multi-source research over a question, with independent cross-checking agents, returning a cited report where every claim is tagged verified (V, confirmed on the issuing source), reported (R, secondary source only) or unverified (U).',
  whenToUse: 'Use for standards/compliance/toolchain research that needs V/R/U-tagged, cited claims -- e.g. "what is the current edition of standard X", "does regulation Y apply to Z", "what changed in this tool\'s latest release". Mirrors the tagging convention already used in docs/research/R1-R6. Needs the WebSearch/WebFetch tools to be useful; without them every claim will land as U.',
  phases: [
    { title: 'Research', detail: 'independent agents each research the question from a different angle or source type' },
    { title: 'Cross-check', detail: 'independent agents try to verify each distinct claim against its primary source, blind to each other' },
    { title: 'Synthesize', detail: 'merge into one cited report and flag any claim where cross-checkers disagreed' },
  ],
}

// ---- inputs -----------------------------------------------------------
// args: {
//   question: string,
//   angles?: string[],          // hints for what each researcher should look at
//   researcherCount?: number,   // default max(3, angles.length)
//   crossCheckerCount?: number, // default 2, independent cross-checkers per claim
//   timestamp?: string,         // caller-supplied; the script never calls a clock
// }

const question = args && args.question
const angleHints = (args && args.angles) || [
  "the issuing body's own page (standard, regulator, vendor)",
  'a secondary/reporting source (trade press, vendor blog, consultancy note)',
  'an adjacent or comparison source (a related standard, a prior edition, a competing product)',
]
const researcherCount = (args && args.researcherCount) || Math.max(3, angleHints.length)
const crossCheckerCount = (args && args.crossCheckerCount) || 2
const timestamp = (args && args.timestamp) || 'unspecified'

if (!question) {
  throw new Error('standards-research needs args.question')
}

// ---- phase 1: research from independent angles ----
phase('Research')

const CLAIM_SCHEMA = {
  type: 'object',
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          source_url: { type: 'string' },
          source_name: { type: 'string' },
          self_tag: { type: 'string', enum: ['V', 'R', 'U'] },
        },
        required: ['text', 'source_url', 'self_tag'],
      },
    },
  },
  required: ['claims'],
}

const researched = (await parallel(
  Array.from({ length: researcherCount }, (_, i) => () => agent(
    `Research this question using web search/fetch tools: ${question}\n\n` +
    `Angle for this pass: ${angleHints[i % angleHints.length]}.\n\n` +
    `Return a list of distinct, checkable factual claims (edition numbers, dates, thresholds, status), ` +
    `each with the exact source URL you found it at, a short source name, and your OWN tag: ` +
    `'V' only if you fetched it directly from the issuing body's own page, 'R' if only a secondary ` +
    `source confirmed it, 'U' if you could not confirm it at all (say what you tried in the text). ` +
    `Never invent a claim you didn't actually find.`,
    { schema: CLAIM_SCHEMA, phase: 'Research', label: `researcher-${i + 1}` }
  ))
)).filter(Boolean)

const allClaims = researched.flatMap(r => r.claims || [])
if (!allClaims.length) {
  throw new Error('no claims returned by any researcher -- check that WebSearch/WebFetch are available')
}

log(`${researched.length} researcher(s) returned ${allClaims.length} claim(s) total; cross-checking each.`)

// ---- phase 2: independent cross-check per claim, blind to each other ----
phase('Cross-check')

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    tag: { type: 'string', enum: ['V', 'R', 'U'] },
    reasoning: { type: 'string' },
    corrected_text: { type: 'string' },
  },
  required: ['tag', 'reasoning'],
}

const crossChecked = await pipeline(
  allClaims,
  async (claim) => {
    const votes = (await parallel(
      Array.from({ length: crossCheckerCount }, () => () => agent(
        `Independently cross-check this claim -- try to fetch the ORIGINAL/primary source yourself, ` +
        `don't just trust the URL you're given:\n\n` +
        `Claim: "${claim.text}"\nGiven source: ${claim.source_url} (${claim.source_name || 'unnamed'})\n` +
        `Original researcher's self-tag: ${claim.self_tag}.\n\n` +
        `Tag it 'V' only if YOU independently confirmed it on the issuing body's own page, 'R' if only a ` +
        `secondary source confirms it, or 'U' if you cannot confirm it. If the claim looks wrong or stale, ` +
        `say so and give the correction in 'corrected_text'. Do not simply defer to the original tag.`,
        { schema: VERDICT_SCHEMA, phase: 'Cross-check', label: `crosscheck-${claim.text.slice(0, 32)}` }
      ))
    )).filter(Boolean)
    return { claim, votes }
  },
)

// ---- phase 3: synthesize into one cited, tagged report ----
phase('Synthesize')

function finalTag(votes) {
  if (votes.some(v => v.tag === 'V')) return 'V'
  if (votes.some(v => v.tag === 'R')) return 'R'
  return 'U'
}

const report = crossChecked.filter(Boolean).map(({ claim, votes }) => {
  const tags = votes.map(v => v.tag)
  const tag = votes.length ? finalTag(votes) : 'U'
  const conflicting = new Set(tags).size > 1
  const corrections = votes.map(v => v.corrected_text).filter(Boolean)
  return {
    text: claim.text,
    source_url: claim.source_url,
    source_name: claim.source_name || null,
    tag,
    researcher_self_tag: claim.self_tag,
    cross_checker_votes: tags,
    conflicting_votes: conflicting,
    corrections,
  }
})

const counts = { V: 0, R: 0, U: 0 }
for (const c of report) counts[c.tag] = (counts[c.tag] || 0) + 1
log(`${report.length} claim(s) synthesized: V=${counts.V} R=${counts.R} U=${counts.U}. ` +
  `${report.filter(c => c.conflicting_votes).length} claim(s) had disagreeing cross-checkers.`)

return {
  schema: 'forge.standards_research/1',
  question,
  generated_at: timestamp,
  claims: report,
  researcher_count: researched.length,
  cross_checker_count: crossCheckerCount,
  summary_counts: counts,
}
