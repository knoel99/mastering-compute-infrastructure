"""Facts for the HPC master's survey. Pages are a projection of this file."""

from __future__ import annotations

from domain import (
    AccessDate,
    Course,
    CoursesAbsent,
    CoursesUnknown,
    CreditsAbsent,
    CreditsUnknown,
    Described,
    Ects,
    Elsewhere,
    Gap,
    GapId,
    HardwareAbsent,
    HardwareUnknown,
    HttpUrl,
    InChina,
    InFrance,
    InUsa,
    Language,
    LanguageUnknown,
    ListedCourses,
    Meta,
    OtherCredits,
    Prerequisite,
    PrerequisitesAbsent,
    PrerequisitesListed,
    PrerequisitesUnknown,
    Program,
    ProgramId,
    ProjectAbsent,
    ProjectDescribed,
    ProjectKind,
    ProjectUnknown,
    Source,
    StudyId,
    StudyKind,
    StudyResource,
    StudyStep,
    Topic,
    TopicId,
)

DAY = AccessDate(2026, 10, 24)


def S(url: str) -> Source:
    return Source(HttpUrl(url), DAY)


def tops(*ids: str) -> tuple[TopicId, ...]:
    return tuple(TopicId(item) for item in ids)


def course(short: str, detail: str, url: str, *ids: str) -> Course:
    return Course(short, detail, S(url), tops(*ids))


def listed(url: str, *items: Course) -> ListedCourses:
    return ListedCourses(items, S(url))


def pre(short: str, detail: str, url: str) -> Prerequisite:
    return Prerequisite(short, detail, S(url))


def pres(url: str, *items: Prerequisite) -> PrerequisitesListed:
    return PrerequisitesListed(items, S(url))


def body(short: str, detail: str, url: str, *ids: str) -> Described:
    return Described(short, detail, S(url), tops(*ids))


def project(kind: ProjectKind, short: str, detail: str, url: str, *ids: str) -> ProjectDescribed:
    return ProjectDescribed(kind, body(short, detail, url, *ids))


SACLAY = "https://www.universite-paris-saclay.fr/formation/master/calcul-haute-performance-simulation"
SACLAY_M1 = "https://www.universite-paris-saclay.fr/formation/master/calcul-haute-performance-simulation/m1-calcul-haute-performance-simulation"
SACLAY_IHPS = "https://www.universite-paris-saclay.fr/formation/master/calcul-haute-performance-simulation/m2-informatique-haute-performance-et-simulation-ihps"
SACLAY_MSCHP = "https://www.universite-paris-saclay.fr/formation/master/calcul-haute-performance-simulation/m2-modelisation-et-simulation-avec-le-calcul-haute-performance"
UVSQ_M1 = "https://www.chps.uvsq.fr/m1"
UVSQ_M2 = "https://www.chps.uvsq.fr/m2"
SORBONNE = "https://sciences.sorbonne-universite.fr/en/Masters/masters-degree-mathematics-and-applications/masters-high-performance-computing-hpc"
MSIAM_CUR = "https://msiam.imag.fr/m2siam/curriculum/"
MSIAM_COURSES = "https://msiam.imag.fr/courses/"
MSIAM_APP = "https://msiam.imag.fr/admission/application-process/"
MSIAM_CAT = "https://formations.univ-grenoble-alpes.fr/fr/catalogue-2021/master-XB/master-mathematiques-et-applications-IAQKA8QE/master-of-science-in-industrial-and-applied-mathematics-msiam-IB9H19KL.html"
STRAS = "https://formations.unistra.fr/fr/formations/master-MAS/master-mathematiques-et-applications-ME195/calcul-scientifique-et-mathematiques-de-l-innovation-csmi-PR438.html"
IPPARIS = "https://www.ip-paris.fr/en/education/masters/computer-science-program/major-parallel-and-distributed-systems-pds"
LILLE = "https://sciences-technologies.univ-lille.fr/mathematiques/formation/master-mention-mathematiques-et-applications/parcours-cs"
LILLE_M1 = "https://sciences-technologies.univ-lille.fr/filefst/user_upload/mathematiques/Formation/Master/maths_applications/plaquettes/Livret_peda_26_27_M1_MA_SCIENTIFIC_COMPUTING_VF-2.pdf"
LILLE_M2 = "https://sciences-technologies.univ-lille.fr/filefst/user_upload/mathematiques/Formation/Master/maths_applications/LOP_M2/livretM2_2627_CALSCI__.pdf"
BORDEAUX = "https://formations.u-bordeaux.fr/details-formation?id=1681&type=periode"

GT = "https://catalog.gatech.edu/programs/computational-science-engineering-ms/"
GT_CSE = "https://catalog.gatech.edu/courses-grad/cse/"
STAN = "https://bulletin.stanford.edu/programs/CME-MS"
STAN_213 = "https://bulletin.stanford.edu/courses/2120661"
STAN_HPC = "https://icme.stanford.edu/get-involved/icme-resources/hpc-resources"
UT = "https://catalog.utexas.edu/graduate/programs/computational-science-engineering-mathematics-mscsem/"
UT_ODEN = "https://oden.utexas.edu/academics/masters-program/"
UT_PDF = "https://oden.utexas.edu/media/academics/public_files/CSEM_Approved_Courses_by_Area.pdf"
MIT = "https://catalog.mit.edu/degree-charts/master-computational-science-engineering/"
MIT_SM = "https://cse.mit.edu/programs-admissions/cse-sm/"
HARVARD = "https://seas.harvard.edu/masters-computational-science-and-engineering/degree-requirements"
HARVARD_HOME = "https://seas.harvard.edu/masters-computational-science-and-engineering"
NYU = "https://bulletins.nyu.edu/graduate/arts-science/programs/scientific-computing-ms/"
NYU_DEPT = "https://math.nyu.edu/dynamic/graduate/ms-gsas/ms-scientific-computing/"
UCHI_PDF = "https://bpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/4/4035/files/2026/04/MPCS_ProgramRequirements_12_CourseHPC.pdf"
UCHI = "https://masters.cs.uchicago.edu/hpc-specialization-2/"
FSU = "https://www.sc.fsu.edu/images/docs/graduate_handbook_2026-03.pdf"

USTC = "https://gradschool.ustc.edu.cn/static/upload/article/ueditor/1758537439275-615627.pdf"
PKU = "https://admission.pku.edu.cn/zsxx/sszs/zyml/2026/yx/zsml_ss_yx_00101.pdf"
PKU_BROCHURE = "https://admission.pku.edu.cn/docs/20251009101959431969.pdf"
TSING = "https://ac.cs.tsinghua.edu.cn/"
TSING_CUR = "https://ac.cs.tsinghua.edu.cn/curriculum.html"
TSING_APP = "https://ac.cs.tsinghua.edu.cn/application.html"
BUAA = "https://is.buaa.edu.cn/Master-Program-Major-List-of-2026-Beihang.pdf"
BUAA_ANN = "https://is.buaa.edu.cn/en/info/1029/3071.htm"
SYSU = "https://cse.sysu.edu.cn/article/3663"
SYSU_SUP = "https://cse.sysu.edu.cn/article/3564"
ZJU = "http://www.cs.zju.edu.cn/csen/2025/0728/c27006a3071976/page.htm"
ZJU_LAB = "http://vm.zju.edu.cn/team/chen-jian-hai.html"

EDIN = "https://study.ed.ac.uk/programmes/postgraduate-taught/187-high-performance-computing"
EDIN_EPCC = "https://www.epcc.ed.ac.uk/education-training/masters-programmes"
EDIN_DPT = "https://www.drps.ed.ac.uk/26-27/dpt/ptmschpcmp1f.htm"
TUD = "https://tu-dresden.de/ing/informatik/studium/studienangebot/master-studiengaenge/m-sc-computer-science?set_language=en"
TUD_ADM = "https://tu-dresden.de/ing/informatik/studium/studienangebot/master-studiengaenge/m-sc-computer-science/admission"
TUD_PLAN = "https://tu-dresden.de/ing/informatik/ressourcen/dateien/studium/studien_und_pruefungsordnungen/2026-2027-WiSe-MA-Computer-Science-StAP.pdf?lang=de"
ETH = "https://ethz.ch/en/studies/master/degree-programmes/engineering-sciences/computational-science-and-engineering.html"
ETH_M = "https://rw.ethz.ch/the-programme/master.html"
ETH_APP = "https://ethz.ch/content/dam/ethz/common/docs/master-profile/englisch/naturwissenschaften/MSc-Computational-Science-Engineering-Appendix.pdf"
ETH_GL = "https://ethz.ch/content/dam/ethz/special-interest/study-programme-websites/ms-compsci-and-eng-dam/documents/master-programme/MSc-CSE-GL-curr.pdf"
VU = "https://vu.nl/en/education/master/computer-science-joint-degree-vu-uva/curriculum"
VU_ADM = "https://vu.nl/en/education/master/computer-science-joint-degree-vu-uva/admissions"
UVA = "https://www.uva.nl/shared-content/programmas/en/masters/computer-science-computer-systems-and-infrastructure/study-programme/study-programme.html"
KTH = "https://www.kth.se/en/studies/master/computer-science/msc-computer-science-1.419974"
KTH_C = "https://www.kth.se/en/studies/master/computer-science/courses-computer-science-1.502267"
KTH_E = "https://www.kth.se/en/studies/master/computer-science/entry-requirements-computer-science-1.419975"
EURO = "https://www.eurohpc-ju.europa.eu/research-innovation/our-projects/eumaster4hpc-phase-2_en"
EURO_C = "https://eumaster4hpc.eu/studies/curriculum/"
EURO_H = "https://eumaster4hpc.eu/"
IISC = "https://cds.iisc.ac.in/admissions/course-degrees/"
IISC_C = "https://cds.iisc.ac.in/academics/mtechcds/"
IISC_H = "https://cds.iisc.ac.in/internal-resources/computing-resources/"
AIZU = "https://u-aizu.ac.jp/en/curriculum/graduate/master/"
AIZU_REG = "https://u-aizu.ac.jp/files/page/intro/regulations/reg005_e.pdf"
AIZU_ADM = "https://u-aizu.ac.jp/files/admissions/2027_m_out_e.pdf"
AIZU_SYL = "https://web-ext.u-aizu.ac.jp/official/curriculum/syllabus/2026_2_E_002.html"
POLIMI = "https://www.polimi.it/en/education/laurea-magistrale-programmes/programme-detail/high-performance-computing-engineering"
POLIMI_REG = "https://onlineservices.polimi.it/manifesti/manifesti/controller/extra/RegolamentoPublic.do?EVN_DEFAULT=evento&aa=2026&jaf_currentWFID=main&k_corso_la=550&lang=EN"

UNREAD = "La page officielle n'a pas pu être ouverte lors de la lecture."


def _france() -> tuple[Program, ...]:
    chps = Program(
        id=ProgramId("fr-paris-saclay-chps"),
        placement=InFrance("Saclay"),
        school="Université Paris-Saclay",
        program_name="Master Calcul haute performance, simulation (CHPS)",
        language=Language.FR,
        credits=CreditsAbsent(
            "La page de mention n'imprime pas de total de diplôme, et le stage de M2 n'a pas le même volume sur Paris-Saclay et à l'UVSQ",
            S(SACLAY),
        ),
        home=S(SACLAY),
        core=listed(
            SACLAY_M1,
            course(
                "Calcul numérique",
                "Cours de M1, 5 ECTS, sur la table de cours Paris-Saclay.",
                SACLAY_M1,
                "numerical",
            ),
            course(
                "Architecture parallèle",
                "Cours de M1, 5 ECTS, sur la table de cours Paris-Saclay.",
                SACLAY_M1,
                "architecture",
            ),
            course(
                "Architecture interne des systèmes d'exploitation",
                "Cours de M1, 3 ECTS, sur la table de cours Paris-Saclay.",
                SACLAY_M1,
                "architecture",
            ),
            course(
                "Algorithmique et programmation parallèle",
                "Cours de M1, 5 ECTS. La page UVSQ nomme les langages et bibliothèques MPI, OpenMP et pthread.",
                UVSQ_M1,
                "mpi",
                "openmp",
            ),
            course(
                "Projet de programmation sur machine parallèle",
                "Cours de M1, 4 ECTS. L'objectif UVSQ demande de programmer sur une machine parallèle.",
                UVSQ_M1,
            ),
            course(
                "Techniques d'optimisation de la parallélisation",
                "Cours de M1, 3 ECTS. La page UVSQ vise les pertes de performance, les mesures de performances et les outils d'analyse de performance.",
                UVSQ_M1,
                "performance",
            ),
            course(
                "Programmation avancée des architectures multicoeurs",
                "Tronc commun HPCS du M2 IHPS, 3 ECTS. Gaël Thomas, Telecom SudParis, est nommé sur la page UVSQ.",
                SACLAY_IHPS,
                "architecture",
            ),
            course(
                "Architecture et programmation d'accélérateurs matériels",
                "Tronc commun HPCS du M2 IHPS, 3 ECTS, sigle APM.",
                SACLAY_IHPS,
                "architecture",
            ),
            course(
                "Évaluation de performances",
                "Tronc commun HPCS du M2 IHPS, 3 ECTS, sigle EDP.",
                SACLAY_IHPS,
                "performance",
            ),
            course(
                "Méthodes et programmation numériques avancées",
                "Tronc commun HPCS du M2 IHPS, 3 ECTS, sigle MPNA.",
                SACLAY_IHPS,
                "numerical",
            ),
            course(
                "Données et apprentissage",
                "Tronc commun HPCS du M2 IHPS, 3 ECTS, sigle DA. La page ne dit pas que ce cours est un système d'apprentissage.",
                SACLAY_IHPS,
            ),
        ),
        electives=listed(
            UVSQ_M2,
            course(
                "Architecture et optimisation de codes",
                "Option B2 du M2 IHPS, 3 ECTS. Titre complet : architecture et optimisation de codes pour microprocesseur haute performance.",
                SACLAY_IHPS,
                "architecture",
                "performance",
            ),
            course(
                "Compilation avancée",
                "Option B2 du M2 IHPS, 3 ECTS.",
                SACLAY_IHPS,
            ),
            course(
                "Paradigmes de programmation pour le calcul scientifique",
                "Option B2 du M2 IHPS, 3 ECTS.",
                SACLAY_IHPS,
            ),
            course(
                "Calcul quantique",
                "Option B2 du M2 IHPS, 3 ECTS.",
                SACLAY_IHPS,
            ),
            course(
                "Introduction à la simulation moléculaire",
                "Option B2 du M2 IHPS, 3 ECTS.",
                SACLAY_IHPS,
            ),
            course(
                "Stratégies de calcul multi-échelle",
                "Option B1 du M2 MSCHP, 3 ECTS. Titre : stratégie de calcul multi-échelle et méthode de décomposition de domaine.",
                SACLAY_MSCHP,
            ),
            course(
                "Modélisation et simulation en mécanique des fluides",
                "Option B1 du M2 MSCHP, 3 ECTS.",
                SACLAY_MSCHP,
            ),
            course(
                "Réduction de modèles",
                "Option B1 du M2 MSCHP, 3 ECTS.",
                SACLAY_MSCHP,
            ),
            course(
                "Méthode et simulation en mécanique des structures",
                "Option B1 du M2 MSCHP, 3 ECTS.",
                SACLAY_MSCHP,
            ),
        ),
        project=project(
            ProjectKind.EITHER,
            "Stage et unités de projet",
            "La mention décrit un stage de 5 à 6 mois en laboratoire ou en R et D industrielle, et des unités de projet pendant les deux années. Paris-Saclay imprime un stage de 24 ECTS, l'UVSQ un semestre 4 de stage à 30 ECTS.",
            SACLAY,
        ),
        hardware=HardwareAbsent(
            "La page de mention ne nomme ni un cluster étudiant ni un compte",
            S(SACLAY),
        ),
        prerequisites=pres(
            SACLAY,
            pre(
                "Licence d'informatique, de mathématiques ou de physique",
                "La mention s'adresse aux titulaires d'un diplôme équivalent à l'une de ces trois licences.",
                SACLAY,
            ),
            pre(
                "Entrée directe en M2",
                "La mention ouvre aussi le M2 aux étudiants ayant validé un M1 ou la quatrième année d'un cycle ingénieur.",
                SACLAY,
            ),
        ),
    )
    sorbonne = Program(
        id=ProgramId("fr-sorbonne-hpc"),
        placement=InFrance("Paris"),
        school="Sorbonne Université",
        program_name="Master's in High Performance Computing",
        language=Language.EN,
        credits=CreditsAbsent(
            "La page ne donne pas de total de diplôme. Les nombres 48 ECTS et 60 ECTS figurent seulement dans la règle du diplôme EUMaster4HPC",
            S(SORBONNE),
        ),
        home=S(SORBONNE),
        core=listed(
            SORBONNE,
            course("Computer hardware and parallel architectures", "Semestre 1 du programme. La page n'imprime pas d'ECTS par cours.", SORBONNE, "architecture"),
            course("Parallel Programming", "Semestre 1. Le titre ne nomme ni MPI, ni OpenMP, ni CUDA.", SORBONNE),
            course("Foundations of numerical methods", "Semestre 1. Le titre précise finite differences and finite elements.", SORBONNE, "numerical"),
            course("Numerical algorithms: arithmetics and reliability", "Semestre 2.", SORBONNE, "numerical"),
            course("Multicore and multiprocessor architectures", "Semestre 2.", SORBONNE, "architecture"),
            course("Approximation of PDEs and numerical simulation", "Semestre 2.", SORBONNE, "numerical"),
            course("Advanced HPC algorithms and many-core architectures", "Semestre 3. Titre : Advanced high performance computing algorithms and programming many core architectures.", SORBONNE, "architecture"),
            course("Parallelism and accelerators for cluster computing", "Semestre 3. Le titre ne nomme pas CUDA.", SORBONNE),
            course("Finite elements methods in practice", "Semestre 3.", SORBONNE, "numerical"),
            course("HPC for numerical methods and data analysis", "Semestre 3. Titre : High performance computing for numerical methods and data Analysis.", SORBONNE, "numerical"),
        ),
        electives=listed(
            SORBONNE,
            course("Modern methods and algorithms for parallel computation", "Semestre 4, marqué elective. Le titre ajoute domain decomposition.", SORBONNE),
            course("Approximation and data analysis in large dimension", "Semestre 4, marqué elective.", SORBONNE),
            course("Neural networks and adaptive numerical approximation", "Semestre 4, marqué elective.", SORBONNE, "numerical"),
            course("Tensor methods for solving PDEs in large dimension", "Semestre 4, marqué elective. La page ne dit pas combien d'électifs sont exigés.", SORBONNE),
        ),
        project=project(
            ProjectKind.EITHER,
            "Projet et master thesis",
            "Le semestre 2 contient un Project et le semestre 4 un Master thesis. La page dit aussi qu'un stage en laboratoire ou en groupe industriel est possible.",
            SORBONNE,
        ),
        hardware=HardwareAbsent(
            "La page parle d'une exposition aux centres européens de supercalcul et ne nomme ni machine ni compte",
            S(SORBONNE),
        ),
        prerequisites=pres(
            SORBONNE,
            pre(
                "Licence de mathématiques ou d'informatique",
                "La page demande un Bachelor's degree in Mathematics and/or Computer Science.",
                SORBONNE,
            ),
            pre(
                "Anglais et bases numériques",
                "La page demande un anglais au moins CEFR B2, TOEFL 85 ou IELTS 5, l'algèbre linéaire, l'analyse numérique de base, et un langage, de préférence C ou C++.",
                SORBONNE,
            ),
        ),
    )
    msiam = Program(
        id=ProgramId("fr-grenoble-msiam"),
        placement=InFrance("Grenoble"),
        school="Université Grenoble Alpes",
        program_name="Master of Science in Industrial and Applied Mathematics (MSIAM)",
        language=Language.EN,
        credits=Ects(120, S(MSIAM_CAT)),
        home=S(MSIAM_CUR),
        core=listed(
            MSIAM_COURSES,
            course("Advanced numerical methods for PDEs and optimal transport", "Carte taguée MSCI. La page ne dit pas quels cours sont obligatoires dans les 30 ECTS scientifiques.", MSIAM_COURSES, "numerical"),
            course("An introduction to shape and topology optimization", "Carte taguée MSCI.", MSIAM_COURSES),
            course("Differential Calculus, Wavelets and Applications", "Carte taguée MSCI.", MSIAM_COURSES),
            course("Geophysical imaging", "Carte taguée MSCI.", MSIAM_COURSES),
            course("GPU Computing", "Carte taguée MSCI. Le texte introduit des paradigmes de programmation parallèle en mathématiques appliquées, sans nommer CUDA, MPI ou OpenMP.", MSIAM_COURSES),
            course("Machine Learning for Physics", "Carte taguée MSCI.", MSIAM_COURSES),
            course("Mathematical optimization", "Carte taguée MSCI.", MSIAM_COURSES),
            course("Modeling Seminar", "Carte taguée MSCI.", MSIAM_COURSES),
        ),
        electives=listed(
            MSIAM_COURSES,
            course("Data Science Seminars and Challenge", "Carte Data Science non taguée MSCI. Le choix de parcours est le mécanisme indiqué.", MSIAM_COURSES),
            course("From Basic Machine Learning models to Advanced Kernel Learning", "Carte Data Science non taguée MSCI.", MSIAM_COURSES),
            course("Generative, Multimodal AI", "Carte Data Science non taguée MSCI.", MSIAM_COURSES),
            course("Mathematical Foundations of Machine Learning", "Carte Data Science non taguée MSCI.", MSIAM_COURSES),
            course("Natural Language Processing and Information Retrieval", "Carte Data Science non taguée MSCI.", MSIAM_COURSES),
        ),
        project=project(
            ProjectKind.EITHER,
            "Master thesis ou stage",
            "La page de curriculum dit que le second semestre est dédié au Master thesis ou Internship, en laboratoire ou en entreprise. Les pages 2026-2027 lues n'impriment pas d'ECTS de mémoire.",
            MSIAM_CUR,
        ),
        hardware=HardwareAbsent(
            "Les pages 2026-2027 lues ne nomment ni cluster ni compte",
            S(MSIAM_COURSES),
        ),
        prerequisites=pres(
            MSIAM_APP,
            pre(
                "M1 de mathématiques et 240 ECTS",
                "La page de candidature demande un M1 déjà fait et au moins 60 ECTS en mathématiques ou mathématiques appliquées, et au total l'équivalent de 240 ECTS.",
                MSIAM_APP,
            ),
            pre(
                "Anglais B2",
                "La page cite TOEFL iBT 78, TOEIC 700 ou IELTS 6, niveau CEFR B2. Un niveau A2 de français est recommandé.",
                MSIAM_APP,
            ),
        ),
    )
    strasbourg = Program(
        id=ProgramId("fr-strasbourg-csmi"),
        placement=InFrance("Strasbourg"),
        school="Université de Strasbourg",
        program_name="Master Mathématiques et applications, parcours CSMI",
        language=Language.FR_EN,
        credits=Ects(120, S(STRAS)),
        home=S(STRAS),
        core=listed(
            STRAS,
            course("UE Calcul haute performance 1", "Semestre 1, 3 ECTS. Le titre ne nomme ni MPI, ni OpenMP, ni CUDA.", STRAS),
            course("UE Calcul haute performance 2", "Semestre 2, 3 ECTS.", STRAS),
            course("UE Calcul haute performance 3", "Semestre 3, 3 ECTS.", STRAS),
            course("UE Calcul scientifique 1", "Semestre 1, 3 ECTS.", STRAS),
            course("UE Méthodes numériques pour les EDP 1", "Semestre 2, 6 ECTS.", STRAS, "numerical"),
            course("UE Méthodes numériques pour les EDP 2", "Semestre 3, 3 ECTS.", STRAS, "numerical"),
            course("UE Système d'exploitation", "Semestre 1, 3 ECTS.", STRAS),
            course("UE C++", "Semestre 1, 3 ECTS.", STRAS),
            course("UE Apprentissage automatique scientifique 1", "Semestre 2, 3 ECTS. Le titre ne décrit pas un système d'apprentissage.", STRAS),
            course(
                "Prétraitement et post-traitement intégrés au réseau",
                "Semestre 3, 3 ECTS. Titre complet : prétraitement et post-traitement intégrés au réseau dans le calcul scientifique.",
                STRAS,
                "networking",
            ),
        ),
        electives=CoursesAbsent(
            "Les tableaux du programme ne marquent aucun groupe au choix",
            S(STRAS),
        ),
        project=project(
            ProjectKind.EITHER,
            "Mémoire et stages",
            "L'UE Mémoire du semestre 4 vaut 30 ECTS. Les stages de M1 et de M2 sont obligatoires, et des UE projet jalonnent le parcours.",
            STRAS,
        ),
        hardware=HardwareAbsent(
            "La page cite le calcul haute performance et des plateformes numériques sans nommer de machine ni de compte",
            S(STRAS),
        ),
        prerequisites=pres(
            STRAS,
            pre(
                "Licence de mathématiques",
                "L'admission en M1 se fait sur dossier pour une licence de mathématiques ou un équivalent, avec un anglais B1.",
                STRAS,
            ),
            pre(
                "Bases d'analyse numérique et de programmation",
                "La page recommande une licence 3 de mathématiques appliquées, avec calcul différentiel et intégral, modélisation, Fourier, statistiques, analyse numérique, et si possible Python ou C++.",
                STRAS,
            ),
        ),
    )
    ipparis = Program(
        id=ProgramId("fr-ip-paris-pds"),
        placement=InFrance("Palaiseau"),
        school="Institut Polytechnique de Paris",
        program_name="Master in Computer Science, major Parallel and Distributed Systems",
        language=Language.EN,
        credits=Ects(120, S(IPPARIS)),
        home=S(IPPARIS),
        core=listed(
            IPPARIS,
            course("High performance runtimes", "Cours listé au semestre, 45 h et 5 ECTS, en anglais. La page ne marque pas les cours obligatoires.", IPPARIS),
            course("Advanced programming of multi-core architectures", "Cours listé, 45 h et 5 ECTS.", IPPARIS, "architecture"),
            course("Cloud infrastructures", "Cours listé, 45 h et 5 ECTS.", IPPARIS, "cloud-containers"),
            course("An Introduction to Computer Architecture and Operating Systems", "Cours listé, 45 h et 5 ECTS.", IPPARIS, "architecture"),
            course("Data analytic infrastructures", "Cours listé, 45 h et 5 ECTS.", IPPARIS),
            course("Operating systems", "Cours du second semestre, 45 h et 5 ECTS.", IPPARIS),
            course("Programming with GPU for Deep Learning", "Cours du second semestre, 24 h et 2,5 ECTS. Le titre ne dit pas CUDA.", IPPARIS),
            course("Technologies of large-scale parallel computing", "Cours du second semestre, 24 h et 2,5 ECTS.", IPPARIS),
            course("Systems for big data", "Cours du second semestre, 45 h et 5 ECTS.", IPPARIS),
            course("Middleware and software architecture for distributed applications", "Cours listé, 45 h et 5 ECTS. Le titre vise l'architecture logicielle, pas l'architecture des machines.", IPPARIS),
        ),
        electives=CoursesAbsent(
            "La page ne marque aucun cours comme électif",
            S(IPPARIS),
        ),
        project=project(
            ProjectKind.EITHER,
            "Projets de recherche et master thesis",
            "Sous le semestre 1, la page indique M1 Research Projects pour 30, M2 Research Projects pour 12,5 et M2 master thesis pour 30, plus un stage de recherche.",
            IPPARIS,
        ),
        hardware=HardwareAbsent(
            "La page ne décrit pas l'accès à une machine",
            S(IPPARIS),
        ),
        prerequisites=pres(
            IPPARIS,
            pre(
                "Licence d'informatique ou de génie électrique",
                "La page demande un Bachelor of Science in Computer Science or Electrical Engineering, et un anglais B2.",
                IPPARIS,
            ),
        ),
    )
    lille = Program(
        id=ProgramId("fr-lille-scientific-computing"),
        placement=InFrance("Lille"),
        school="Université de Lille",
        program_name="Master Mathématiques et applications, parcours Scientific Computing",
        language=LanguageUnknown(
            "Ni la page de faculté ni les livrets n'impriment une langue d'enseignement.",
        ),
        credits=CreditsAbsent(
            "Aucun total de diplôme n'est imprimé. Le livret de M1 imprime 30 ECTS par semestre",
            S(LILLE),
        ),
        home=S(LILLE),
        core=listed(
            LILLE,
            course("UE Méthodes numériques avancées 1", "Semestre 1 du livret M1 2026-2027, 3 ECTS.", LILLE_M1, "numerical"),
            course("UE Méthodes numériques avancées 2", "Semestre 2 du livret M1, 3 ECTS.", LILLE_M1, "numerical"),
            course("UE Numérique avec C++1", "Semestre 1 du livret M1, 3 ECTS.", LILLE_M1),
            course("UE Numérique avec C++2", "Semestre 2 du livret M1, 3 ECTS.", LILLE_M1),
            course("Finite Element Methods", "Livret M2, dans UE Math. Tools for scientific computing, 6 ECTS.", LILLE_M2, "numerical"),
            course("Finite Volume Methods", "Livret M2, 6 ECTS.", LILLE_M2, "numerical"),
            course(
                "UE Super computing",
                "Livret M2, 10,5 ECTS. Le syllabus cite Grid'5000 et nomme OpenMP, MPI et Cuda.",
                LILLE_M2,
                "mpi",
                "openmp",
                "cuda",
            ),
            course("UE Applied scientific computing 1", "Organisation du printemps, livret M2, 9 ECTS.", LILLE_M2),
            course("UE Applied scientific computing 2", "Organisation du printemps, livret M2, 9 ECTS.", LILLE_M2),
        ),
        electives=listed(
            LILLE_M2,
            course(
                "Machine learning and optimization for scientific computing",
                "Le livret M2 dit que deux cours avancés sont à choisir, dont celui-ci. Il n'imprime pas d'ECTS sur ce titre.",
                LILLE_M2,
            ),
            course(
                "Scientific computing for electrical engineering",
                "Second titre du choix de quatrième semestre dans le livret M2, sans ECTS imprimé sur la ligne.",
                LILLE_M2,
            ),
        ),
        project=project(
            ProjectKind.EITHER,
            "Projet encadré et stage",
            "Le livret M1 donne un projet de recherche encadré de 6 ECTS. Le livret M2 donne un Internship de 12 ECTS. La faculté parle d'un stage long de 4 à 6 mois.",
            LILLE,
        ),
        hardware=body(
            "Cluster hybride et Grid'5000",
            "La faculté écrit que les étudiants de M2 disposent du cluster hybride de la DSI, avec des GPU, et de l'accès à Grid'5000.",
            LILLE,
        ),
        prerequisites=pres(
            LILLE_M1,
            pre(
                "Licence de mathématiques ou école d'ingénieurs",
                "Le livret M1 vise une licence de mathématiques, de mathématiques appliquées ou d'ingénierie mathématique, ou des élèves d'écoles d'ingénieurs.",
                LILLE_M1,
            ),
            pre(
                "Passage du M1 Scientific Computing au M2",
                "Le livret M2 dit que les étudiants du M1 Scientific Computing de Lille passent en M2. Les autres candidatures passent par Campus France ou e-candidat.",
                LILLE_M2,
            ),
        ),
    )
    bordeaux = Program(
        id=ProgramId("fr-bordeaux-calcul-intensif"),
        placement=InFrance("Bordeaux"),
        school="Université de Bordeaux",
        program_name="Calcul intensif et sciences des données",
        language=LanguageUnknown(UNREAD),
        credits=CreditsUnknown(UNREAD),
        home=S(BORDEAUX),
        core=CoursesUnknown(UNREAD),
        electives=CoursesUnknown(UNREAD),
        project=ProjectUnknown(UNREAD),
        hardware=HardwareUnknown(UNREAD),
        prerequisites=PrerequisitesUnknown(UNREAD),
    )
    return (chps, sorbonne, msiam, strasbourg, ipparis, lille, bordeaux)


def _usa() -> tuple[Program, ...]:
    gatech = Program(
        id=ProgramId("us-gatech-cse"),
        placement=InUsa("Atlanta", "Géorgie"),
        school="Georgia Institute of Technology",
        program_name="Master of Science in Computational Science and Engineering",
        language=LanguageUnknown("La page de programme 2026-2027 ne dit pas la langue d'enseignement."),
        credits=OtherCredits("heures de crédit", 30, S(GT)),
        home=S(GT),
        core=listed(
            GT,
            course("CSE 6643 Numerical Linear Algebra", "Un des quatre cours à choisir dans le noyau de 12 heures. La liste graduée indique 3 credit hours.", GT_CSE, "numerical"),
            course("CSE 6140 Computational Science and Engineering Algorithms", "Un des quatre cours du noyau. La liste graduée parle d'algorithmes high-performance et scalables, sans nommer MPI.", GT_CSE),
            course("CSE 6730 Modeling and Simulation", "Un des quatre cours du noyau. Le catalogue dit Foundations and Implementation. 3 credit hours.", GT_CSE),
            course("CSE 6740 Computational Data Analysis", "Un des quatre cours du noyau. 3 credit hours.", GT_CSE),
            course("CSE 6220 High Performance Computing", "Un des quatre cours du noyau. 3 credit hours. La liste graduée décrit la conception d'applications de calcul scientifique haute performance, sans nommer MPI, OpenMP ou CUDA.", GT_CSE),
        ),
        electives=CoursesAbsent(
            "La page exige un mineur de 12 heures et n'en publie pas le menu",
            S(GT),
        ),
        project=project(
            ProjectKind.EITHER,
            "Option cours ou thèse",
            "La note 2 demande 6 heures de cours supplémentaires, ou une thèse de master soutenue devant le comité.",
            GT,
        ),
        hardware=HardwareAbsent(
            "La page de programme et la liste des cours CSE ne décrivent pas d'accès à un cluster",
            S(GT),
        ),
        prerequisites=PrerequisitesAbsent(
            "La page de programme ne liste pas de cours antérieurs",
            S(GT),
        ),
    )
    stanford = Program(
        id=ProgramId("us-stanford-cme"),
        placement=InUsa("Stanford", "Californie"),
        school="Stanford University",
        program_name="Master of Science in Computational and Mathematical Engineering",
        language=LanguageUnknown("La page du bulletin ne dit pas la langue d'enseignement."),
        credits=OtherCredits("unités", 45, S(STAN)),
        home=S(STAN),
        core=listed(
            STAN,
            course("CME 302 Numerical Linear Algebra", "Un des six cours de fondation du track général. L'étudiant en choisit quatre, pour au moins 12 unités.", STAN, "numerical"),
            course("CME 303 Partial Differential Equations of Applied Mathematics", "Un des six cours de fondation.", STAN),
            course("CME 306 Computational Methods of Applied Mathematics", "Un des six cours de fondation.", STAN),
            course("CME 307 Optimization", "Un des six cours de fondation, en alternative avec CME 364A Convex Optimization I.", STAN),
            course("CME 310 Combinatorial Optimization", "Un des six cours de fondation.", STAN),
            course("CME 308 Stochastic Methods in Engineering", "Un des six cours de fondation, avec des alternatives stochastiques nommées sur la page.", STAN),
            course(
                "Introduction to parallel computing using MPI, openMP, and CUDA",
                "CME 213, dans le menu de programmation. Le bulletin le recommande fortement pour le track CME. La page du cours décrit une pratique sur multicœurs, GPU et machines parallèles.",
                STAN_213,
                "mpi",
                "openmp",
                "cuda",
            ),
            course("CME 212 Programming for performance", "Cours du menu de programmation de base, au moins 3 unités dans ce groupe.", STAN, "performance"),
        ),
        electives=listed(
            STAN,
            course("CS 149 Parallel Computing", "Titre du menu de programmation avancée du track général. Le menu de breadth est plus long que cette fiche.", STAN),
            course("CS 244B Distributed Systems", "Titre du menu de breadth du track général.", STAN),
            course("CS 315B Parallel Computing Research Project", "Titre du menu de programmation avancée.", STAN),
        ),
        project=project(
            ProjectKind.PROJECT,
            "Recherche optionnelle",
            "La page dit qu'aucune thèse n'est exigée. Un étudiant peut participer à des projets de recherche, et une distinction demande au moins 9 unités de recherche.",
            STAN,
        ),
        hardware=body(
            "Clusters ICME",
            "La page HPC dit que les clusters ICME servent aux étudiants, avec des partitions restreintes pour certains cours. Elle nomme des nœuds cpu et gpu reliés en Infiniband, et un accès sur demande par courriel.",
            STAN_HPC,
        ),
        prerequisites=pres(
            STAN,
            pre(
                "Mathématiques et programmation",
                "Le bulletin recommande l'algèbre linéaire, les probabilités, les équations différentielles, les méthodes numériques et la programmation. Il ne fixe pas de diplôme précis.",
                STAN,
            ),
        ),
    )
    ut = Program(
        id=ProgramId("us-utexas-csem"),
        placement=InUsa("Austin", "Texas"),
        school="The University of Texas at Austin",
        program_name="Master of Science in Computational Science, Engineering, and Mathematics",
        language=LanguageUnknown("La page de catalogue 2026-2027 ne dit pas la langue d'enseignement."),
        credits=OtherCredits("heures de semestre", 30, S(UT)),
        home=S(UT),
        core=listed(
            UT_PDF,
            course("Numerical Analysis: Linear Algebra", "Ligne de l'aire B du PDF Oden, CSE 383C, dernière offre Fall 2026. Au moins six heures sont exigées dans chaque aire.", UT_PDF, "numerical"),
            course("Numerical Analysis: Algebra and Approximation", "Ligne de l'aire B, CSE 383K, Fall 2026.", UT_PDF, "numerical"),
            course("Numerical Analysis: Differential Equations", "Ligne de l'aire B, CSE 383L, Spring 2027.", UT_PDF, "numerical"),
            course("Tools and Techniques of Computational Science", "Ligne de l'aire B, CSE 380, Fall 2026.", UT_PDF),
            course("Parallel Algorithms for Scientific Computing", "Ligne de l'aire B, CSE 392.1, Spring 2027. Le titre ne nomme pas MPI.", UT_PDF),
            course("The Finite Element Method", "Ligne de l'aire B, CSE 393.1, Fall 2026.", UT_PDF, "numerical"),
        ),
        electives=CoursesAbsent(
            "Le PDF contient d'autres lignes d'aires A, B et C que cette fiche ne recopie pas",
            S(UT_PDF),
        ),
        project=project(
            ProjectKind.EITHER,
            "Rapport ou thèse, au choix",
            "La page Oden décrit un rapport comme une revue, équivalent à 3 heures, et une thèse comme une contribution originale, équivalent à 6 heures. Le catalogue permet aussi un parcours sans thèse.",
            UT_ODEN,
        ),
        hardware=HardwareAbsent(
            "Le catalogue et la page Oden du master ne décrivent pas d'accès à un cluster",
            S(UT),
        ),
        prerequisites=pres(
            UT,
            pre(
                "Licence scientifique",
                "Le catalogue attend une licence d'ingénierie, d'informatique, de mathématiques ou d'une science naturelle.",
                UT,
            ),
        ),
    )
    mit = Program(
        id=ProgramId("us-mit-cse"),
        placement=InUsa("Cambridge", "Massachusetts"),
        school="Massachusetts Institute of Technology",
        program_name="Master of Science in Computational Science and Engineering",
        language=LanguageUnknown("Ni la charte ni la page CCSE ne nomment la langue des cours."),
        credits=OtherCredits("unités", 108, S(MIT)),
        home=S(MIT),
        core=listed(
            MIT,
            course("Introduction to Modeling and Simulation", "6.7300, un des sujets dont l'étudiant choisit trois, pour 36 unités. La page CCSE titre le même numéro Introduction to Numerical Simulation.", MIT),
            course("Optimization Methods", "15.C57, un des trois sujets de tronc, 12 unités sur la charte.", MIT),
            course("Numerical Methods for Partial Differential Equations", "16.920, un des trois sujets de tronc.", MIT, "numerical"),
            course("Introduction to Numerical Methods", "18.335, un des trois sujets de tronc.", MIT, "numerical"),
        ),
        electives=listed(
            MIT,
            course(
                "Parallel Computing and Scientific Machine Learning",
                "18.337, 12 unités, une ligne de la liste restreinte de 24 unités. La liste complète est plus longue.",
                MIT,
            ),
        ),
        project=project(
            ProjectKind.THESIS,
            "CSE.THG Graduate Thesis",
            "La charte attribue 36 unités à la thèse. La page du catalogue dit que la thèse décrit une recherche originale sous la direction d'un membre du CSE.",
            MIT,
        ),
        hardware=HardwareAbsent(
            "La charte et la page CCSE ne décrivent pas d'accès à un cluster",
            S(MIT),
        ),
        prerequisites=pres(
            MIT_SM,
            pre(
                "Graduate Writing Exam",
                "La page CCSE exige cet examen. Un échec impose le workshop 21W.794. Les matières d'admission ne sont pas listées sur la charte.",
                MIT_SM,
            ),
            pre(
                "Admission externe en pause",
                "La page CCSE dit que l'admission externe au master CSE est en pause. Un étudiant déjà inscrit dans un master de recherche au MIT peut le préparer comme diplôme secondaire.",
                MIT_SM,
            ),
        ),
    )
    harvard = Program(
        id=ProgramId("us-harvard-cse"),
        placement=InUsa("Cambridge", "Massachusetts"),
        school="Harvard University",
        program_name="Master of Science in Computational Science and Engineering",
        language=LanguageUnknown("La page des exigences ne dit pas la langue d'enseignement."),
        credits=OtherCredits("crédits", 32, S(HARVARD)),
        home=S(HARVARD),
        core=listed(
            HARVARD,
            course("AM 205 Advanced Scientific Computing: Numerical Methods", "Cours marqué obligatoire pour le SM.", HARVARD, "numerical"),
            course("AM 207 Stochastic Methods in Artificial Intelligence", "Un des trois cours dont l'étudiant en choisit deux.", HARVARD),
            course("AM 215 Mathematical Modeling for Computational Science", "Un des trois cours dont l'étudiant en choisit deux.", HARVARD),
            course("CS 2050 High Performance Computing for Science and Engineering", "Un des trois cours dont l'étudiant en choisit deux. Le titre ne nomme ni MPI, ni OpenMP, ni CUDA.", HARVARD),
        ),
        electives=CoursesAbsent(
            "La page demande deux électifs supplémentaires et ne fixe pas leur menu",
            S(HARVARD),
        ),
        project=project(
            ProjectKind.PROJECT,
            "AC 297r Capstone Project",
            "Pour le SM, l'expérience de recherche est remplie par AC 297r, Capstone Project. La page ne l'appelle pas une thèse.",
            HARVARD,
        ),
        hardware=HardwareAbsent(
            "La page des exigences ne décrit pas d'accès à un cluster",
            S(HARVARD),
        ),
        prerequisites=pres(
            HARVARD_HOME,
            pre(
                "Calcul, algèbre linéaire et un langage",
                "La page de présentation ne fixe pas de prérequis formel. Elle attend le calcul, l'algèbre linéaire, les équations différentielles, les probabilités, et un langage tel que Python ou R.",
                HARVARD_HOME,
            ),
        ),
    )
    nyu = Program(
        id=ProgramId("us-nyu-scientific-computing"),
        placement=InUsa("New York", "New York"),
        school="New York University",
        program_name="M.S. in Scientific Computing",
        language=LanguageUnknown("Le bulletin 2026-2027 ne dit pas la langue d'enseignement."),
        credits=OtherCredits("crédits", 36, S(NYU)),
        home=S(NYU),
        core=listed(
            NYU,
            course("MATH-GA 2010 Numerical Methods I", "Noyau de mathématiques, 3 crédits.", NYU, "numerical"),
            course("MATH-GA 2020 Numerical Methods II", "Noyau de mathématiques, 3 crédits.", NYU, "numerical"),
            course("CSCI-GA 1170 Fundamental Algorithms", "Noyau d'informatique, 3 crédits.", NYU),
            course("CSCI-GA 2110 Programming Languages", "Noyau d'informatique, 3 crédits.", NYU),
            course("MATH-GA 2490 Introduction to Partial Differential Equations", "Un des cours dont l'étudiant en choisit deux, pour 6 crédits.", NYU),
            course("CSCI-GA 2565 Machine Learning", "Un des cours d'informatique dont l'étudiant en choisit deux. Le titre ne décrit pas un système d'apprentissage.", NYU),
        ),
        electives=CoursesAbsent(
            "Le bulletin demande trois cours électifs et ne les nomme pas",
            S(NYU),
        ),
        project=project(
            ProjectKind.PROJECT,
            "Capstone de 3 crédits",
            "Le bulletin dit que le programme culmine dans un master's project qui intègre les cours. Il n'imprime pas de code de cours pour ce capstone.",
            NYU,
        ),
        hardware=body(
            "Postes et centre de calcul",
            "La page du département dit que les étudiants gradués ont un compte, et que NYU exploite un centre de calcul haute performance à mémoire partagée et à mémoire distribuée.",
            NYU_DEPT,
        ),
        prerequisites=pres(
            NYU_DEPT,
            pre(
                "Calcul, algèbre linéaire et programmation",
                "La page révisée à l'été 2026 demande au moins trois semestres de calcul, l'algèbre linéaire, et une programmation de niveau première année.",
                NYU_DEPT,
            ),
        ),
    )
    uchicago = Program(
        id=ProgramId("us-uchicago-hpc"),
        placement=InUsa("Chicago", "Illinois"),
        school="University of Chicago",
        program_name="Master of Science in Computer Science, spécialisation High Performance Computing",
        language=LanguageUnknown("Le PDF d'exigences et la page de spécialisation ne disent pas la langue d'enseignement."),
        credits=OtherCredits("cours exigés", 12, S(UCHI_PDF)),
        home=S(UCHI_PDF),
        core=listed(
            UCHI_PDF,
            course(
                "MPCS 51087 High Performance Computing",
                "Le PDF le rend obligatoire. La page de spécialisation dit que les étudiants optimisent des applications C ou C++ sur des clusters CPU et GPU, avec OpenMP, CUDA et MPI.",
                UCHI,
                "mpi",
                "openmp",
                "cuda",
            ),
        ),
        electives=listed(
            UCHI_PDF,
            course("GPU Programming", "MPCS 52072, un des choix HPC-2 et un choix de systèmes. Le titre dit GPU Programming.", UCHI_PDF, "cuda"),
            course("Parallel Programming", "MPCS 52060, un des choix HPC-2. Le titre ne dit pas OpenMP.", UCHI_PDF),
            course("Advanced Computer Architecture", "Choix de systèmes et choix HPC-2. Le PDF ne le rend pas obligatoire pour chaque étudiant.", UCHI_PDF, "architecture"),
            course("Distributed Systems", "Choix de systèmes du PDF.", UCHI_PDF),
            course("Networks", "Choix de systèmes du PDF.", UCHI_PDF, "networking"),
            course("Cloud Computing", "Un des électifs nommés sur le PDF, après trois cours de tronc.", UCHI_PDF, "cloud-containers"),
        ),
        project=project(
            ProjectKind.PROJECT,
            "Stage ou practicum",
            "Le PDF décrit une exigence de stage technologique, souvent l'été, et permet aussi un practicum comme douzième cours. Il ne décrit pas de thèse.",
            UCHI_PDF,
        ),
        hardware=body(
            "Cluster Midway",
            "La page de spécialisation dit que les étudiants ont un accès pratique au cluster Midway, avec GPU et jobs parallèles, et peuvent travailler avec les systèmes d'Argonne.",
            UCHI,
        ),
        prerequisites=pres(
            UCHI_PDF,
            pre(
                "Examen ou mise à niveau en programmation",
                "Le PDF demande l'examen de placement en programmation ou MPCS 50101, et l'examen de mathématiques discrètes ou MPCS 50103.",
                UCHI_PDF,
            ),
        ),
    )
    fsu = Program(
        id=ProgramId("us-fsu-computational-science"),
        placement=InUsa("Tallahassee", "Floride"),
        school="Florida State University",
        program_name="M.S. in Computational Science",
        language=LanguageUnknown(
            "Le handbook parle d'une absence d'exigence de langue étrangère, pas de la langue des cours.",
        ),
        credits=OtherCredits("heures de crédit", 30, S(FSU)),
        home=S(FSU),
        core=listed(
            FSU,
            course("ISC 5305 Scientific Programming", "Cours de tronc du groupe A, 3 credit hours, en note lettre.", FSU),
            course("ISC 5315 Applied Computational Science I", "Cours de tronc du groupe A, 4 credit hours. ISC 5318 High-Performance Computing est marqué Ph.D. only sur la même table.", FSU),
            course("ISC 5934 Introductory Seminar on Research", "Le handbook demande 2 credit hours de séminaire ISC 5934r. La table indique 1 credit hour pour l'intitulé.", FSU),
        ),
        electives=CoursesAbsent(
            "Le handbook renvoie les électifs ISC vers le site du département, qui n'a pas été ouvert pour en lire les titres",
            S(FSU),
        ),
        project=project(
            ProjectKind.EITHER,
            "Thèse ou projet",
            "L'option thèse demande 6 credit hours de thèse ISC 5975 et un manuscrit en anglais, sauf dérogation. L'option sans thèse demande un projet qui n'a pas à être original.",
            FSU,
        ),
        hardware=HardwareAbsent(
            "Le handbook de mars 2026 ne décrit pas d'accès à un cluster",
            S(FSU),
        ),
        prerequisites=pres(
            FSU,
            pre(
                "Un langage et un diplôme STEM",
                "Le handbook demande l'expérience d'au moins un langage, en pratique C, C++ ou Fortran 90, et typiquement une licence STEM. Le GRE général est exigé depuis décembre 2025.",
                FSU,
            ),
        ),
    )
    return (gatech, stanford, ut, mit, harvard, nyu, uchicago, fsu)


def _chine() -> tuple[Program, ...]:
    ustc = Program(
        id=ProgramId("cn-ustc-cs"),
        placement=InChina("Hefei"),
        school="University of Science and Technology of China",
        program_name="Master académique d'informatique, code 0812",
        language=LanguageUnknown("Le schéma 2025 ne dit pas la langue d'enseignement."),
        credits=OtherCredits("crédits", 35, S(USTC)),
        home=S(USTC),
        core=listed(
            USTC,
            course("高级计算机体系结构", "Fondement professionnel cité pour l'architecture des systèmes, avec une étoile. Au moins un cours étoilé entre dans le quota.", USTC, "architecture"),
            course("并行算法", "Fondement professionnel cité pour l'architecture des systèmes. Le titre ne nomme pas MPI.", USTC),
            course("高级计算机网络", "Fondement professionnel cité pour l'architecture des systèmes.", USTC, "networking"),
            course("高级操作系统", "Fondement professionnel cité pour l'architecture des systèmes.", USTC),
            course("并行与分布式计算", "Fondement professionnel cité pour le logiciel et la théorie.", USTC),
            course("算法设计与分析", "Cours de fondement de discipline marqué obligatoire par le symbole dièse.", USTC),
        ),
        electives=listed(
            USTC,
            course("并行程序设计", "Électif professionnel, 60 heures dont 20 de pratique, 3,5 crédits. Le titre ne nomme pas MPI.", USTC),
            course("并行编译技术", "Électif professionnel, 60 heures, 3 crédits.", USTC),
            course("智能计算系统", "Électif professionnel, 60 heures dont 40 de pratique, 4 crédits.", USTC),
            course("存储与文件系统", "Électif professionnel du schéma, stockage et système de fichiers.", USTC, "storage-io"),
            course("边缘与云计算", "Électif professionnel, 60 heures, 3 crédits.", USTC, "cloud-containers"),
        ),
        project=project(
            ProjectKind.THESIS,
            "Ouverture et mémoire",
            "L'ouverture de thèse vaut 2 crédits et reste obligatoire, en général pendant la deuxième année. Une pré-évaluation du mémoire est exigée avant la revue formelle.",
            USTC,
        ),
        hardware=HardwareAbsent(
            "Le schéma de diplôme ne nomme pas de machine. L'avis du centre de calcul n'est pas une obligation du master",
            S(USTC),
        ),
        prerequisites=PrerequisitesAbsent(
            "Le schéma décrit des objectifs de formation, pas des conditions d'admission",
            S(USTC),
        ),
    )
    pku = Program(
        id=ProgramId("cn-pekin-cs"),
        placement=InChina("Pékin"),
        school="Peking University",
        program_name="Master académique d'informatique, code 081200",
        language=LanguageUnknown("Le catalogue 2026 et la brochure 2026 ne disent pas la langue d'enseignement."),
        credits=CreditsAbsent(
            "Le catalogue 2026 ne donne pas de total de crédits pour cette majeure",
            S(PKU),
        ),
        home=S(PKU),
        core=CoursesAbsent("Le catalogue 2026 ne liste pas de cours", S(PKU)),
        electives=CoursesAbsent("Le catalogue 2026 ne liste pas d'électifs", S(PKU)),
        project=ProjectAbsent("Le catalogue 2026 ne décrit pas de mémoire", S(PKU)),
        hardware=HardwareAbsent("Le catalogue 2026 ne nomme pas de machine", S(PKU)),
        prerequisites=pres(
            PKU,
            pre(
                "Épreuves 101, 201, 301 et 408",
                "Le catalogue indique ces quatre épreuves, puis un examen sur machine et un entretien de réexamen.",
                PKU,
            ),
            pre(
                "Licence reconnue",
                "La brochure vise les diplômés d'une licence reconnue par l'État, et les étudiants en fin de licence.",
                PKU_BROCHURE,
            ),
        ),
    )
    tsinghua = Program(
        id=ProgramId("cn-tsinghua-advanced-computing"),
        placement=InChina("Pékin"),
        school="Tsinghua University",
        program_name="Master's in Advanced Computing",
        language=Language.EN,
        credits=OtherCredits("crédits", 26, S(TSING_CUR)),
        home=S(TSING),
        core=listed(
            TSING_CUR,
            course("Chinese Language", "Sujet obligatoire encore visible quand l'onglet master masque les cours de doctorat.", TSING_CUR),
            course("Chinese Culture and Society", "Sujet obligatoire du même bloc.", TSING_CUR),
            course("Combinatorics and Algorithms Design", "Sujet fondamental académique, hors item de doctorat.", TSING_CUR),
        ),
        electives=listed(
            TSING_CUR,
            course(
                "Distributed Systems",
                "Électif académique. La page le présente comme une introduction et nomme Google file system, MapReduce et Amazon Dynamo.",
                TSING_CUR,
                "storage-io",
            ),
            course("Distributed Database System", "Électif académique, hors item de doctorat. La page n'imprime pas de crédit par cours.", TSING_CUR),
            course(
                "Introduction to Big Data Systems",
                "Électif académique. La page parle de clustering and distributed programming.",
                TSING_CUR,
            ),
        ),
        project=project(
            ProjectKind.THESIS,
            "Literature Summarizing and Presentation of Thesis",
            "Sujet obligatoire. Les étudiants font une revue, présentent un plan de recherche et discutent le sujet avec leur encadrant.",
            TSING_CUR,
        ),
        hardware=HardwareAbsent(
            "Les pages du programme ne spécifient pas de cluster pour le diplôme",
            S(TSING),
        ),
        prerequisites=pres(
            TSING_APP,
            pre(
                "Licence et nationalité étrangère",
                "La page, mise à jour le 27 septembre 2026, demande un bachelor ou un équivalent, et la nationalité étrangère.",
                TSING_APP,
            ),
            pre(
                "Anglais TOEFL ou IELTS",
                "Pour les non natifs, la page demande TOEFL iBT 85 ou 4,5 selon la date du test, ou IELTS 6,5.",
                TSING_APP,
            ),
        ),
    )
    buaa = Program(
        id=ProgramId("cn-beihang-cs"),
        placement=InChina("Pékin"),
        school="Beihang University",
        program_name="Master Computer Science and Technology, étudiants internationaux",
        language=Language.EN,
        credits=CreditsAbsent(
            "La liste des majeures 2026 n'imprime pas de total de crédits",
            S(BUAA),
        ),
        home=S(BUAA),
        core=CoursesAbsent(
            "La liste 2026 donne des domaines de recherche, pas des cours obligatoires",
            S(BUAA),
        ),
        electives=CoursesAbsent(
            "Le catalogue de cours en anglais est marqué seulement pour référence, pas comme exigence du diplôme",
            S(BUAA_ANN),
        ),
        project=ProjectAbsent(
            "La liste 2026 et l'annonce ne décrivent pas de règle de mémoire",
            S(BUAA),
        ),
        hardware=HardwareAbsent(
            "Ni la liste 2026 ni l'annonce ne nomment de cluster",
            S(BUAA),
        ),
        prerequisites=pres(
            BUAA_ANN,
            pre(
                "Licence avant 35 ans et anglais",
                "L'annonce demande une nationalité autre que chinoise, une licence, moins de 35 ans, et IELTS 6,0, TOEFL 90 ou Duolingo 105.",
                BUAA_ANN,
            ),
            pre(
                "Lettre d'un encadrant",
                "L'annonce demande en principe une lettre d'acceptation d'un encadrant de Beihang.",
                BUAA_ANN,
            ),
        ),
    )
    sysu = Program(
        id=ProgramId("cn-sysu-cs"),
        placement=InChina("Guangzhou"),
        school="Sun Yat-sen University",
        program_name="Master d'informatique, code 081200",
        language=LanguageUnknown("La foire aux questions et le tableau des encadrants ne disent pas la langue d'enseignement."),
        credits=CreditsAbsent("Les deux pages lues ne donnent pas de total de crédits", S(SYSU)),
        home=S(SYSU),
        core=CoursesAbsent("La foire aux questions ne liste pas de cours", S(SYSU)),
        electives=CoursesAbsent("La foire aux questions ne liste pas d'électifs", S(SYSU)),
        project=ProjectAbsent("La foire aux questions ne décrit pas de mémoire", S(SYSU)),
        hardware=HardwareAbsent(
            "Ni la foire aux questions ni le tableau des encadrants ne décrivent de machine",
            S(SYSU),
        ),
        prerequisites=PrerequisitesAbsent(
            "La page renvoie les conditions d'inscription ailleurs et ne les répète pas",
            S(SYSU),
        ),
    )
    zju = Program(
        id=ProgramId("cn-zhejiang-cs"),
        placement=InChina("Hangzhou"),
        school="Zhejiang University",
        program_name="Master académique d'informatique, code 081200",
        language=LanguageUnknown("Ni l'avis du collège ni la page du laboratoire ne disent la langue d'enseignement."),
        credits=CreditsAbsent("Les deux pages lues ne donnent pas de total de crédits", S(ZJU)),
        home=S(ZJU),
        core=CoursesAbsent("Les deux pages lues ne listent pas de cours", S(ZJU)),
        electives=CoursesAbsent("Les deux pages lues ne listent pas d'électifs", S(ZJU)),
        project=ProjectAbsent("Les deux pages lues ne décrivent pas de mémoire", S(ZJU)),
        hardware=HardwareAbsent("Aucune des deux pages ne nomme de machine", S(ZJU)),
        prerequisites=pres(
            ZJU,
            pre(
                "Admission sur titre",
                "L'avis demande la citoyenneté chinoise et une qualification de recommandation. Il ne donne pas les matières d'un concours national.",
                ZJU,
            ),
        ),
    )
    return (ustc, pku, tsinghua, buaa, sysu, zju)


def _monde() -> tuple[Program, ...]:
    edinburgh = Program(
        id=ProgramId("uk-edinburgh-hpc"),
        placement=Elsewhere("Royaume-Uni", "Édimbourg"),
        school="The University of Edinburgh",
        program_name="High Performance Computing MSc",
        language=LanguageUnknown("Le degree finder et la page EPCC ne disent pas la langue d'enseignement."),
        credits=OtherCredits("crédits", 180, S(EDIN_EPCC)),
        home=S(EDIN),
        core=listed(
            EDIN_DPT,
            course("Message-Passing Programming", "Cours obligatoire EPCC11002, 10 crédits, au tableau 2026/27.", EDIN_DPT, "mpi"),
            course("Threaded Programming", "Cours obligatoire EPCC11003, 10 crédits. Le titre ne dit pas OpenMP.", EDIN_DPT),
            course("Practical Software Development", "Cours obligatoire EPCC11001, 20 crédits.", EDIN_DPT),
            course("Project Preparation", "Cours obligatoire EPCC11008, 10 crédits.", EDIN_DPT),
            course("HPC Architectures", "Cours obligatoire EPCC11004, 10 crédits.", EDIN_DPT, "architecture"),
        ),
        electives=listed(
            EDIN_DPT,
            course("Numerical Algorithms for High Performance Computing", "Liste optionnelle EPCC du groupe A, 10 crédits. Le groupe demande exactement 60 crédits.", EDIN_DPT, "numerical"),
            course("Design and Analysis of Parallel Algorithms", "Liste optionnelle EPCC, 10 crédits.", EDIN_DPT),
            course("Performance Programming", "Liste optionnelle EPCC, 10 crédits.", EDIN_DPT, "performance"),
            course("Parallel Design Patterns", "Liste optionnelle EPCC, 10 crédits.", EDIN_DPT),
            course("Advanced Message-Passing Programming", "Liste optionnelle EPCC, 10 crédits.", EDIN_DPT, "mpi"),
            course("Programming Languages for HPC", "Liste optionnelle EPCC, 10 crédits.", EDIN_DPT),
            course("Accelerated Systems: Principles and Practice", "Liste optionnelle EPCC, 10 crédits. Le titre ne dit pas CUDA.", EDIN_DPT),
            course("Machine Learning at Scale", "Jusqu'à 20 crédits peuvent venir de cette liste, à côté du HPC. Le titre ne décrit pas un système d'apprentissage.", EDIN_DPT),
        ),
        project=project(
            ProjectKind.THESIS,
            "Dissertation High Performance Computing",
            "Après les cours, un projet individuel de trois mois mène à la dissertation. Le tableau la liste à 60 crédits, code EPCC11015.",
            EDIN_DPT,
        ),
        hardware=HardwareAbsent(
            "Le degree finder promet l'accès à des plateformes HPC et à des moyens de calcul propres, sans nommer de machine",
            S(EDIN),
        ),
        prerequisites=pres(
            EDIN,
            pre(
                "Licence scientifique et un langage",
                "Pour 2027-28, un honours 2:1 ou équivalent en informatique, physique, mathématiques, ingénierie ou géosciences, et une pratique de C, C++, Python ou Fortran.",
                EDIN,
            ),
            pre(
                "Anglais IELTS 7,0",
                "Le degree finder cite IELTS Academic 7,0 avec au moins 6,0 par composante, parmi d'autres tests.",
                EDIN,
            ),
        ),
    )
    dresden = Program(
        id=ProgramId("de-dresden-dse"),
        placement=Elsewhere("Allemagne", "Dresde"),
        school="Technische Universität Dresden",
        program_name="Master of Science in Computer Science, piste Distributed Systems Engineering",
        language=Language.EN,
        credits=OtherCredits("Leistungspunkte", 120, S(TUD_PLAN)),
        home=S(TUD),
        core=listed(
            TUD_PLAN,
            course("Distributed Systems", "Pflichtbereich de la piste, plan d'hiver 2026/2027, 6 LP.", TUD_PLAN),
            course("Systems Engineering", "Pflichtbereich de la piste, 6 LP.", TUD_PLAN),
            course("Scalable Data Management", "Pflichtbereich de la piste, 6 LP.", TUD_PLAN),
            course("Design Patterns and Frameworks", "Pflichtbereich de la piste, 6 LP.", TUD_PLAN),
            course("Network and Distributed Systems Security", "Pflichtbereich de la piste, 6 LP.", TUD_PLAN, "networking"),
            course("Advanced Operating Systems", "Pflichtbereich de la piste, 6 LP.", TUD_PLAN),
            course("Advanced Computer Networks", "Module du Wahlpflichtbereich, nommé sur le plan. La page anglaise reprend le nom sans crédit.", TUD_PLAN, "networking"),
        ),
        electives=listed(
            TUD_PLAN,
            course("Operating-System Construction", "Module du choix de 36 Leistungspunkte.", TUD_PLAN),
            course("Foundations of Concurrent and Distributed Systems", "Module du même choix.", TUD_PLAN),
            course("Concurrent and Distributed Systems Lab", "Module du même choix.", TUD_PLAN),
            course("Linux Cluster in Theorie und Praxis", "Module électif, 6 LP. Le plan ne dit pas qu'un compte est fourni.", TUD_PLAN),
            course("Microkernel Construction", "Module du même choix.", TUD_PLAN),
            course("Decentralized Systems", "Module du même choix.", TUD_PLAN),
        ),
        project=project(
            ProjectKind.THESIS,
            "Abschlussarbeit et colloque",
            "Le quatrième semestre est réservé au mémoire et au colloque. Le plan imprime l'Abschlussarbeit sur 29 LP et le colloque sur 1 LP, à côté du total 120.",
            TUD_PLAN,
        ),
        hardware=HardwareAbsent(
            "Le plan nomme un module Linux Cluster et ne dit pas qu'un compte est ouvert",
            S(TUD_PLAN),
        ),
        prerequisites=pres(
            TUD_ADM,
            pre(
                "Licence d'informatique et 90 ECTS ciblés",
                "La page d'admission demande un premier diplôme en informatique et 90 ECTS sans recouvrement, dont des volumes minimaux en systèmes, théorie, mathématiques, architecture et programmation.",
                TUD_ADM,
            ),
            pre(
                "Anglais C1",
                "La page demande le niveau C1, avec des exemples TOEFL iBT et IELTS.",
                TUD_ADM,
            ),
        ),
    )
    eth = Program(
        id=ProgramId("ch-eth-cse"),
        placement=Elsewhere("Suisse", "Zurich"),
        school="ETH Zurich",
        program_name="Master of Science ETH in Computational Science and Engineering",
        language=Language.EN,
        credits=Ects(120, S(ETH_M)),
        home=S(ETH),
        core=listed(
            ETH_GL,
            course("Advanced Numerical Methods for CSE", "Cours de tronc d'automne dans le guide, 10 crédits. Deux cours de tronc sont à choisir, pour au moins 12 crédits.", ETH_GL, "numerical"),
            course("Advanced Machine Learning", "Cours de tronc d'automne, 10 crédits. Il est exclusif avec Probabilistic Artificial Intelligence.", ETH_GL),
            course("Computational Statistics", "Cours de tronc de printemps, 8 crédits.", ETH_GL),
            course("Advanced Systems Lab", "Cours de tronc de printemps, 8 crédits.", ETH_GL),
            course("Optimization for Data Science", "Cours de tronc de printemps, 10 crédits.", ETH_GL),
            course("AI in the Sciences and Engineering", "Le guide le liste à 6 crédits en automne et à 8 au printemps, et renvoie au catalogue si la table est périmée.", ETH_GL),
        ),
        electives=CoursesAbsent(
            "Le guide demande des électifs et nomme des domaines, pas une liste fermée de titres",
            S(ETH_GL),
        ),
        project=project(
            ProjectKind.THESIS,
            "Master thesis",
            "Le guide attribue 30 ECTS à un mémoire accepté, pour un travail à plein temps d'environ 26 semaines, et au plus 28 semaines.",
            ETH_GL,
        ),
        hardware=HardwareAbsent(
            "La page du diplôme, le site du programme et le guide ne nomment ni cluster ni compte",
            S(ETH),
        ),
        prerequisites=pres(
            ETH_APP,
            pre(
                "Bachelor de 180 ECTS et profil",
                "L'annexe demande un bachelor d'université d'au moins 180 ECTS, et un profil de discipline de 100 ECTS.",
                ETH_APP,
            ),
            pre(
                "High Performance Computing for Science and Engineering",
                "L'annexe place ce titre dans les connaissances de base, avec Numerical Methods for Partial Differential Equations et Software Engineering.",
                ETH_APP,
            ),
            pre(
                "Anglais C1",
                "L'annexe demande une preuve d'anglais de niveau C1. La langue d'enseignement y est l'anglais.",
                ETH_APP,
            ),
        ),
    )
    vu = Program(
        id=ProgramId("nl-amsterdam-csi"),
        placement=Elsewhere("Pays-Bas", "Amsterdam"),
        school="Vrije Universiteit Amsterdam et University of Amsterdam",
        program_name="Master's Computer Science, spécialisation Computer Systems and Infrastructure",
        language=Language.EN,
        credits=Ects(120, S(UVA)),
        home=S(VU),
        core=listed(
            VU,
            course("Programming Large-scale Parallel Systems", "Cours propre à la spécialisation. La page VU n'imprime pas d'ECTS par cours.", VU),
            course("Distributed Systems", "Cours propre à la spécialisation.", VU),
            course("Parallel Programming Practical", "Cours propre à la spécialisation. Le titre ne dit pas OpenMP.", VU),
            course("Reliable Computing", "Cours propre à la spécialisation.", VU),
            course("Multi-core Processor Systems", "Cours propre à la spécialisation. Le titre ne dit pas architecture.", VU),
            course("Accelerator-Centric Computing Ecosystem", "Cours propre à la spécialisation. Le titre ne dit pas CUDA.", VU),
            course("Energy-efficient Edge Computing", "Cours propre à la spécialisation.", VU),
        ),
        electives=CoursesAbsent(
            "La page annonce cinq cours au choix contraint et cinq électifs sans en donner les titres",
            S(VU),
        ),
        project=project(
            ProjectKind.THESIS,
            "Mémoire de deuxième année",
            "La page VU dit que le mémoire s'écrit en deuxième année. La page UvA parle d'un projet de recherche de 30 ECTS, en général dans un groupe de l'UvA ou de la VU.",
            UVA,
        ),
        hardware=HardwareAbsent(
            "Ni la page VU ni la page UvA ne nomment de cluster ou de compte",
            S(VU),
        ),
        prerequisites=pres(
            VU_ADM,
            pre(
                "Licence et 180 ECTS",
                "La page d'admission demande un bachelor d'université de recherche, au moins trois ans et 180 ECTS, dont une part en informatique.",
                VU_ADM,
            ),
        ),
    )
    kth = Program(
        id=ProgramId("se-kth-hpc"),
        placement=Elsewhere("Suède", "Stockholm"),
        school="KTH Royal Institute of Technology",
        program_name="MSc Computer Science, sous-piste High Performance Computing",
        language=Language.EN,
        credits=Ects(120, S(KTH)),
        home=S(KTH),
        core=listed(
            KTH_C,
            course("Introduction to the Philosophy of Science and Research Methodology", "Cours obligatoire du programme, DA2210, 6 crédits, rentrée 2027.", KTH_C),
            course("Program Integrating Course in Computer Science", "Cours obligatoire DD2300, 2 crédits.", KTH_C),
            course("Artificial Intelligence", "Cours obligatoire DD2380, 6 crédits.", KTH_C),
            course("Computer Security", "Cours obligatoire DD2395, 6 crédits.", KTH_C),
            course("Advanced Algorithms", "Cours obligatoire DD2440, 6 crédits.", KTH_C),
            course("Protocols and Principles of the Internet", "Cours obligatoire IK2218, 6 crédits. Le titre nomme l'Internet, pas un cours de réseau.", KTH_C),
            course("Introduction to High Performance Computing", "DD2358, obligatoire dans la sous-piste High Performance Computing.", KTH_C),
            course("Methods in High Performance Computing", "DD2356, obligatoire dans la même sous-piste.", KTH_C),
            course("Applied GPU Programming", "DD2360, obligatoire dans la même sous-piste.", KTH_C, "cuda"),
        ),
        electives=listed(
            KTH_C,
            course("Project Course in High-Performance Computing", "DD2375, au moins un cours de cette liste est à prendre.", KTH_C),
            course("Parallel and Distributed Computing", "DD2443, dans la même liste.", KTH_C),
            course("Networked Systems for Machine Learning", "IK2221, dans la même liste.", KTH_C, "networking", "ml-systems"),
            course("Scalable Machine Learning and Deep Learning", "ID2223, dans la même liste. Le titre ne dit pas système.", KTH_C),
            course("Computational Methods for Electromagnetics", "DD2370, dans la même liste. Le titre ne dit pas méthodes numériques.", KTH_C),
        ),
        project=project(
            ProjectKind.THESIS,
            "Projet de master",
            "Le programme se termine par un projet de master en milieu académique ou industriel. La page des cours réserve le dernier terme à ce projet, d'environ 30 ECTS, sans code ni crédit exact.",
            KTH_C,
        ),
        hardware=body(
            "PDC Center for High Performance Computing",
            "La page présente le PDC comme fournisseur de systèmes HPC, de stockage court et long, et d'aide d'experts. Elle ne dit pas que chaque étudiant reçoit un compte.",
            KTH,
            "storage-io",
        ),
        prerequisites=pres(
            KTH_E,
            pre(
                "Licence de 180 ECTS, mathématiques et informatique",
                "La page demande une licence de 180 ECTS, 28,5 ECTS de mathématiques sur quatre sujets, et 22,5 ECTS d'informatique sur trois sujets.",
                KTH_E,
            ),
            pre(
                "Anglais",
                "La page demande un anglais équivalent au cours suédois English 6, et donne en exemple IELTS 6,5 ou TOEFL 4,5.",
                KTH_E,
            ),
        ),
    )
    euro = Program(
        id=ProgramId("lu-eumaster4hpc"),
        placement=Elsewhere("Luxembourg", "Luxembourg"),
        school="EUMaster4HPC",
        program_name="European Master Degree in HPC",
        language=LanguageUnknown(
            "Le site exige l'anglais à l'admission et ne dit pas que chaque module est enseigné en anglais.",
        ),
        credits=Ects(120, S(EURO)),
        home=S(EURO),
        core=listed(
            EURO_C,
            course("Mathematics and Statistics", "Cours fondamental de première année sur la page de curriculum.", EURO_C),
            course("Software Engineering", "Cours fondamental de première année.", EURO_C),
            course("Parallel Programming", "Cours fondamental de première année. Le titre ne nomme ni MPI ni OpenMP.", EURO_C),
            course("Computer Architecture", "Cours fondamental de première année.", EURO_C, "architecture"),
            course("Transversal Skills", "Cours fondamental de première année. La page y range l'éthique, la méthode scientifique et la propriété intellectuelle.", EURO_C),
        ),
        electives=CoursesAbsent(
            "La page nomme quatre spécialisations de deuxième année, pas une liste de cours au choix",
            S(EURO_C),
        ),
        project=project(
            ProjectKind.EITHER,
            "Mastership",
            "Le site combine les cours avec un Mastership, stage ou mémoire de master. Le crédit du mémoire n'est pas imprimé sur les pages lues.",
            EURO_C,
        ),
        hardware=HardwareAbsent(
            "Le site cite des centres de supercalcul partenaires et des stages, sans login sur une machine nommée",
            S(EURO_H),
        ),
        prerequisites=pres(
            EURO_H,
            pre(
                "Licence STEM et anglais B2",
                "Le site demande au moins un bachelor en STEM et un anglais B2, attesté par IELTS ou TOEFL de moins de deux ans.",
                EURO_H,
            ),
        ),
    )
    iisc = Program(
        id=ProgramId("in-iisc-cds"),
        placement=Elsewhere("Inde", "Bengaluru"),
        school="Indian Institute of Science",
        program_name="M.Tech. in Computational and Data Science",
        language=LanguageUnknown("La page d'admission 2026 et la page de curriculum ne disent pas la langue d'enseignement."),
        credits=OtherCredits("crédits", 64, S(IISC_C)),
        home=S(IISC),
        core=listed(
            IISC_C,
            course("DS 215 Introduction to Data Science", "Hard core, tous obligatoires, pour 14 crédits au total du bloc.", IISC_C),
            course("DS 221 Introduction to Scalable Systems", "Hard core obligatoire.", IISC_C),
            course("DS 284 Numerical Linear Algebra", "Hard core obligatoire.", IISC_C, "numerical"),
            course("DS 288 Numerical Methods", "Hard core obligatoire.", IISC_C, "numerical"),
            course("DS 200 Research Methods", "Hard core, cours de compétences, à prendre en deuxième année au terme d'août.", IISC_C),
        ),
        electives=listed(
            IISC_C,
            course("DS 295 Parallel Programming", "Soft core. Le bloc soft core demande au moins 10 crédits et trois cours. Le titre ne dit pas OpenMP.", IISC_C),
            course("DS 256 Scalable Systems for Data Science", "Soft core.", IISC_C),
            course("DS 289 Numerical Solution of Differential Equations", "Soft core.", IISC_C, "numerical"),
            course("DS 290 Modelling and Simulation", "Soft core.", IISC_C),
            course("DS 244 Hardware-aware Scientific Computing", "Électif nommé sur la page.", IISC_C),
            course("DS 393 High-performance Computing for Quantum Modeling of Materials", "Électif nommé sur la page.", IISC_C),
        ),
        project=project(
            ProjectKind.THESIS,
            "DS 299 Dissertation Project",
            "La page de curriculum indique 28 crédits sur un an. La page d'admission parle d'un projet de dissertation d'un an.",
            IISC_C,
        ),
        hardware=body(
            "SahasraT et cluster turing",
            "La page des moyens cite le Cray XC40 SahasraT et le cluster d'enseignement turing, 24 nœuds, avec MPI et PBS, plus un nœud GPU NVIDIA Tesla K40M.",
            IISC_H,
            "mpi",
        ),
        prerequisites=pres(
            IISC,
            pre(
                "BE, B Tech ou M Sc avec GATE",
                "Pour le terme d'août 2026, la page demande ce diplôme et un GATE dans une liste de papiers, plus un écrit en présentiel.",
                IISC,
            ),
            pre(
                "Écrit de mathématiques et de programmation",
                "Le syllabus de l'écrit couvre l'algèbre linéaire, les probabilités, la combinatoire, le calcul, les structures de données et une programmation de base.",
                IISC,
            ),
        ),
    )
    aizu = Program(
        id=ProgramId("jp-aizu-cis"),
        placement=Elsewhere("Japon", "Aizu-Wakamatsu"),
        school="University of Aizu",
        program_name="Master's Program, Graduate Department of Computer and Information Systems",
        language=Language.EN,
        credits=OtherCredits("crédits académiques", 30, S(AIZU_REG)),
        home=S(AIZU),
        core=CoursesAbsent(
            "Le règlement ne nomme pas de cours HPC obligatoire. Il demande des cours réguliers, des séminaires et un cours de recherche",
            S(AIZU_REG),
        ),
        electives=listed(
            AIZU_SYL,
            course(
                "CSA20 High Performance Computing",
                "Syllabus 2026, 2 crédits. Le texte couvre les architectures parallèles, la programmation MPI et la programmation OpenMP. Il n'est pas marqué obligatoire pour tous.",
                AIZU_SYL,
                "architecture",
                "mpi",
                "openmp",
            ),
            course(
                "CSA24 Advanced Distributed Networking",
                "Syllabus 2026, 2 crédits, aspects algorithmiques des systèmes distribués. Non marqué obligatoire pour tous.",
                AIZU_SYL,
                "networking",
            ),
        ),
        project=project(
            ProjectKind.THESIS,
            "Thesis Research",
            "La page du master exige le cours Thesis Research et la rédaction du mémoire. Le règlement attribue 6 crédits académiques aux cours de recherche.",
            AIZU_REG,
        ),
        hardware=HardwareAbsent(
            "La page du master, le règlement et le syllabus CSA20 ne nomment ni cluster ni compte",
            S(AIZU),
        ),
        prerequisites=pres(
            AIZU_ADM,
            pre(
                "Licence et accord d'un encadrant",
                "Le guide AY2027 demande une licence ou seize années d'études, et l'accord du membre qui suivra le projet.",
                AIZU_ADM,
            ),
            pre(
                "Score d'anglais",
                "Le guide demande TOEIC, TOEFL, IELTS ou Duolingo de moins de deux ans, avec un plancher TOEIC 500, sauf exemption.",
                AIZU_ADM,
            ),
        ),
    )
    polimi = Program(
        id=ProgramId("it-polimi-hpc"),
        placement=Elsewhere("Italie", "Milan"),
        school="Politecnico di Milano",
        program_name="Laurea Magistrale in High Performance Computing Engineering",
        language=Language.EN,
        credits=OtherCredits("CFU", 120, S(POLIMI_REG)),
        home=S(POLIMI),
        core=listed(
            POLIMI_REG,
            course("Parallel Computing", "Plan préapprouvé HPC, première année, 5,0 CFU.", POLIMI_REG),
            course("Advanced Methods for Scientific Computing", "Première année, 5,0 CFU. Le titre ne dit pas méthodes numériques.", POLIMI_REG),
            course("Numerical Linear Algebra", "Première année, 5,0 CFU.", POLIMI_REG, "numerical"),
            course("Numerical Methods for Partial Differential Equations", "Première année, 5,0 CFU.", POLIMI_REG, "numerical"),
            course("Software Engineering for HPC", "Première année, 5,0 CFU.", POLIMI_REG),
            course("Advanced Computer Architectures", "Première année, 5,0 CFU.", POLIMI_REG, "architecture"),
            course("Computing Infrastructures", "Première année, 5,0 CFU.", POLIMI_REG),
            course("Artificial Neural Networks and Deep Learning", "Paire obligatoire de deuxième année, 5,0 CFU.", POLIMI_REG),
            course("Systems and Methods for Big and Unstructured Data", "Paire obligatoire de deuxième année, 5,0 CFU.", POLIMI_REG),
        ),
        electives=listed(
            POLIMI_REG,
            course("Distributed Systems", "Titre du groupe ICT, 5,0 CFU. Le groupe ICT vaut 10 CFU au choix.", POLIMI_REG),
            course("Performance Evaluation and Applications", "Titre du groupe ICT, 5,0 CFU.", POLIMI_REG, "performance"),
            course("Code Transformation and Optimization", "Titre du groupe ICT, 5,0 CFU.", POLIMI_REG),
            course("High Performance Scientific Computing in Aerospace", "Titre du groupe multidisciplinaire, 10,0 CFU.", POLIMI_REG),
        ),
        project=project(
            ProjectKind.THESIS,
            "Thesis and final exam",
            "Le règlement attribue 20,0 CFU à la thèse et à l'examen final, dont un crédit pour l'anglais. La thèse peut être en italien ou en anglais, avec un résumé en anglais.",
            POLIMI_REG,
        ),
        hardware=HardwareAbsent(
            "Le règlement ouvre les installations du Politecnico et cite des centres de supercalcul partenaires, sans compte nommé",
            S(POLIMI_REG),
        ),
        prerequisites=pres(
            POLIMI,
            pre(
                "Licence et secteurs ECTS",
                "La page demande une licence d'au moins 180 ECTS, avec des minima dans les secteurs informatiques, mathématiques et physiques, ou une admission automatique pour certains cursus de Milan avec une moyenne d'au moins 24 sur 30.",
                POLIMI,
            ),
        ),
    )
    return (edinburgh, dresden, eth, vu, kth, euro, iisc, aizu, polimi)


META = Meta(
    topics=(
        Topic(TopicId("mpi"), "MPI"),
        Topic(TopicId("openmp"), "OpenMP"),
        Topic(TopicId("cuda"), "CUDA"),
        Topic(TopicId("architecture"), "Architecture"),
        Topic(TopicId("numerical"), "Méthodes numériques"),
        Topic(TopicId("schedulers"), "Ordonnanceurs"),
        Topic(TopicId("storage-io"), "Stockage et entrées-sorties"),
        Topic(TopicId("networking"), "Réseau"),
        Topic(TopicId("cloud-containers"), "Cloud et conteneurs"),
        Topic(TopicId("ml-systems"), "Systèmes pour l'apprentissage"),
        Topic(TopicId("performance"), "Ingénierie de performance"),
    ),
    gaps=(
        Gap(
            GapId("mpi"),
            "MPI",
            tops("mpi"),
            "Le registre ne compte MPI que lorsque la page le nomme. L'entraînement multi-nœud part de là.",
        ),
        Gap(
            GapId("openmp"),
            "OpenMP",
            tops("openmp"),
            "OpenMP n'est compté que lorsque la page le nomme. Le calcul à mémoire partagée en dépend.",
        ),
        Gap(
            GapId("cuda-programming"),
            "Programmation CUDA",
            tops("cuda"),
            "CUDA n'est compté que lorsque la page le nomme. Faire tourner un modèle ne remplace pas ce modèle de programmation.",
        ),
        Gap(
            GapId("slurm"),
            "Slurm",
            tops("schedulers"),
            "Aucun programme du corpus ne nomme un ordonnanceur de cluster.",
        ),
        Gap(
            GapId("infiniband"),
            "InfiniBand et RoCE",
            tops("networking"),
            "Les pages ne décrivent pas InfiniBand ni RoCE, le réseau d'une flotte de GPU.",
        ),
        Gap(
            GapId("nccl"),
            "NCCL",
            tops("networking"),
            "Aucune citation ne nomme NCCL, la couche de communication collective entre GPU.",
        ),
        Gap(
            GapId("multi-cloud-gpu"),
            "Flottes GPU multi-fournisseurs",
            tops("cuda", "cloud-containers"),
            "Les pages décrivent un cluster de campus ou un cours sur GPU. Elles ne décrivent pas une flotte d'entraînement répartie entre plusieurs fournisseurs.",
        ),
        Gap(
            GapId("ray"),
            "Ray",
            tops("ml-systems"),
            "Aucune citation retenue ne nomme Ray comme environnement d'entraînement distribué.",
        ),
        Gap(
            GapId("skypilot"),
            "SkyPilot",
            tops("cloud-containers"),
            "Aucune citation retenue ne nomme SkyPilot pour envoyer un job GPU d'un cloud à un autre.",
        ),
        Gap(
            GapId("cost"),
            "Coût",
            (),
            "Les maquettes parlent de crédits pédagogiques et de stages. Elles ne traitent pas le coût d'une flotte d'entraînement.",
        ),
        Gap(
            GapId("observability"),
            "Observabilité",
            (),
            "Les pages ne décrivent pas les métriques d'une flotte d'entraînement. Le suivi d'un cours ne couvre pas ce besoin.",
        ),
    ),
    self_study=(
        StudyStep(
            order=1,
            gap_ids=(GapId("mpi"),),
            body=StudyResource(
                id=StudyId("llnl-mpi"),
                title="MPI Tutorial",
                kind=StudyKind.COURSE,
                source=S("https://hpc-tutorials.llnl.gov/mpi/"),
                why_for_profile_fr="Kim n'a pas écrit de programme MPI. Ce tutoriel du Lawrence Livermore National Laboratory est gratuit et part de la première communication entre processus.",
            ),
        ),
        StudyStep(
            order=2,
            gap_ids=(GapId("openmp"),),
            body=StudyResource(
                id=StudyId("llnl-openmp"),
                title="OpenMP Tutorial",
                kind=StudyKind.COURSE,
                source=S("https://hpc-tutorials.llnl.gov/openmp/"),
                why_for_profile_fr="Kim n'a pas OpenMP. Le même organisme publie le tutoriel gratuit pour le parallélisme à mémoire partagée, avant les GPU.",
            ),
        ),
        StudyStep(
            order=3,
            gap_ids=(GapId("cuda-programming"),),
            body=StudyResource(
                id=StudyId("cuda-guide"),
                title="CUDA Programming Guide",
                kind=StudyKind.COURSE,
                source=S("https://docs.nvidia.com/cuda/cuda-programming-guide/index.html"),
                why_for_profile_fr="Kim fait tourner des modèles sur GPU. Il n'a pas le modèle de programmation CUDA. Le guide NVIDIA est la référence gratuite.",
            ),
        ),
        StudyStep(
            order=4,
            gap_ids=(GapId("slurm"),),
            body=StudyResource(
                id=StudyId("slurm-overview"),
                title="Slurm overview",
                kind=StudyKind.COURSE,
                source=S("https://slurm.schedmd.com/overview.html"),
                why_for_profile_fr="Kim ordonnance des jobs avec Kubernetes. Slurm est l'ordonnanceur des clusters d'entraînement que le rôle attend.",
            ),
        ),
        StudyStep(
            order=5,
            gap_ids=(GapId("infiniband"),),
            body=StudyResource(
                id=StudyId("rdma-guide"),
                title="RDMA Aware Networks Programming User Manual",
                kind=StudyKind.COURSE,
                source=S("https://networking-docs.nvidia.com/rdmaawareprogramming"),
                why_for_profile_fr="Kim n'a pas InfiniBand. Ce manuel NVIDIA décrit la programmation RDMA, le réseau derrière une flotte de GPU.",
            ),
        ),
        StudyStep(
            order=6,
            gap_ids=(GapId("nccl"),),
            body=StudyResource(
                id=StudyId("nccl-overview"),
                title="NCCL overview",
                kind=StudyKind.COURSE,
                source=S("https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html"),
                why_for_profile_fr="Kim n'a pas NCCL. Le guide NVIDIA décrit la communication collective entre GPU, après CUDA et avant un runtime comme Ray.",
            ),
        ),
        StudyStep(
            order=7,
            gap_ids=(GapId("multi-cloud-gpu"),),
            body=StudyResource(
                id=StudyId("gpu-operator"),
                title="About the NVIDIA GPU Operator",
                kind=StudyKind.COURSE,
                source=S("https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/overview.html"),
                why_for_profile_fr="Kim exploite déjà Kubernetes et l'inférence GPU sur une machine. Cette documentation officielle décrit l'installation d'une flotte de GPU sur un cluster, avant de la répartir entre fournisseurs.",
            ),
        ),
        StudyStep(
            order=8,
            gap_ids=(GapId("ray"),),
            body=StudyResource(
                id=StudyId("ray-docs"),
                title="Welcome to Ray",
                kind=StudyKind.COURSE,
                source=S("https://docs.ray.io/en/latest/index.html"),
                why_for_profile_fr="Kim n'a pas Ray. La documentation officielle couvre le runtime distribué qui lui manque pour l'entraînement, à côté de Kubernetes qu'il exploite déjà.",
            ),
        ),
        StudyStep(
            order=9,
            gap_ids=(GapId("skypilot"),),
            body=StudyResource(
                id=StudyId("skypilot-docs"),
                title="SkyPilot documentation",
                kind=StudyKind.COURSE,
                source=S("https://docs.skypilot.ai/en/latest/"),
                why_for_profile_fr="Kim déploie déjà l'inférence sur plusieurs clouds, sans SkyPilot. La documentation officielle montre comment lancer des jobs GPU d'un fournisseur à l'autre.",
            ),
        ),
        StudyStep(
            order=10,
            gap_ids=(GapId("cost"),),
            body=StudyResource(
                id=StudyId("opencost-docs"),
                title="OpenCost overview",
                kind=StudyKind.COURSE,
                source=S("https://opencost.io/docs/"),
                why_for_profile_fr="Kim pratique déjà le FinOps et Prometheus. OpenCost prolonge ce suivi au coût d'une flotte Kubernetes, au lieu d'un premier cours de tableau de bord.",
            ),
        ),
        StudyStep(
            order=11,
            gap_ids=(GapId("observability"),),
            body=StudyResource(
                id=StudyId("dcgm-exporter"),
                title="DCGM Exporter",
                kind=StudyKind.COURSE,
                source=S("https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html"),
                why_for_profile_fr="Kim suit déjà des services avec Prometheus, Grafana et DCGM. L'export DCGM vers Prometheus prolonge ces outils aux métriques d'une flotte de GPU d'entraînement.",
            ),
        ),
    ),
    method_note_fr=(
        "Chaque fiche distingue un fait lu sur une page officielle d'un silence de cette page. Un silence après lecture est marqué comme non indiqué. Une page qui n'a pas pu être ouverte reste non vérifiée.",
        "Les intitulés officiels restent dans la langue publiée. Un sujet n'est posé que si la citation nomme MPI, OpenMP, CUDA ou le thème du registre.",
    ),
    selection_note_fr=(
        "Le corpus retient des masters qui affichent le calcul haute performance, le calcul scientifique ou les systèmes parallèles et distribués.",
        "Les cursus d'ingénieur, les mastères spécialisés, les doctorats, les offres fermées et les mentions trop générales restent dehors. Le catalogue de Bordeaux est gardé sans cours, parce que sa page ne s'est pas ouverte.",
    ),
    takeaways_fr=(
        "MPI, OpenMP et CUDA n'apparaissent que dans les cours ou les accès qui les nomment. Un intitulé seulement parallèle ne suffit pas.",
        "Les maquettes lues parlent de clusters de campus ou de centres de calcul. Elles ne nomment ni Ray, ni SkyPilot, ni une flotte GPU chez plusieurs fournisseurs.",
        "Le coût d'une flotte d'entraînement et son observabilité restent hors des pages de diplôme.",
    ),
    role_need_fr=(
        "Kim Noël construit déjà des applications de modèles de langage. Il exploite Kubernetes, Prometheus, Grafana et le FinOps, et il fait tourner l'inférence sur GPU.",
        "Le rôle visé ajoute l'entraînement distribué. MPI, OpenMP, CUDA, Slurm, InfiniBand, NCCL, Ray et SkyPilot lui manquent encore.",
        "Le coût et l'observabilité à acquérir prolongent le FinOps et Prometheus vers une flotte d'entraînement, au lieu d'un premier tableau de bord.",
    ),
)

PROGRAMS = _france() + _usa() + _chine() + _monde()
