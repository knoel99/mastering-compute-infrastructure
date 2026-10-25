#!/usr/bin/env python3
"""Assemble data/resources/learning.json from (a) a hand-curated list of sources read for this site
and (b) the ecosystem items already collected in data/masters/*.json (their quotes are verified).
Then run:  python3 tools/verify_quotes.py data/resources/learning.json --write && python3 tools/gen_resources.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Y = 2026


def it(i, kind, title, by, year, url, topics, level, cost, why, quote):
    return {"id": i, "kind": kind, "title": title, "by": by, "year": year, "url": url, "topics": topics, "level": level,
            "cost": cost, "why": why, "evidence": {"url": url, "quote": quote, "source": "web"}}


CURATED = [
    # ---- papers
    it("palm", "paper", "PaLM: Scaling Language Modeling with Pathways", "Chowdhery et al.", 2022, "https://arxiv.org/abs/2204.02311", ["ml-systems", "perf-model"], "advanced", "free", "Définition du MFU (section 4.1) et formule des FLOP par token (annexe B).", "PaLM: Scaling Language Modeling with Pathways"),
    it("llama3", "paper", "The Llama 3 Herd of Models", "Dubey et al.", 2024, "https://arxiv.org/abs/2407.21783", ["ml-systems", "resilience"], "advanced", "free", "Tableau 4 (MFU par configuration de parallélisme) et section 3.3.4 sur la fiabilité à 16 000 GPU.", "The Llama 3 Herd of Models"),
    it("zero", "paper", "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models", "Rajbhandari et al.", 2020, "https://arxiv.org/abs/1910.02054", ["ml-systems"], "advanced", "free", "Section 3.1 : 16 octets par paramètre en précision mixte avec Adam ; partition des états d'optimiseur.", "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models"),
    it("megatron", "paper", "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM", "Narayanan et al.", 2021, "https://arxiv.org/abs/2104.04473", ["ml-systems"], "advanced", "free", "Combinaison des parallélismes de données, tensoriel et pipeline à grande échelle.", "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM"),
    it("fsdp", "paper", "PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel", "Zhao et al.", 2023, "https://arxiv.org/abs/2304.11277", ["ml-systems"], "advanced", "free", "Conception et retours d'expérience de FSDP, base du module 9.", "PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel"),
    it("ray-paper", "paper", "Ray: A Distributed Framework for Emerging AI Applications", "Moritz et al.", 2017, "https://arxiv.org/abs/1712.05889", ["distributed-sys", "ml-systems"], "intermediate", "free", "Modèle de tâches et d'acteurs de Ray, base du module 11.", "Ray: A Distributed Framework for Emerging AI Applications"),
    it("flashattention", "paper", "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness", "Dao et al.", 2022, "https://arxiv.org/abs/2205.14135", ["gpu-prog", "perf-model"], "advanced", "free", "Un exemple de noyau gouverné par le trafic mémoire : lien direct avec le roofline.", "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness"),
    it("megascale", "paper", "MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs", "Jiang et al.", 2024, "https://arxiv.org/abs/2402.15627", ["ml-systems", "resilience", "observability-sre"], "advanced", "free", "Retour d'expérience de ByteDance sur l'efficacité, le diagnostic et la tolérance aux pannes à plus de 10 000 GPU.", "MegaScale: Scaling Large Language Model Training to More Than 10,000 GPUs"),
    it("revisiting-reliability", "paper", "Revisiting Reliability in Large-Scale Machine Learning Research Clusters", "Kokolis et al.", 2024, "https://arxiv.org/abs/2410.21680", ["resilience", "observability-sre"], "advanced", "free", "Étude de la fiabilité de grands clusters de recherche en apprentissage automatique.", "Revisiting Reliability in Large-Scale Machine Learning Research Clusters"),
    it("acme", "paper", "Characterization of Large Language Model Development in the Datacenter", "Hu et al.", 2024, "https://arxiv.org/abs/2403.07648", ["resilience", "scheduling", "observability-sre"], "advanced", "free", "Caractérisation de charges de développement de LLM et de leurs pannes dans un centre de calcul.", "Characterization of Large Language Model Development in the Datacenter"),
    it("roofline", "paper", "Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures", "Williams, Waterman, Patterson", 2008, "https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.html", ["perf-model"], "intermediate", "free", "Version rapport technique de l'article du modèle roofline (version CACM 2009 : doi:10.1145/1498765.1498785).", "Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures"),
    it("hoefler-belli", "paper", "Scientific Benchmarking of Parallel Computing Systems: Twelve Ways to Tell the Masses when Reporting Performance Results", "Hoefler, Belli", 2015, "https://evaluate.inf.usi.ch/node/366", ["perf-model"], "intermediate", "free", "Règles de mesure et de rapport statistique ; base des chapitres 3 et 8 du module 2.", "Twelve Ways to Tell the Masses when Reporting Performance Results"),
    it("patarasuk-yuan", "paper", "Bandwidth optimal all-reduce algorithms for clusters of workstations", "Patarasuk, Yuan", 2009, "https://www.cs.fsu.edu/~xyuan/paper/09jpdc.pdf", ["interconnect", "ml-systems"], "advanced", "free", "Borne inférieure de données émises par un all-reduce et algorithme en anneau optimal.", "Bandwidth optimal all-reduce algorithms for clusters of workstations"),
    # ---- docs and tools
    it("slurm-priority", "docs", "Slurm — Multifactor Priority Plugin", "SchedMD", Y, "https://slurm.schedmd.com/priority_multifactor.html", ["scheduling"], "intermediate", "free", "La formule de priorité d'un job et ses poids (module 5, chapitre 3).", "Job_priority"),
    it("slurm-fairtree", "docs", "Slurm — Fair Tree Fairshare Algorithm", "SchedMD", Y, "https://slurm.schedmd.com/fair_tree.html", ["scheduling"], "intermediate", "free", "Algorithme d'équité par défaut depuis 19.05 (module 5, chapitre 3).", "Fair Tree Fairshare Algorithm"),
    it("slurm-preempt", "docs", "Slurm — Preemption", "SchedMD", Y, "https://slurm.schedmd.com/preempt.html", ["scheduling"], "intermediate", "free", "PreemptType, PreemptMode, GraceTime (module 5, chapitre 4).", "PreemptMode"),
    it("slurm-gres", "docs", "Slurm — Generic Resource (GRES) Scheduling", "SchedMD", Y, "https://slurm.schedmd.com/gres.html", ["scheduling", "gpu-prog"], "intermediate", "free", "Déclaration des GPU et gestion de MIG (module 5, chapitre 5).", "MIG Management"),
    it("slurm-topology", "docs", "Slurm — Topology Guide", "SchedMD", Y, "https://slurm.schedmd.com/topology.html", ["scheduling", "interconnect"], "advanced", "free", "topology/tree, topology/block et --switches (module 5, chapitre 5).", "Block Topology"),
    it("slurm-prolog", "docs", "Slurm — Prolog and Epilog Guide", "SchedMD", Y, "https://slurm.schedmd.com/prolog_epilog.html", ["scheduling", "sysadmin"], "intermediate", "free", "Sémantique des prologues et épilogues et conséquences de leurs échecs (module 5, chapitre 7).", "Prolog and Epilog Guide"),
    it("slurm-sbatch", "docs", "Slurm — sbatch", "SchedMD", Y, "https://slurm.schedmd.com/sbatch.html", ["scheduling"], "intro", "free", "Toutes les options de soumission, dont --signal, --requeue et --gpus-per-node.", "--gpus-per-node"),
    it("slurm-sinfo", "docs", "Slurm — sinfo", "SchedMD", Y, "https://slurm.schedmd.com/sinfo.html", ["scheduling", "sysadmin"], "intro", "free", "États de nœuds et sorties de sinfo.", "DRAINING"),
    it("slurm-squeue", "docs", "Slurm — squeue", "SchedMD", Y, "https://slurm.schedmd.com/squeue.html", ["scheduling"], "intro", "free", "Codes de raison d'attente d'un job.", "InvalidAccount"),
    it("slurm-cgroup", "docs", "Slurm — cgroup.conf", "SchedMD", Y, "https://slurm.schedmd.com/cgroup.conf.html", ["scheduling", "sysadmin"], "intermediate", "free", "ConstrainDevices, ConstrainCores, ConstrainRAMSpace.", "ConstrainDevices"),
    it("nccl-tests", "docs", "nccl-tests — performance metrics", "NVIDIA", Y, "https://raw.githubusercontent.com/NVIDIA/nccl-tests/master/doc/PERFORMANCE.md", ["interconnect", "ml-systems"], "intermediate", "free", "Définitions de algbw et busbw, base du module 7.", "algbw"),
    it("pyxis", "tool", "Pyxis — Slurm container plugin", "NVIDIA", Y, "https://raw.githubusercontent.com/NVIDIA/pyxis/master/README.md", ["containers-k8s", "scheduling"], "intermediate", "free", "Plugin SPANK qui ajoute --container-image à srun.", "Pyxis is a [SPANK]"),
    it("nhc", "tool", "LBNL Node Health Check (NHC)", "Lawrence Berkeley National Laboratory", Y, "https://raw.githubusercontent.com/mej/nhc/master/README.md", ["sysadmin", "resilience"], "intermediate", "free", "Implémentation de référence d'un contrôle de santé de nœud pour Slurm et d'autres ordonnanceurs.", "LBNL Node Health Check (NHC)"),
    it("slinky", "tool", "Slinky — Slurm and Kubernetes", "SchedMD / NVIDIA", Y, "https://www.nvidia.com/en-us/software/slinky/", ["containers-k8s", "scheduling"], "intermediate", "free", "Projet ouvert pour exécuter des clusters Slurm dans Kubernetes (module 5, chapitre 8 ; module 12).", "enables seamless interoperability between Slurm and Kubernetes"),
]

KIND_MAP = {"cours-ouvert": "course", "formation-courte": "course", "centre": "community", "compétition": "community", "réseau": "community"}


def imported():
    out = []
    for f in sorted((ROOT / "data" / "masters").glob("*.json")):
        if f.name == "synthesis.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("ecosystem", []):
            ev = [x for x in e.get("evidence", []) if x.get("source", "web") == "web" and x.get("quote")]
            if not ev or e["kind"] not in KIND_MAP:
                continue
            out.append({"id": "eco-" + e["id"], "kind": KIND_MAP[e["kind"]], "title": e["name"].split(" (")[0][:110], "by": "", "year": Y, "url": e["url"],
                        "topics": [], "level": "intermediate", "cost": "unknown", "why": e["why_relevant"],
                        "evidence": {"url": ev[0]["url"], "quote": ev[0]["quote"], "source": "web"}})
    return out


items = CURATED + imported()
# items added directly to learning.json (for example by a later research pass) are kept, not silently dropped
f = ROOT / "data" / "resources" / "learning.json"
if f.exists():
    known = {i["id"] for i in items}
    items += [i for i in json.loads(f.read_text(encoding="utf-8")).get("items", []) if i["id"] not in known]
(ROOT / "data" / "resources").mkdir(parents=True, exist_ok=True)
(ROOT / "data" / "resources" / "learning.json").write_text(json.dumps({"unit": "res", "retrieved_on": "2026-10-25", "items": items, "blocked_sources": [], "verification": {"status": "unverified"}}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(CURATED), "curated +", len(items) - len(CURATED), "imported =", len(items))
