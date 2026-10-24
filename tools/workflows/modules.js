export const meta = {
  name: 'write-course-modules',
  description: 'Write course modules (page + verified labs) from data/curriculum.json, then technically review each one',
  phases: [{ title: 'Write', detail: 'one writer per module: labs run, gates pass' }, { title: 'Review', detail: 'one skeptical technical reviewer per module' }],
}

const REPO = '/home/user/mastering-compute-infrastructure'
const PY = '/tmp/claude-0/-home-user/d102e5e9-dd94-5c0c-abf5-595d43a437da/scratchpad/venv/bin/python'
const ids = args.modules
const curr = args.curriculum   // {modules: [...]} subset passed by the caller

const SANDBOX = `SANDBOX FACTS (Linux, 4 vCPU, 15 GB RAM, no GPU, root, outbound HTTPS through a proxy):
- Python venv with CPU PyTorch 2.14 (gloo works), numpy, pytest, pyyaml, prometheus_client, scipy: run labs with  PYTHON=${PY}  (verify.sh honours $PYTHON). pip install of other packages works (PyPI reachable); GitHub release downloads are blocked (403) but apt works (Ubuntu noble), dl.k8s.io is reachable (kubectl binary), raw.githubusercontent.com is reachable.
- Installed: munge, Slurm 23.11, MariaDB, slurmdbd, shellcheck, yamllint, pandoc, node, pdftotext. A TESTED script brings up a real single-node Slurm with accounting: bash ${REPO}/labs/slurm/slurm-sandbox/setup.sh (idempotent, ~15 s) and bash ${REPO}/labs/slurm/slurm-sandbox/teardown.sh (always run it when you finish; it stops every daemon). WITHOUT slurmdbd every job stays pending with reason InvalidAccount (found by testing), so reuse that script for any Slurm lab. NOT available: docker daemon, kind, GPUs, systemd as PID 1. cgroup v2 write access is probably limited: test before promising a cgroup lab.
- Pandoc build: python3 tools/build.py courses/<id> ; gates: python3 tools/check_gates.py courses/<id> ; airiness: python3 tools/check_airiness.py courses/<id>.
- Never leave daemons running when you finish (pkill what you started). Put scratch files under /tmp/claude-0/-home-user/d102e5e9-dd94-5c0c-abf5-595d43a437da/scratchpad/<module-id>/ , never in the repo.`

const WRITE = (m) => `You are writing ONE course module of the public French-language site "Mastering Compute Infrastructure" (repository ${REPO}). Audience: a senior AI/LLM engineer (strong Kubernetes, Prometheus/Grafana, Terraform, FinOps; no HPC schedulers, no InfiniBand/NCCL, no multi-node training operations) who wants to become a compute infrastructure engineer/lead for GPU training fleets.

YOUR MODULE (from data/curriculum.json):
${JSON.stringify(m, null, 1)}

STEP 0 — read, in this order (use sed -n ranges, do not dump whole files twice):
 1. ${REPO}/specs/module-contract.md and ${REPO}/AGENTS.md  (binding: YAML front matter, anchors, session plan summing to ${m.hours} h, >= 8 graded exercises each followed by ::: sol, >= 2 labs, airiness rules A1-A3, French prose / English code, no invented numbers).
 2. The EXEMPLAR module ${REPO}/courses/perf-models/index.md: read the front matter + intro (first ~110 lines), one chapter, the labs section, three exercises with their solutions, the exit/refs/sources sections. Imitate its voice, density, box usage (def/thm/ex/note/key/war/recap), worked examples with real computed numbers, honest "Documenté / Recommandé / À vérifier / Hors périmètre" section. Also read its lab folders ${REPO}/labs/perf-models/*/ (code + verify.sh + README.md) as the model for labs.
 3. ${REPO}/data/resources/learning.json if it exists (verified references: prefer them for the references section; check the 'topics' field).
${SANDBOX}

STEP 1 — facts first. For every external factual claim you intend to make (versions, numbers, defaults, flags, paper results, prices, limits), read the primary source with  python3 ${REPO}/tools/fetch_text.py "URL" --grep 'regex'  (official docs, arXiv/paper text, vendor datasheets). If you cannot confirm it, either drop it or present it as an order of magnitude and list it under "À vérifier". Never quote prices or contract terms as real unless a page you read states them with a date. Record each source you really used for the references section (title, authors/provider, year, URL).

STEP 2 — labs. Create ${REPO}/labs/${m.id}/<lab-id>/ for every lab (README.md, code, verify.sh with set -euo pipefail, honouring \${PYTHON:-python3}). Labs of kind "sandbox" MUST run to completion here: execute verify.sh, read its output, fix until it passes, and quote one real output line in the lab text. If a lab cannot run here (needs GPUs, a real cluster, cloud accounts), its kind is "cluster" or "gpu": lint it (bash -n / shellcheck / python -m py_compile / yamllint / schema validation where possible), say so plainly in the lab block and keep the badge "unverified" if ANY lab is non-sandbox... (class "verified" only when ALL labs of the module are sandbox labs whose verify.sh passed). Prefer making labs sandbox-runnable by simulation or small CPU versions rather than downgrading them; but never fake: a simulated workload must be labelled as simulated.

STEP 3 — the page. Write ${REPO}/courses/${m.id}/index.md in parts (e.g. cat > then cat >> with heredocs). Compute EVERY number used in examples and exercise solutions with a Python script first; paste only computed values. Exercises must vary: numeric calculation, reading a log/command output, failure diagnosis, design/sizing, trade-off with numbers. Solutions complete and correct. Use display math $$..$$ for any formula longer than ~40 characters of TeX, keep paragraphs <= 100 words and <= 6 inline formulas per block (the gate enforces it). Chapters ${m.chapters.length}: follow the curriculum chapter list but you may refine titles. Every chapter has at least one worked example (::: ex) and a ::: recap. Include 1-3 ::: war boxes only for incidents/limits you verified with a link. Inline SVG diagrams (<figure class="fig"><svg ... currentColor/var(--accent) ...></svg><figcaption>) are welcome (max 4), never <img> (dark mode).
Link to the projects as ../../projects/<project-id>/index.html (they will exist later) and to other modules as ../<module-id>/index.html.

STEP 4 — prove it. Run: python3 tools/check_gates.py courses/${m.id} (must say ok), python3 tools/build.py courses/${m.id}, PYTHON=${PY} bash labs/${m.id}/<lab>/verify.sh for each sandbox lab, python3 tools/check_links.py courses/${m.id} (no BROKEN). Fix everything. Do not touch files of other modules, data/curriculum.json, assets/, tools/ (report needed changes instead).

Budget: aim at about 90-130 tool calls; keep command output short (head/tail/grep). Do not git commit. When finished, return the JSON summary of the schema (honest: list anything unverified in open_issues).`

const REVIEW = (m, w) => `You are a skeptical technical reviewer of the course module "${m.id}" (page ${REPO}/courses/${m.id}/index.md, labs in ${REPO}/labs/${m.id}/). The writer reported: ${JSON.stringify(w)}. Your job is to find what is WRONG, not to praise. Default to "unsupported" when you cannot confirm.

Read ${REPO}/specs/module-contract.md first, then the page. Then:
1. Recompute at least 10 numbers from worked examples and exercise solutions with Python; fix any error in the page (edit in place with minimal diffs).
2. Re-check at least 12 external factual claims against the primary source with python3 ${REPO}/tools/fetch_text.py URL --grep 'regex' (versions, defaults, flags, paper numbers, limits). Correct, soften to "ordre de grandeur", or move to "À vérifier" what you cannot confirm. Check every ::: war box has a real source.
3. Run every sandbox lab (PYTHON=${PY} bash labs/${m.id}/<lab>/verify.sh); also read the lab code for bugs, secrets, wrong claims in README. Lint non-sandbox labs.
4. Pedagogy: could the reference reader (see contract) follow the module? Are prerequisites respected, jargon defined at first use, exercises solvable with the chapter content, difficulty grades fair? Fix small things; list big ones.
5. Rules: French prose + English code; no employer/client names; no invented statistics; badges honest.
6. Finally run python3 tools/check_gates.py courses/${m.id} and python3 tools/build.py courses/${m.id}; both must pass.
Budget: about 60-90 tool calls. Do not touch other modules or tools/. Return the schema.
${SANDBOX}`

const W_SCHEMA = { type: 'object', properties: {
  module: { type: 'string' }, prose_words: { type: 'number' }, exercises: { type: 'number' }, labs: { type: 'number' },
  labs_verified: { type: 'array', items: { type: 'string' } }, labs_not_executed: { type: 'array', items: { type: 'string' } },
  gate_ok: { type: 'boolean' }, sources_read: { type: 'number' }, open_issues: { type: 'array', items: { type: 'string' } } },
  required: ['module', 'gate_ok', 'labs_verified', 'open_issues'] }
const R_SCHEMA = { type: 'object', properties: {
  module: { type: 'string' }, numbers_rechecked: { type: 'number' }, claims_rechecked: { type: 'number' },
  corrections: { type: 'array', items: { type: 'string' } }, removed_or_softened: { type: 'array', items: { type: 'string' } },
  labs_rerun: { type: 'array', items: { type: 'string' } }, gate_ok: { type: 'boolean' }, remaining_concerns: { type: 'array', items: { type: 'string' } } },
  required: ['module', 'corrections', 'gate_ok', 'remaining_concerns'] }

phase('Write')
const out = await pipeline(
  ids,
  (id) => agent(WRITE(curr.modules.find((x) => x.id === id)), { label: `write:${id}`, phase: 'Write', schema: W_SCHEMA }),
  (w, id) => w ? agent(REVIEW(curr.modules.find((x) => x.id === id), w), { label: `review:${id}`, phase: 'Review', schema: R_SCHEMA }).then((r) => ({ id, writer: w, review: r })) : null,
)
const ok = out.filter(Boolean)
const failed = ids.filter((i) => !ok.find((o) => o.id === i))
if (failed.length) log(`modules without result: ${failed.join(', ')}`)
return { ok, failed }
