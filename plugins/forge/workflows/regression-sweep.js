export const meta = {
  name: 'regression-sweep',
  description: 'Rebuild and re-verify every domain in a Forge product repo (forge verify --all), then diff the results against the last green run and flag any domain that changed with no fresh evidence.',
  whenToUse: 'The weekly routine, or before a gate review / release, to catch silent regressions across mech/elec/fw/sys/sim that a narrow --changed run would miss.',
  phases: [
    { title: 'Snapshot', detail: 'preserve the previous out/verify/ results for comparison, if any' },
    { title: 'Verify', detail: 'run forge verify --all for every domain in forge.toml' },
    { title: 'Diff', detail: 'compare against the preserved previous run and the evidence manifest' },
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

// ---- phase 3: diff against the previous run and the evidence manifest --
phase('Diff')

const diffRun = await agent(
  `In the project at "${project}": compare out/verify/ (the run that just finished) against ` +
  `out/verify.previous/ (from before this sweep), if out/verify.previous/ exists -- if it doesn't, say this is ` +
  `the first recorded run and skip the diff, but still do the evidence check below.\n\n` +
  `For every check_id present in either directory, classify it as one of: NEW (no previous result), ` +
  `REMOVED (had a previous result, none now), UNCHANGED (same status both times), REGRESSED (previously ` +
  `pass, now fail or error), FIXED (previously fail or error, now pass). ` +
  `List every REGRESSED check_id with its remediation string(s) from the check-result JSON's measurements. ` +
  `\n\nSeparately: read evidence/manifest.json and \`git status\` in "${project}". For each domain (mech, ` +
  `elec, fw, sw, sys, sim, mfg, compliance) that has files changed per git status, confirm there is an ` +
  `evidence/manifest.json entry for that domain at or after those changes; flag any changed domain with no ` +
  `fresh evidence entry as an UNVERIFIED risk (CONTRACTS.md §4-5).` +
  `\n\nEnd with one summary line: "X regressed, Y fixed, Z unchanged, W new, V unverified-domain risk(s)".`,
  { phase: 'Diff', label: 'diff' }
)

log('Regression sweep complete: rebuilt, re-verified and diffed against the last preserved run.')

return {
  schema: 'forge.regression_sweep/1',
  project,
  snapshot,
  verify_run: verifyRun,
  diff: diffRun,
}
