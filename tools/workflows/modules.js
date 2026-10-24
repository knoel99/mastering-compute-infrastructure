export const meta = {
  name: 'write-course-modules',
  description: 'Write course modules (page + verified labs) from data/curriculum.json, then technically review each one',
  phases: [{ title: 'Write', detail: 'one writer per module: labs run, gates pass' }, { title: 'Review', detail: 'one skeptical technical reviewer per module' }],
}

// args = { modules: ['module-id', ...] }. Each agent reads its own entry in data/curriculum.json.
const REPO = '/home/user/mastering-compute-infrastructure'
const SCR = '/tmp/claude-0/-home-user/d102e5e9-dd94-5c0c-abf5-595d43a437da/scratchpad'
const PY = `${SCR}/venv/bin/python`
const ids = args.modules

const ENTRY = (id) => `python3 -c "import json; print(json.dumps([m for m in json.load(open('${REPO}/data/curriculum.json'))['modules'] if m['id']=='${id}'][0], indent=1, ensure_ascii=False))"`

const SANDBOX = `SANDBOX FACTS (Linux 6.18 VM, 4 vCPU, 16 GB RAM, no GPU, root, outbound HTTPS through a proxy; measured, not assumed):
- Python venv with CPU PyTorch 2.14 (gloo works), numpy, scipy, pytest, pyyaml: run labs with  PYTHON=${PY}  (verify.sh must honour \${PYTHON:-python3}). pip install of other packages works (PyPI reachable). apt works (Ubuntu noble 24.04). GitHub release downloads are blocked (403); dl.k8s.io and raw.githubusercontent.com are reachable.
- Already installed: munge, Slurm 23.11, MariaDB, slurmdbd, promtool 2.45 (apt package prometheus), fio 3.36, numactl, sysstat, stress-ng, hwloc, ethtool, iperf3, shellcheck, yamllint, pandoc, node, pdftotext, strace, smartctl, ipmitool. A TESTED script brings up a real single-node Slurm with accounting: bash ${REPO}/labs/slurm/slurm-sandbox/setup.sh (idempotent, ~15 s) and teardown.sh (always run it when you finish). WITHOUT slurmdbd every job stays pending (InvalidAccount). NOT available: docker daemon, kind, GPUs, systemd as PID 1, perf, bpftrace.
- cgroups are v1 / hybrid here (cgroup2 only has hugetlb): a cgroup v2 lab cannot be verified; see ${REPO}/labs/linux-systems/cgroup-limits for a lab that detects v1/v2 and says which branch ran.
- IMPORTANT, shared machine: another writer may be running labs on the same 4 vCPUs at the same time. Never assert on wall-clock timing in verify.sh; assert on counters, ratios or structural properties with generous tolerances, and never saturate all CPUs for more than ~10 s. The page cache here is dropped periodically by the platform and the virtual disk is cached by the host: timing of cold vs warm reads is NOT reliable (see labs/linux-systems/pagecache for counter-based measurement).
- Pandoc build: python3 tools/build.py courses/<id> ; gates: python3 tools/check_gates.py courses/<id> ; airiness: python3 tools/check_airiness.py courses/<id>.
- Never leave daemons running when you finish (pkill -x what you started; never pkill -f). Put scratch files under ${SCR}/<module-id>/ , never in the repo.
- Already published and linkable: modules ../perf-models/index.html, ../slurm/index.html; projects ../../projects/resilient-trainer/index.html (checkpoint, supervisor, Young-Daly), ../../projects/scaling-study/index.html (alpha-beta, Karp-Flatt), ../../projects/gpu-observability/index.html (dcgm-exporter format, promtool unit tests with mutation testing, detectors). Other modules/projects are planned (links to them are allowed by the gate). The project labs under ${REPO}/labs/projects/*/reference/ contain tested code you may reuse by reference instead of rewriting.`

const WRITE = (id) => `You are writing ONE course module of the public French-language site "Mastering Compute Infrastructure" (repository ${REPO}). Audience: a senior AI/LLM engineer (strong Kubernetes, Prometheus/Grafana, Terraform, FinOps; no HPC schedulers, no InfiniBand/NCCL, no multi-node training operations) who wants to become a compute infrastructure engineer/lead for GPU training fleets.

YOUR MODULE: id "${id}". Read its entry first with:
${ENTRY(id)}
(fields: number, phase, hours, level, status, title, summary, prerequisites, outcomes, chapters, labs, facts, feeds).

STEP 0 — read, in this order (use sed -n ranges, do not dump whole files twice):
 1. ${REPO}/specs/module-contract.md and ${REPO}/AGENTS.md  (binding: YAML front matter, anchors, session plan summing to the entry's hours, >= 8 graded exercises each followed by ::: sol with >= 2 of each grade, >= 2 labs, 4500-18000 prose words, airiness rules A1-A3, French prose / English code, no invented numbers).
 2. EXEMPLARS: ${REPO}/courses/perf-models/index.md and ${REPO}/courses/slurm/index.md: read the front matter + intro, one chapter, the labs section, three exercises with solutions, the exit/refs/sources sections. Imitate voice, density, box usage (def/thm/ex/note/key/war/recap), worked examples with REAL computed or captured outputs, honest "Documenté / Recommandé / À vérifier / Hors périmètre". Read their lab folders ${REPO}/labs/perf-models/*/ and ${REPO}/labs/slurm/*/ as the model for labs.
 3. ${REPO}/data/resources/learning.json (verified references: prefer them for the references section; check the 'topics' field).
${SANDBOX}

STEP 1 — facts first. For every external factual claim you intend to make (versions, numbers, defaults, flags, paper results, prices, limits), read the primary source with  python3 ${REPO}/tools/fetch_text.py "URL" --grep 'regex'  (official docs, arXiv/paper text, vendor datasheets). If you cannot confirm it, drop it or present it as an order of magnitude and list it under "À vérifier". Never quote prices or contract terms as real unless a page you read states them with a date (prefer giving the METHOD and telling the reader to read the price page the same day). Record each source you really used for the references section (title, authors/provider, year, URL). Quote a source verbatim only if the string appears in the fetched text.

STEP 2 — labs. Create ${REPO}/labs/${id}/<lab-id>/ for every lab (README.md, code, verify.sh with set -euo pipefail, honouring \${PYTHON:-python3}). Labs of kind "sandbox" MUST run to completion here: execute verify.sh at least twice, read the output, fix until it passes reliably, and quote one real output line in the lab text. Make labs sandbox-runnable by simulation, fixtures or small CPU versions rather than downgrading them, but NEVER fake: a simulated workload or a hand-made fixture must be labelled as such in the README and in the page. If a lab cannot run here (needs GPUs, a real cluster, cloud accounts), its kind is "cluster" or "gpu": lint it (bash -n / shellcheck / python -m py_compile / yamllint / offline schema validation), say so plainly in the lab block, and use badge class "unverified" for the module (class "verified" only when ALL labs are sandbox labs whose verify.sh passed; a lab with a verified branch and an unverified branch must say which in its README and in the page). Prefer the project-style structure when a lab has a starter/reference: starter code + tests that fail on the starter and pass on the reference.

STEP 3 — the page. Write ${REPO}/courses/${id}/index.md in parts (cat > then cat >> with heredocs). Compute EVERY number used in examples and exercise solutions with a Python script first; paste only computed or captured values and label captured ones with the machine they came from. Exercises must vary: numeric calculation, reading a log/command output, failure diagnosis, design/sizing, trade-off with numbers. Solutions complete and correct (run commands/scripts that appear in solutions). Use display math $$..$$ for any formula longer than ~40 characters of TeX, keep paragraphs <= 100 words and <= 6 inline formulas per block (the gate enforces it). Follow the curriculum chapter list (you may refine titles; 5-10 chapters). Every chapter has at least one worked example (::: ex) and a ::: recap. Use ::: war boxes only for incidents/limits you verified with a link. Inline SVG diagrams (<figure class="fig"><svg ... currentColor/var(--accent) ...></svg><figcaption>) are welcome (max 4), never <img>. Session plan: durations 1.5-3.5 h each, levels non-decreasing, sum equals the entry's hours exactly.
Link to projects as ../../projects/<project-id>/index.html and to other modules as ../<module-id>/index.html. Do NOT mention employers, clients or a person's name.

STEP 4 — prove it. Run: python3 tools/check_gates.py courses/${id} (must say ok), python3 tools/build.py courses/${id}, PYTHON=${PY} bash labs/${id}/<lab>/verify.sh for each sandbox lab, python3 tools/check_links.py courses/${id} (links reported BROKEN with URLError may be blocked by the sandbox proxy: confirm with curl before changing them). Fix everything. Do not touch files of other modules, data/curriculum.json, assets/ or tools/ (report needed changes instead).

Budget: aim at about 100-140 tool calls; keep command output short (head/tail/grep). Do not git commit. When finished, return the JSON summary of the schema (honest: list anything unverified in open_issues).`

const REVIEW = (id, w) => `You are a skeptical technical reviewer of the course module "${id}" (page ${REPO}/courses/${id}/index.md, labs in ${REPO}/labs/${id}/). The writer reported: ${JSON.stringify(w)}. Your job is to find what is WRONG, not to praise. Default to "unsupported" when you cannot confirm.

Read ${REPO}/specs/module-contract.md first, then the page. Then:
1. Recompute at least 10 numbers from worked examples and exercise solutions with Python; fix any error in the page (edit in place with minimal diffs).
2. Re-check at least 12 external factual claims against the primary source with python3 ${REPO}/tools/fetch_text.py URL --grep 'regex' (versions, defaults, flags, paper numbers, limits). Correct, soften to "ordre de grandeur", or move to "À vérifier" what you cannot confirm. Check every ::: war box has a real source and that every verbatim quote appears in the fetched text.
3. Run every sandbox lab (PYTHON=${PY} bash labs/${id}/<lab>/verify.sh) TWICE to catch flakiness; also read the lab code for bugs, secrets, and false claims in README. Lint non-sandbox labs. Make sure no assertion depends on wall-clock timing.
4. Pedagogy: could the reference reader (see contract) follow the module? Are prerequisites respected, jargon defined at first use, exercises solvable with the chapter content, difficulty grades fair? Fix small things; list big ones.
5. Rules: French prose + English code; no employer/client/person names; no invented statistics; badges honest (verified only if ALL labs are sandbox and passed; hand-made fixtures labelled).
6. Finally run python3 tools/check_gates.py courses/${id} and python3 tools/build.py courses/${id}; both must pass.
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
  (id) => agent(WRITE(id), { label: `write:${id}`, phase: 'Write', schema: W_SCHEMA }),
  (w, id) => w ? agent(REVIEW(id, w), { label: `review:${id}`, phase: 'Review', schema: R_SCHEMA }).then((r) => ({ id, writer: w, review: r })) : null,
)
const ok = out.filter(Boolean)
const failed = ids.filter((i) => !ok.find((o) => o.id === i))
if (failed.length) log(`modules without result: ${failed.join(', ')}`)
return { ok, failed }
