export const meta = {
  name: 'review-pages',
  description: 'Independent skeptical review of finished course modules and projects (numbers recomputed, labs rerun, claims re-sourced)',
  phases: [{ title: 'Review', detail: 'one skeptical reviewer per course or project' }],
}

// args = { targets: [{kind: 'course'|'project', id: '...'}, ...] }
const REPO = '/home/user/mastering-compute-infrastructure'
const SCR = '/tmp/claude-0/-home-user/d102e5e9-dd94-5c0c-abf5-595d43a437da/scratchpad'
const PY = `${SCR}/venv/bin/python`
const targets = args.targets

const FACTS = `SANDBOX FACTS (Linux 6.18 VM, 4 vCPU, 16 GB RAM, no GPU, root; measured, not assumed):
- Python venv with CPU PyTorch 2.14, numpy, scipy, pytest, pyyaml, yamllint: run labs with PYTHON=${PY}. apt works (promtool, fio, stress-ng, shellcheck, numactl installed). GitHub release downloads and gnu.org are blocked by the proxy; many docs sites are reachable through python3 ${REPO}/tools/fetch_text.py URL --grep REGEX.
- cgroups are v1/hybrid here; PSI exists; page cache is dropped periodically by the platform; the Slurm sandbox (labs/slurm/slurm-sandbox/setup.sh, teardown.sh) may be in use by another agent: do NOT start or stop it unless your target needs it, and never use pkill -f.
- Shared machine: other agents may use the CPUs. A flaky verify.sh is a finding: report which assertion is timing-dependent.
- Gates: python3 tools/check_gates.py <courses/ID or projects/ID> ; python3 tools/build.py <path> ; python3 tools/check_airiness.py <path>.`

const REVIEW = (t) => {
  const page = t.kind === 'course' ? `${REPO}/courses/${t.id}/index.md` : `${REPO}/projects/${t.id}/index.md`
  const labs = t.kind === 'course' ? `${REPO}/labs/${t.id}/` : `${REPO}/labs/projects/${t.id}/`
  const contract = t.kind === 'course' ? 'module-contract.md' : 'project-contract.md'
  return `You are an independent, skeptical technical reviewer of the ${t.kind} "${t.id}" of the public French-language site "Mastering Compute Infrastructure". The author wrote it in one pass and nobody else has checked it. Your job is to find what is WRONG, not to praise. Default to "unsupported" when you cannot confirm. Page: ${page}. Labs/code: ${labs}.

Read ${REPO}/specs/${contract} and ${REPO}/AGENTS.md first, then the page, then the code and tests.
${FACTS}

Do ALL of the following and fix what you find in place with minimal diffs (never rewrite large parts):
1. NUMBERS. Recompute at least 12 numbers from worked examples, exercise solutions, tables and result tables with Python (or by re-running the reference code). Every discrepancy is a finding; fix the page.
2. FACTS. Re-check at least 12 external factual claims and every verbatim quote against the primary source: python3 ${REPO}/tools/fetch_text.py URL --grep 'regex' (the cached text is what counts; quotes must appear in it after whitespace normalisation). Correct, soften to an order of magnitude, or move to an 'À vérifier' part what you cannot confirm. Check that every ::: war box has a real source and that no price, vendor claim or statistic is invented.
3. RUN IT. Run every verify.sh (or the project verify.sh) TWICE with PYTHON=${PY}. For projects, also run the starter against the tests and read the failures: each failing test must fail for the INTENDED reason (a missing feature), not because of an accidental error such as a wrong fixture; and the tests must be discriminating (try at least three small mutations of the reference code and confirm a test fails for each; report any mutation that survives). Any assertion that depends on wall-clock timing or machine load is a finding.
4. CODE. Read the lab/reference code for bugs, race conditions, unsafe shell, secrets, misleading comments, off-by-one errors, and claims in READMEs that the code does not support.
5. HONESTY. Badges must be true (verified only if the scripts passed here; hand-made fixtures, invented data and unrun branches must be labelled as such in the page AND the README). No employer, client or person names. No invented statistics.
6. PEDAGOGY. Can the reference reader (senior AI/LLM engineer, strong Kubernetes/Prometheus/Terraform, no HPC schedulers) follow it? Are prerequisites respected, terms defined at first use, exercises solvable from the text, difficulty grades fair, milestones' durations plausible? Fix small things; list big ones.
7. Finally run python3 tools/check_gates.py ${t.kind === 'course' ? 'courses' : 'projects'}/${t.id} and python3 tools/build.py ${t.kind === 'course' ? 'courses' : 'projects'}/${t.id}; both must pass. If you changed any number or claim in the page, make sure the same change is made everywhere it appears (page, README of the lab, code comments, tests).
Do not touch other pages, data/curriculum.json, assets/ or tools/ (report needed changes). Do not git commit. Budget: about 80-110 tool calls; keep outputs short. Return the schema, honestly, with target set to exactly "${t.kind}:${t.id}".`
}

const SCHEMA = { type: 'object', properties: {
  target: { type: 'string' }, numbers_rechecked: { type: 'number' }, claims_rechecked: { type: 'number' },
  errors_found_and_fixed: { type: 'array', items: { type: 'string' } },
  unconfirmed_removed_or_softened: { type: 'array', items: { type: 'string' } },
  mutations_tried: { type: 'number' }, mutations_surviving: { type: 'array', items: { type: 'string' } },
  flaky_or_timing_dependent: { type: 'array', items: { type: 'string' } },
  verify_runs_passed: { type: 'number' }, gate_ok: { type: 'boolean' },
  remaining_concerns: { type: 'array', items: { type: 'string' } } },
  required: ['target', 'errors_found_and_fixed', 'gate_ok', 'remaining_concerns'] }

phase('Review')
const out = await pipeline(
  targets,
  (t) => agent(REVIEW(t), { label: `review:${t.kind}:${t.id}`, phase: 'Review', schema: SCHEMA }),
)
const ok = out.filter(Boolean)
const failed = targets.filter((t) => !ok.find((o) => o.target && o.target.includes(t.id)))
if (failed.length) log(`no result for: ${failed.map((t) => t.id).join(', ')}`)
return { reviews: ok, no_result: failed }
