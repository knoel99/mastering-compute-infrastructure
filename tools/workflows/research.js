export const meta = {
  name: 'hpc-masters-research-lean',
  description: 'Lean, incremental research of HPC master programmes (FR/US/CN/world), compute-infra job postings and learning resources; verbatim quotes only',
  phases: [{ title: 'Research', detail: 'one agent per unit, files written after every item' }],
}

const TODAY = '2026-10-22'
const REPO = '/home/user/mastering-compute-infrastructure'

const COMMON = `You work for a learner (senior AI/LLM engineer: Kubernetes, Prometheus/Grafana, Terraform, FinOps, on-prem GPU inference) who wants to become a *compute infrastructure engineer* (GPU clusters, Slurm, distributed-training platforms, multi-provider capacity). We are building a public course site and need a SOURCED survey. The data you write will be checked mechanically: every web quote must appear VERBATIM in the cached text of the cited page.

Today is ${TODAY}. Repository: ${REPO}.

STEP 0 (once): read ${REPO}/specs/research-contract.md fully (taxonomy of 26 topics, JSON formats, honesty rules).

HOW TO READ PAGES (mandatory): do NOT rely on WebFetch summaries for evidence (they paraphrase). Use the shared fetcher via Bash:
  cd ${REPO} && python3 tools/fetch_text.py "URL" --grep 'regex' --context 2      # filtered lines, cheap
  python3 tools/fetch_text.py "URL" --max 6000 [--offset N]                        # raw text window
  python3 tools/fetch_text.py "URL" --links                                        # navigate a site
It prints the exact text that the verifier will later search. Copy quotes (<= 25 words) character for character from that output. WebSearch is allowed to discover URLs (it is a US index; queries about foreign institutions and in other languages work). If a page is unreachable or JS-only, say so in blocked_sources and move on: never invent.

WORKING RULES (cost matters, the account has a usage limit):
- Budget: STRICT, about 40-50 tool calls in total (the account has a weekly usage limit that was already hit once). Prefer --grep over dumping pages. Do not re-read what you already read.
- WRITE INCREMENTALLY: create the output JSON file early (valid skeleton from the contract) and update it after EVERY programme/posting/resource using a small Python snippet (load, append, json.dump(..., ensure_ascii=False, indent=1)). A crash must never lose finished work.
- After each update run: python3 ${REPO}/tools/validate_research.py <file>  and fix errors.
- Accuracy over coverage: 3-5 programmes with real syllabi beat 10 shallow ones. Unknown topic coverage is null, not 0. Memory-based facts: source "memory", confidence "low".
- Finish by running: python3 ${REPO}/tools/verify_quotes.py <file> (dry run) and fix or drop evidence it reports as not verbatim (re-copy from fetch_text output). Then return the summary requested by the schema.`

const MASTERS = (u) => `${COMMON}

UNIT "${u.id}" — ${u.label}. Output: ${REPO}/data/masters/${u.id}.json with "region": "${u.region}". Format: "data/masters/<unit>.json" of the contract.

CANDIDATES (rough prior knowledge, may be wrong; verify, drop what does not exist or is not HPC-relevant, add notable ones you stumble upon; target ${u.n} programmes with curriculum evidence):
${u.seed}

Per programme: official programme page + curriculum/course catalogue; fill every contract field (duration, credits in original unit, entry requirements, core_courses/electives with topics, topic_coverage for ALL 26 topics, machines_access only if a page says so, >= 4 evidence entries: duration/credits, 2-3 course titles, machine access or industry link). Also 1-3 "ecosystem" items (centres, training schools, competitions, certificates) when relevant to this unit.`

const JOBS = (u) => `${COMMON}

UNIT "${u.id}" — job-market analysis. Output: ${REPO}/data/jobs/${u.id}.json ("data/jobs/<unit>.json" format).
Collect ${u.n} REAL, CURRENT postings (live around ${TODAY}) for roles like Compute Infrastructure Engineer/Lead, GPU Cluster Engineer, ML/AI Infrastructure Engineer, HPC Systems Engineer, Training Platform Engineer, Research Infrastructure/Capacity. Favour TRAINING / large GPU fleets over inference-only. Mix company types and seniority.
Where: ${u.seed}
Per posting: read the posting text with fetch_text.py (public page or ATS JSON endpoint; both print text), extract skills with the fixed taxonomy (required vs bonus) each with a verbatim quote from that printed text; 3-6 responsibilities in your own words; years_required if stated; seniority; location.
${u.extra || ''}`

const RES = `${COMMON}

UNIT "res" — learning resources. Output: ${REPO}/data/resources/learning.json ("data/resources/learning.json" format).
Collect about 45 VERIFIED resources for becoming a compute infrastructure engineer, spread over: books (open access first), open courses with public material (CMU DL Systems / ML Systems, Stanford CS149 and CS336, Berkeley CS267, MIT, ETH, EPCC online material, NVIDIA DLI, HPC Carpentry...), must-read papers/reports (Megatron-LM, ZeRO, FSDP, Llama 3 herd of models, MegaScale, Meta/Microsoft/Alibaba GPU-cluster reliability studies, Gemini in-memory checkpoints, CheckFreq, Ray, SkyPilot, Borg/Omega/Kubernetes, Slurm, ring all-reduce, roofline, 'How to Scale Your Model', Hugging Face Ultra-Scale Playbook...), certifications (CKA/CKAD, NVIDIA certifications for AI infrastructure/operations, LFCS, SchedMD Slurm training, HPC Certification Forum, relevant cloud ones — current exam name, provider, cost/format only if the official page prints them), official documentation entry points (Slurm, Kubernetes, NCCL, PyTorch distributed, Ray, SkyPilot, DCGM, Prometheus, Terraform, Ansible, Lustre, DeepSpeed, Megatron-LM...), communities/conferences (SC, ISC, Slurm User Group, KubeCon, Ray Summit, MLSys, EuroHPC).
For each: title/authors/year/url verified on the target page itself (arXiv abs pages, publisher pages, course home pages) and a verbatim quote from the page (e.g. the title line or abstract sentence). Tag topics from the 26-topic taxonomy, level, cost.`

const SCHEMA = {
  type: 'object',
  properties: {
    unit: { type: 'string' }, file: { type: 'string' },
    items_count: { type: 'number' }, validator_passed: { type: 'boolean' },
    quotes_verified: { type: 'string' },
    blocked_sources: { type: 'array', items: { type: 'string' } },
    dropped_candidates: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['unit', 'file', 'items_count', 'validator_passed', 'notes'],
}

const UNITS = [
  { id: 'eu-b', kind: 'm', region: 'world', n: '4', label: 'Europe 2 — Italy, Spain, Nordics, Netherlands',
    seed: `- ICTP-SISSA Master in High Performance Computing (MHPC), Trieste
- Politecnico di Milano MSc HPC Engineering
- KTH (Computer Science / Computational Science) and/or UPC Barcelona MIRI HPC / BSC training, and/or VU Amsterdam Parallel and Distributed Computer Systems
Pick the 4 with the best publicly readable curricula; prefer distinctive (industry- or operations-linked) offers.` },
  { id: 'row', kind: 'm', region: 'world', n: '4', label: 'Rest of the world — India, Japan, Singapore/Korea, Middle East, Canada',
    seed: `- India: C-DAC PG Diploma in HPC System Administration (PG-DHPCSA) — operations/sysadmin-oriented, important; IISc Computational and Data Sciences
- Japan: University of Tokyo IST or Institute of Science Tokyo (ex Tokyo Tech, TSUBAME) or University of Tsukuba CCS
- Canada: University of Toronto / SciNet HPC certificate; Singapore NUS/NTU or KAIST; KAUST
Pick 4 programmes with publicly readable curricula; put short courses and certificates in ecosystem (2-3 items).` },
  { id: 'jobs', kind: 'j', n: '10', seed: `Mix Paris/Europe and US/global employers hiring for GPU cluster, compute platform, ML/AI infrastructure or HPC roles: AI labs and startups (Mistral AI, Hugging Face, H Company, Anthropic, OpenAI...), GPU clouds (Scaleway, OVHcloud, Nebius, CoreWeave, Lambda, Crusoe, Together AI), HPC centres (GENCI, IDRIS, national labs). Public ATS endpoints (Greenhouse https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true , Lever https://api.lever.co/v0/postings/<company>?mode=json , Ashby https://api.ashbyhq.com/posting-api/job-board/<name>) print as text with fetch_text.py.`,
    extra: `ALSO include two SEED postings anonymized: fetch https://app.dover.com/api/v1/inbound/application-portal-job/e314405d-7978-4307-9680-739e25e2ea4b and https://app.dover.com/api/v1/inbound/application-portal-job/13b60d6e-5abc-4e45-9cdc-e1cc74363a82 with fetch_text.py. Extract skills like the others (verbatim quotes from the printed text) but set company to "startup robotique (Paris)", give NO url, and never write the real company name anywhere in the file (also not in quotes: choose quotes that do not contain it). Because they have no URL, the verifier cannot check them: that is expected.` },
]

phase('Research')
const results = await parallel(UNITS.map((u) => () => {
  const prompt = u.kind === 'm' ? MASTERS(u) : u.kind === 'j' ? JOBS(u) : RES
  return agent(prompt, { label: `research:${u.id}`, phase: 'Research', schema: SCHEMA })
}))
const ok = results.filter(Boolean)
const failed = UNITS.map((u) => u.id).filter((id) => !ok.find((r) => r.unit === id))
if (failed.length) log(`Units without result: ${failed.join(', ')}`)
return { ok, failed }
