export const meta = {
  name: 'regression-sweep',
  description: 'Rebuild and re-verify every domain in a Forge product repo (forge verify --all), then diff the results against the last green run and flag any domain that changed with no fresh evidence -- the diff itself is a deterministic script (workflows/scripts/regression_diff.py), not an LLM judgement call.',
  whenToUse: 'The weekly routine, or before a gate review / release, to catch silent regressions across mech/elec/fw/sys/sim that a narrow --changed run would miss.',
  phases: [
    { title: 'Snapshot', detail: 'preserve the previous out/verify/ results for comparison, if any' },
    { title: 'Verify', detail: 'run forge verify --all for every domain in forge.toml' },
    { title: 'Diff', detail: 'run regression_diff.py: check_id status diff + last_green-state staleness, both exact/mechanical' },
  ],
}

// ---- inputs -----------------------------------------------------------
// args: { project: string, keepHistory?: boolean }  // keepHistory: don't overwrite an
// existing out/verify.previous/ from an earlier sweep run today (default: true)

const project = args && args.project
const keepHistory = !(args && args.keepHistory === false)

if (!project) {
  throw new Error('regression-sweep requires args: { project: "<path>" }')
}

// ---- phase 1: snapshot the previous run --------------------------------
phase('Snapshot')

const snapshot = await agent(
  `In the project at "${project}": if out/verify/ exists and has any *.json files, and ` +
  (keepHistory
    ? `out/verify.previous/ does NOT already exist (an earlier sweep today already preserved a baseline -- ` +
      `leave it alone in that case), `
    : ``) +
  `copy out/verify/ to out/verify.previous/ (recursively, overwriting out/verify.previous/ if ` +
  `${keepHistory ? 'it does not yet exist' : 'allowed to'}). ` +
  `Report: whether out/verify/ existed, how many *.json files it had, and whether out/verify.previous/ was ` +
  `written, left alone, or there was nothing to snapshot.`,
  { phase: 'Snapshot', label: 'snapshot' }
)

// ---- phase 2: rebuild and re-verify every domain -----------------------
phase('Verify')

const verifyRun = await agent(
  `In the project at "${project}": run \`plugins/forge/bin/forge verify --all --project ${project}\` ` +
  `(the Forge repo root is wherever plugins/forge/bin/forge is found relative to or above "${project}"; if ` +
  `"${project}" IS inside the Forge repo's plugins/forge/tests fixtures, use that same repo's forge binary). ` +
  `Capture the full stdout and the process exit code. Then list every out/verify/*.json file this run wrote, ` +
  `with its check_id, status (pass/fail/error) and target. If forge.toml is missing or has no [[verify]] ` +
  `blocks, say so plainly instead of guessing at what "every domain" means.`,
  { phase: 'Verify', label: 'verify-all' }
)

// ---- phase 3: diff against the last-green state -- a deterministic script,
// never an LLM's judgement call (M9, review #1: "that diff is done by an
// LLM with no schema"). The agent here is a pure executor: it runs exactly
// one command and returns its stdout verbatim. Every classification
// (NEW/REMOVED/UNCHANGED/REGRESSED/FIXED, and which domains are stale
// against their recorded last_green state) is decided by
// workflows/scripts/regression_diff.py, not by the agent reading files and
// reasoning about them.
phase('Diff')

const diffRunRaw = await agent(
  `Locate the Forge repo root: the directory at or above "${project}" that contains ` +
  `plugins/forge/bin/forge (same resolution rule as the Verify phase). Then run exactly:\n\n` +
  `    <forge-python-if-it-exists-else-python3> <forge-repo-root>/plugins/forge/workflows/scripts/regression_diff.py --project "${project}"\n\n` +
  `(\`forge-python\` is ~/.forge/bin/forge-python if that file exists, else use \`python3\` -- this script is ` +
  `standard-library only, so either interpreter works.) Your entire final message must be that command's raw ` +
  `stdout, character for character -- no markdown code fence, no summary, no commentary before or after it, ` +
  `and no reformatting of the JSON. If the command exits non-zero, your final message must instead be exactly ` +
  `"REGRESSION_DIFF_ERROR: " followed by its stderr.`,
  { phase: 'Diff', label: 'diff' }
)

let diff
if (typeof diffRunRaw === 'string' && diffRunRaw.trim().startsWith('REGRESSION_DIFF_ERROR:')) {
  diff = { schema: 'forge.regression_diff/1', error: diffRunRaw.trim() }
} else {
  // Strip an accidental markdown fence, if the agent added one despite the
  // instruction not to -- parsing itself is still plain JSON.parse, not an
  // LLM interpreting the content.
  const text = (typeof diffRunRaw === 'string' ? diffRunRaw : '').trim()
    .replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '')
  try {
    diff = JSON.parse(text)
  } catch (e) {
    diff = { schema: 'forge.regression_diff/1', error: `could not parse regression_diff.py output as JSON: ${e.message}`, raw: text }
  }
}

log(diff.summary ? `Diff: ${diff.summary}` : `Diff: ${diff.error || 'no summary available'}`)
log('Regression sweep complete: rebuilt, re-verified and diffed against the last preserved run.')

return {
  schema: 'forge.regression_sweep/1',
  project,
  snapshot,
  verify_run: verifyRun,
  diff,
}
