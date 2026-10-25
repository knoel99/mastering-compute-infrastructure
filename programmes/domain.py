"""Survey types, corpus checks, citation order, and the topic matrix."""

from __future__ import annotations

import enum
import re
import unicodedata
import urllib.parse
from dataclasses import dataclass
from datetime import date

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _slug(value: str) -> None:
    if not isinstance(value, str) or _SLUG.fullmatch(value) is None:
        raise ValueError(f"invalid slug: {value!r}")


def _plain(text: str, *, limit: int | None = None) -> str:
    if not isinstance(text, str) or text == "":
        raise ValueError("prose is empty")
    if text != text.strip():
        raise ValueError("prose has surrounding whitespace")
    if "\n" in text or "\r" in text or "|" in text:
        raise ValueError("prose contains a forbidden character")
    if "http://" in text or "https://" in text:
        raise ValueError("prose contains a URL")
    if limit is not None and len(text) > limit:
        raise ValueError("prose is too long")
    return text


def _without_digits(text: str) -> str:
    plain = _plain(text)
    if any(character.isdigit() for character in plain):
        raise ValueError("prose contains a digit")
    return plain


def _paragraphs(items: tuple[str, ...]) -> None:
    if not isinstance(items, tuple) or len(items) == 0:
        raise ValueError("expected a non-empty tuple of paragraphs")
    for item in items:
        _without_digits(item)


def _tuple_of(items: tuple[object, ...], kind: type, label: str) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{label} must be a tuple")
    for item in items:
        if not isinstance(item, kind):
            raise TypeError(f"{label} must contain {kind.__name__}")


def _reason(text: str) -> None:
    _plain(text, limit=240)


def _short(text: str) -> None:
    _plain(text, limit=120)


def _at_least_one(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be an int of at least 1")


class Region(enum.Enum):
    FRANCE = "france"
    USA = "usa"
    CHINE = "chine"
    MONDE = "monde"


class Language(enum.Enum):
    FR = "fr"
    EN = "en"
    FR_EN = "fr_en"


class ProjectKind(enum.Enum):
    PROJECT = "project"
    THESIS = "thesis"
    EITHER = "either"


class StudyKind(enum.Enum):
    MOOC = "mooc"
    BOOK = "book"
    COURSE = "course"


class Field(enum.Enum):
    HOME = "home"
    CREDITS = "credits"
    CORE_EVIDENCE = "core-evidence"
    CORE_COURSE = "core-course"
    ELECTIVES_EVIDENCE = "electives-evidence"
    ELECTIVE_COURSE = "elective-course"
    PROJECT = "project"
    HARDWARE = "hardware"
    PREREQUISITES_EVIDENCE = "prerequisites-evidence"
    PREREQUISITE = "prerequisite"
    SELF_STUDY = "self-study"


class Strength(enum.Enum):
    CORE = "core"
    ELECTIVE = "elective"
    PROJECT = "project"
    HARDWARE = "hardware"


_STRENGTH_RANK = {
    Strength.CORE: 0,
    Strength.ELECTIVE: 1,
    Strength.PROJECT: 2,
    Strength.HARDWARE: 3,
}


@dataclass(frozen=True)
class ProgramId:
    value: str

    def __post_init__(self) -> None:
        _slug(self.value)


@dataclass(frozen=True)
class TopicId:
    value: str

    def __post_init__(self) -> None:
        _slug(self.value)


@dataclass(frozen=True)
class GapId:
    value: str

    def __post_init__(self) -> None:
        _slug(self.value)


@dataclass(frozen=True)
class StudyId:
    value: str

    def __post_init__(self) -> None:
        _slug(self.value)


@dataclass(frozen=True)
class HttpUrl:
    """Absolute http or https URL with a host and no whitespace."""

    value: str

    def __post_init__(self) -> None:
        text = self.value
        if not isinstance(text, str) or text == "" or any(character.isspace() for character in text):
            raise ValueError("url is empty or contains whitespace")
        if not (text.startswith("http://") or text.startswith("https://")):
            raise ValueError("url scheme must be http or https")
        parsed = urllib.parse.urlparse(text)
        if parsed.hostname is None or parsed.hostname == "":
            raise ValueError("url requires a host")


@dataclass(frozen=True)
class AccessDate:
    """A real calendar day in October 2026."""

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        parts = (self.year, self.month, self.day)
        if any(isinstance(part, bool) or not isinstance(part, int) for part in parts):
            raise ValueError("access date must be a real day in October 2026")
        if (self.year, self.month) != (2026, 10):
            raise ValueError("access date must be a real day in October 2026")
        try:
            date(self.year, self.month, self.day)
        except ValueError:
            raise ValueError("access date must be a real day in October 2026") from None


@dataclass(frozen=True)
class Source:
    url: HttpUrl
    accessed: AccessDate

    def __post_init__(self) -> None:
        if not isinstance(self.url, HttpUrl) or not isinstance(self.accessed, AccessDate):
            raise TypeError("source requires an HttpUrl and an AccessDate")


@dataclass(frozen=True)
class InFrance:
    city: str

    def __post_init__(self) -> None:
        _plain(self.city)


@dataclass(frozen=True)
class InUsa:
    city: str
    state: str

    def __post_init__(self) -> None:
        _plain(self.city)
        _plain(self.state)


@dataclass(frozen=True)
class InChina:
    city: str

    def __post_init__(self) -> None:
        _plain(self.city)


@dataclass(frozen=True)
class Elsewhere:
    country: str
    city: str

    def __post_init__(self) -> None:
        _plain(self.country)
        _plain(self.city)


Placement = InFrance | InUsa | InChina | Elsewhere


@dataclass(frozen=True)
class OtherLanguage:
    label_fr: str

    def __post_init__(self) -> None:
        _plain(self.label_fr)


@dataclass(frozen=True)
class LanguageUnknown:
    """The page does not name the teaching language."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


ProgramLanguage = Language | OtherLanguage | LanguageUnknown


@dataclass(frozen=True)
class Ects:
    value: int
    source: Source

    def __post_init__(self) -> None:
        _at_least_one(self.value, "credits")
        if not isinstance(self.source, Source):
            raise TypeError("credits require a Source")


@dataclass(frozen=True)
class UsCredits:
    value: int
    source: Source

    def __post_init__(self) -> None:
        _at_least_one(self.value, "credits")
        if not isinstance(self.source, Source):
            raise TypeError("credits require a Source")


@dataclass(frozen=True)
class OtherCredits:
    label_fr: str
    value: int
    source: Source

    def __post_init__(self) -> None:
        _plain(self.label_fr)
        _at_least_one(self.value, "credits")
        if not isinstance(self.source, Source):
            raise TypeError("credits require a Source")


@dataclass(frozen=True)
class CreditsAbsent:
    """The cited page does not state the credits."""

    note_fr: str
    source: Source

    def __post_init__(self) -> None:
        _plain(self.note_fr)
        if not isinstance(self.source, Source):
            raise TypeError("sourced absence requires a Source")


@dataclass(frozen=True)
class CreditsUnknown:
    """The credits were not read on a page."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


Credits = Ects | UsCredits | OtherCredits | CreditsAbsent | CreditsUnknown


@dataclass(frozen=True)
class Course:
    short_fr: str
    detail_fr: str
    source: Source
    topics: tuple[TopicId, ...]

    def __post_init__(self) -> None:
        _short(self.short_fr)
        _plain(self.detail_fr)
        if not isinstance(self.source, Source):
            raise TypeError("course requires a Source")
        _tuple_of(self.topics, TopicId, "topics")


@dataclass(frozen=True)
class ListedCourses:
    items: tuple[Course, ...]
    evidence: Source

    def __post_init__(self) -> None:
        _tuple_of(self.items, Course, "courses")
        if not isinstance(self.evidence, Source):
            raise TypeError("course list requires a Source")


@dataclass(frozen=True)
class CoursesAbsent:
    """The cited page does not state this course list."""

    note_fr: str
    source: Source

    def __post_init__(self) -> None:
        _plain(self.note_fr)
        if not isinstance(self.source, Source):
            raise TypeError("sourced absence requires a Source")


@dataclass(frozen=True)
class CoursesUnknown:
    """This course list was not read on a page."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


CourseGroup = ListedCourses | CoursesAbsent | CoursesUnknown


@dataclass(frozen=True)
class Described:
    short_fr: str
    detail_fr: str
    source: Source
    topics: tuple[TopicId, ...]

    def __post_init__(self) -> None:
        _short(self.short_fr)
        _plain(self.detail_fr)
        if not isinstance(self.source, Source):
            raise TypeError("description requires a Source")
        _tuple_of(self.topics, TopicId, "topics")


@dataclass(frozen=True)
class ProjectDescribed:
    kind: ProjectKind
    body: Described

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProjectKind) or not isinstance(self.body, Described):
            raise TypeError("project description requires a ProjectKind and a Described body")


@dataclass(frozen=True)
class ProjectAbsent:
    """The cited page does not state the project or thesis."""

    note_fr: str
    source: Source

    def __post_init__(self) -> None:
        _plain(self.note_fr)
        if not isinstance(self.source, Source):
            raise TypeError("sourced absence requires a Source")


@dataclass(frozen=True)
class ProjectUnknown:
    """The project or thesis was not read on a page."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


Project = ProjectDescribed | ProjectAbsent | ProjectUnknown


@dataclass(frozen=True)
class HardwareAbsent:
    """The cited page does not state hardware access."""

    note_fr: str
    source: Source

    def __post_init__(self) -> None:
        _plain(self.note_fr)
        if not isinstance(self.source, Source):
            raise TypeError("sourced absence requires a Source")


@dataclass(frozen=True)
class HardwareUnknown:
    """Hardware access was not read on a page."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


Hardware = Described | HardwareAbsent | HardwareUnknown


@dataclass(frozen=True)
class Prerequisite:
    short_fr: str
    detail_fr: str
    source: Source

    def __post_init__(self) -> None:
        _short(self.short_fr)
        _plain(self.detail_fr)
        if not isinstance(self.source, Source):
            raise TypeError("prerequisite requires a Source")


@dataclass(frozen=True)
class PrerequisitesListed:
    items: tuple[Prerequisite, ...]
    evidence: Source

    def __post_init__(self) -> None:
        _tuple_of(self.items, Prerequisite, "prerequisites")
        if not isinstance(self.evidence, Source):
            raise TypeError("prerequisites require a Source")


@dataclass(frozen=True)
class PrerequisitesAbsent:
    """The cited page does not state prerequisites."""

    note_fr: str
    source: Source

    def __post_init__(self) -> None:
        _plain(self.note_fr)
        if not isinstance(self.source, Source):
            raise TypeError("sourced absence requires a Source")


@dataclass(frozen=True)
class PrerequisitesUnknown:
    """Prerequisites were not read on a page."""

    reason_fr: str

    def __post_init__(self) -> None:
        _reason(self.reason_fr)


Prerequisites = PrerequisitesListed | PrerequisitesAbsent | PrerequisitesUnknown


@dataclass(frozen=True)
class Topic:
    id: TopicId
    label_fr: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, TopicId):
            raise TypeError("topic requires a TopicId")
        _plain(self.label_fr)


@dataclass(frozen=True)
class Gap:
    id: GapId
    title_fr: str
    topic_ids: tuple[TopicId, ...]
    why_short_fr: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, GapId):
            raise TypeError("gap requires a GapId")
        _plain(self.title_fr)
        _tuple_of(self.topic_ids, TopicId, "topic_ids")
        _without_digits(self.why_short_fr)


@dataclass(frozen=True)
class StudyResource:
    id: StudyId
    title: str
    kind: StudyKind
    source: Source
    why_for_profile_fr: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, StudyId):
            raise TypeError("study resource requires a StudyId")
        _plain(self.title)
        if not isinstance(self.kind, StudyKind):
            raise TypeError("study resource requires a StudyKind")
        if not isinstance(self.source, Source):
            raise TypeError("study resource requires a Source")
        _plain(self.why_for_profile_fr)


@dataclass(frozen=True)
class StudyNone:
    id: StudyId
    title_fr: str
    reason_fr: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, StudyId):
            raise TypeError("study step requires a StudyId")
        _plain(self.title_fr)
        _plain(self.reason_fr)


@dataclass(frozen=True)
class StudyStep:
    order: int
    gap_ids: tuple[GapId, ...]
    body: StudyResource | StudyNone

    def __post_init__(self) -> None:
        _at_least_one(self.order, "study step order")
        if not isinstance(self.gap_ids, tuple) or len(self.gap_ids) == 0:
            raise ValueError("gap_ids must be a non-empty tuple")
        _tuple_of(self.gap_ids, GapId, "gap_ids")
        if not isinstance(self.body, (StudyResource, StudyNone)):
            raise TypeError("study step body must be a StudyResource or StudyNone")


@dataclass(frozen=True)
class Meta:
    topics: tuple[Topic, ...]
    gaps: tuple[Gap, ...]
    self_study: tuple[StudyStep, ...]
    method_note_fr: tuple[str, ...]
    selection_note_fr: tuple[str, ...]
    takeaways_fr: tuple[str, ...]
    role_need_fr: tuple[str, ...]

    def __post_init__(self) -> None:
        _tuple_of(self.topics, Topic, "topics")
        _tuple_of(self.gaps, Gap, "gaps")
        _tuple_of(self.self_study, StudyStep, "self_study")
        _paragraphs(self.method_note_fr)
        _paragraphs(self.selection_note_fr)
        _paragraphs(self.takeaways_fr)
        _paragraphs(self.role_need_fr)


@dataclass(frozen=True)
class Program:
    id: ProgramId
    placement: Placement
    school: str
    program_name: str
    language: ProgramLanguage
    credits: Credits
    home: Source
    core: CourseGroup
    electives: CourseGroup
    project: Project
    hardware: Hardware
    prerequisites: Prerequisites

    def __post_init__(self) -> None:
        if not isinstance(self.id, ProgramId):
            raise TypeError("program requires a ProgramId")
        if not isinstance(self.placement, (InFrance, InUsa, InChina, Elsewhere)):
            raise TypeError("program requires a placement")
        _plain(self.school)
        _plain(self.program_name)
        if not isinstance(self.language, (Language, OtherLanguage, LanguageUnknown)):
            raise TypeError("program requires a language")
        if not isinstance(self.credits, (Ects, UsCredits, OtherCredits, CreditsAbsent, CreditsUnknown)):
            raise TypeError("program requires credits")
        if not isinstance(self.home, Source):
            raise TypeError("program requires a home Source")
        if not isinstance(self.core, (ListedCourses, CoursesAbsent, CoursesUnknown)):
            raise TypeError("program requires a core course group")
        if not isinstance(self.electives, (ListedCourses, CoursesAbsent, CoursesUnknown)):
            raise TypeError("program requires an elective course group")
        if not isinstance(self.project, (ProjectDescribed, ProjectAbsent, ProjectUnknown)):
            raise TypeError("program requires a project")
        if not isinstance(self.hardware, (Described, HardwareAbsent, HardwareUnknown)):
            raise TypeError("program requires hardware")
        if not isinstance(self.prerequisites, (PrerequisitesListed, PrerequisitesAbsent, PrerequisitesUnknown)):
            raise TypeError("program requires prerequisites")


@dataclass(frozen=True)
class Corpus:
    meta: Meta
    programs: tuple[Program, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.meta, Meta):
            raise TypeError("corpus requires Meta")
        _tuple_of(self.programs, Program, "programs")


@dataclass(frozen=True)
class Citation:
    url: HttpUrl
    accessed: AccessDate
    owner: ProgramId | StudyId
    field: Field


@dataclass(frozen=True)
class TopicHit:
    program_id: ProgramId
    strength: Strength


@dataclass(frozen=True)
class TopicRow:
    topic_id: TopicId
    hits: tuple[TopicHit, ...]


class CorpusError(Exception):
    """Collected corpus failures. errors is sorted by code point."""

    errors: tuple[str, ...]

    def __init__(self, errors: tuple[str, ...]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


MIN_COUNTS: dict[Region, int] = {
    Region.FRANCE: 6,
    Region.USA: 6,
    Region.CHINE: 5,
    Region.MONDE: 8,
}

REQUIRED_TOPIC_IDS: frozenset[str] = frozenset({
    "mpi",
    "openmp",
    "cuda",
    "architecture",
    "numerical",
    "schedulers",
    "storage-io",
    "networking",
    "cloud-containers",
    "ml-systems",
    "performance",
})

REQUIRED_GAP_IDS: frozenset[str] = frozenset({
    "multi-cloud-gpu",
    "ray",
    "skypilot",
    "cost",
    "observability",
})

BLOCKED_COUNTRY_NAMES: frozenset[str] = frozenset({
    "france",
    "états-unis",
    "etats-unis",
    "united states",
    "usa",
    "u.s.a.",
    "us",
    "chine",
    "china",
    "prc",
})


def region_of(placement: Placement) -> Region:
    """Map InFrance, InUsa, InChina, and Elsewhere onto Region."""
    if isinstance(placement, InFrance):
        return Region.FRANCE
    if isinstance(placement, InUsa):
        return Region.USA
    if isinstance(placement, InChina):
        return Region.CHINE
    if isinstance(placement, Elsewhere):
        return Region.MONDE
    raise TypeError(f"unknown placement: {type(placement).__name__}")


def _country_sort_key(placement: Placement) -> str:
    if isinstance(placement, Elsewhere):
        return placement.country
    return ""


def _program_sort_key(program: Program) -> tuple[int, str, str]:
    return (
        tuple(Region).index(region_of(program.placement)),
        _country_sort_key(program.placement),
        program.id.value,
    )


def _citation(source: Source, owner: ProgramId | StudyId, field: Field) -> Citation:
    return Citation(source.url, source.accessed, owner, field)


def _append_courses(
    citations: list[Citation],
    program_id: ProgramId,
    group: CourseGroup,
    evidence_field: Field,
    course_field: Field,
) -> None:
    if isinstance(group, ListedCourses):
        citations.append(_citation(group.evidence, program_id, evidence_field))
        for course in group.items:
            citations.append(_citation(course.source, program_id, course_field))
        return
    if isinstance(group, CoursesAbsent):
        citations.append(_citation(group.source, program_id, evidence_field))
        return
    if isinstance(group, CoursesUnknown):
        return
    raise TypeError(type(group).__name__)


def _program_citations(program: Program) -> list[Citation]:
    citations: list[Citation] = [_citation(program.home, program.id, Field.HOME)]
    credits = program.credits
    if isinstance(credits, (Ects, UsCredits, OtherCredits, CreditsAbsent)):
        citations.append(_citation(credits.source, program.id, Field.CREDITS))
    elif not isinstance(credits, CreditsUnknown):
        raise TypeError(type(credits).__name__)
    _append_courses(
        citations,
        program.id,
        program.core,
        Field.CORE_EVIDENCE,
        Field.CORE_COURSE,
    )
    _append_courses(
        citations,
        program.id,
        program.electives,
        Field.ELECTIVES_EVIDENCE,
        Field.ELECTIVE_COURSE,
    )
    project = program.project
    if isinstance(project, ProjectDescribed):
        citations.append(_citation(project.body.source, program.id, Field.PROJECT))
    elif isinstance(project, ProjectAbsent):
        citations.append(_citation(project.source, program.id, Field.PROJECT))
    elif not isinstance(project, ProjectUnknown):
        raise TypeError(type(project).__name__)
    hardware = program.hardware
    if isinstance(hardware, Described):
        citations.append(_citation(hardware.source, program.id, Field.HARDWARE))
    elif isinstance(hardware, HardwareAbsent):
        citations.append(_citation(hardware.source, program.id, Field.HARDWARE))
    elif not isinstance(hardware, HardwareUnknown):
        raise TypeError(type(hardware).__name__)
    prerequisites = program.prerequisites
    if isinstance(prerequisites, PrerequisitesListed):
        citations.append(
            _citation(prerequisites.evidence, program.id, Field.PREREQUISITES_EVIDENCE)
        )
        for item in prerequisites.items:
            citations.append(_citation(item.source, program.id, Field.PREREQUISITE))
    elif isinstance(prerequisites, PrerequisitesAbsent):
        citations.append(
            _citation(prerequisites.source, program.id, Field.PREREQUISITES_EVIDENCE)
        )
    elif not isinstance(prerequisites, PrerequisitesUnknown):
        raise TypeError(type(prerequisites).__name__)
    return citations


def _consider_topics(
    best: dict[str, Strength],
    topic_ids: tuple[TopicId, ...],
    strength: Strength,
) -> None:
    rank = _STRENGTH_RANK[strength]
    for topic_id in topic_ids:
        current = best.get(topic_id.value)
        if current is None or rank < _STRENGTH_RANK[current]:
            best[topic_id.value] = strength


def _hits_for_program(program: Program) -> dict[str, Strength]:
    best: dict[str, Strength] = {}
    core = program.core
    if isinstance(core, ListedCourses):
        for course in core.items:
            _consider_topics(best, course.topics, Strength.CORE)
    electives = program.electives
    if isinstance(electives, ListedCourses):
        for course in electives.items:
            _consider_topics(best, course.topics, Strength.ELECTIVE)
    project = program.project
    if isinstance(project, ProjectDescribed):
        _consider_topics(best, project.body.topics, Strength.PROJECT)
    hardware = program.hardware
    if isinstance(hardware, Described):
        _consider_topics(best, hardware.topics, Strength.HARDWARE)
    return best


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    found: list[str] = []
    emitted: set[str] = set()
    for value in values:
        if value in seen and value not in emitted:
            found.append(value)
            emitted.add(value)
        seen.add(value)
    return found


def validate(corpus: Corpus) -> None:
    """Raise CorpusError with every collection error, sorted by code point.

    Constructor checks are not repeated here.
    """
    errors: set[str] = set()
    program_ids: list[str] = []
    program_names: list[tuple[str, str]] = []
    counts = {region: 0 for region in Region}
    hit_ids: set[str] = set()
    registry = {topic.id.value for topic in corpus.meta.topics}
    for program in corpus.programs:
        program_ids.append(program.id.value)
        program_names.append((program.school, program.program_name))
        counts[region_of(program.placement)] += 1
        if isinstance(program.placement, Elsewhere):
            country = program.placement.country
            if country.casefold() in BLOCKED_COUNTRY_NAMES:
                errors.add(f"country {country} belongs on a fixed region page")
        hits = _hits_for_program(program)
        for topic_value in hits:
            if topic_value in registry:
                hit_ids.add(topic_value)
            else:
                errors.add(
                    f"unknown topic id {topic_value} on program {program.id.value}"
                )
        shorts: list[str] = []
        for group in (program.core, program.electives):
            if isinstance(group, ListedCourses):
                shorts.extend(course.short_fr for course in group.items)
        for short_fr in _duplicates(shorts):
            errors.add(f"duplicate course {short_fr} on program {program.id.value}")
        if isinstance(program.prerequisites, PrerequisitesListed):
            for short_fr in _duplicates(
                [item.short_fr for item in program.prerequisites.items]
            ):
                errors.add(
                    f"duplicate prerequisite {short_fr} on program {program.id.value}"
                )
    for program_id in _duplicates(program_ids):
        errors.add(f"duplicate program id {program_id}")
    seen_names: set[tuple[str, str]] = set()
    emitted_names: set[tuple[str, str]] = set()
    for school, program_name in program_names:
        key = (school, program_name)
        if key in seen_names and key not in emitted_names:
            errors.add(f"duplicate program name for {school}: {program_name}")
            emitted_names.add(key)
        seen_names.add(key)
    for region, minimum in MIN_COUNTS.items():
        count = counts[region]
        if count < minimum:
            noun = "program" if count == 1 else "programs"
            errors.add(f"{region.value} has {count} {noun}, minimum is {minimum}")
    for topic_id in _duplicates([topic.id.value for topic in corpus.meta.topics]):
        errors.add(f"duplicate topic id {topic_id}")
    for label in _duplicates([topic.label_fr for topic in corpus.meta.topics]):
        errors.add(f"duplicate topic label {label}")
    for topic_id in REQUIRED_TOPIC_IDS:
        if topic_id not in registry:
            errors.add(f"missing required topic id {topic_id}")
    for topic in corpus.meta.topics:
        if topic.id.value not in REQUIRED_TOPIC_IDS and topic.id.value not in hit_ids:
            errors.add(f"optional topic id {topic.id.value} has no program")
    known_gaps = {gap.id.value for gap in corpus.meta.gaps}
    for gap in corpus.meta.gaps:
        for topic_id in gap.topic_ids:
            if topic_id.value not in registry:
                errors.add(f"unknown topic id {topic_id.value} on gap {gap.id.value}")
    for gap_id in _duplicates([gap.id.value for gap in corpus.meta.gaps]):
        errors.add(f"duplicate gap id {gap_id}")
    for label in _duplicates([gap.title_fr for gap in corpus.meta.gaps]):
        errors.add(f"duplicate gap label {label}")
    for gap_id in REQUIRED_GAP_IDS:
        if gap_id not in known_gaps:
            errors.add(f"missing required gap id {gap_id}")
    covered: set[str] = set()
    study_ids: list[str] = []
    for step in corpus.meta.self_study:
        study_ids.append(step.body.id.value)
        unknown_gaps = {
            gap_id.value for gap_id in step.gap_ids if gap_id.value not in known_gaps
        }
        for gap_value in unknown_gaps:
            errors.add(f"unknown gap id {gap_value} on study step {step.order}")
        for gap_id in step.gap_ids:
            covered.add(gap_id.value)
    for gap in corpus.meta.gaps:
        if gap.id.value not in covered:
            errors.add(f"gap id {gap.id.value} has no self-study step")
    for study_id in _duplicates(study_ids):
        errors.add(f"duplicate study id {study_id}")
    orders = [step.order for step in corpus.meta.self_study]
    if sorted(orders) != list(range(1, len(orders) + 1)):
        errors.add(f"study step orders must be 1 through {len(orders)}")
    dates: dict[str, set[AccessDate]] = {}
    for citation in iter_sources(corpus):
        dates.setdefault(citation.url.value, set()).add(citation.accessed)
    for url, seen_dates in dates.items():
        if len(seen_dates) > 1:
            errors.add(f"url {url} has more than one access date")
    if errors:
        raise CorpusError(tuple(sorted(errors)))


def iter_sources(corpus: Corpus) -> tuple[Citation, ...]:
    """List every Source the pages may print, in output order.

    Sort programs by Region enum order, then by Elsewhere.country or the
    empty string for the other placements, using Python's default str
    sort, then by ProgramId value. Inside a program the order is home,
    credits source when present, core evidence, core courses in tuple
    order, electives evidence, elective courses, project source when
    present, hardware source when present, prerequisites evidence,
    prerequisites in tuple order. A sourced absence contributes its
    source in that same slot. Unknown variants contribute no citation.
    Study steps follow, sorted by order, and StudyResource contributes
    one SELF_STUDY citation. StudyNone contributes none.
    """
    citations: list[Citation] = []
    for program in sorted(corpus.programs, key=_program_sort_key):
        citations.extend(_program_citations(program))
    for step in sorted(corpus.meta.self_study, key=lambda item: item.order):
        if isinstance(step.body, StudyResource):
            citations.append(
                _citation(step.body.source, step.body.id, Field.SELF_STUDY)
            )
    return tuple(citations)


def matrix(corpus: Corpus) -> tuple[TopicRow, ...]:
    """One row per visible topic, in META.topics order.

    A program contributes at most one hit. Strength is the strongest
    evidence among core courses, electives, the project body, and the
    hardware description. Rank is CORE, then ELECTIVE, then PROJECT,
    then HARDWARE. Prerequisites add no hit. A topic id in
    REQUIRED_TOPIC_IDS is always a row. Any other topic is a row only
    when it has at least one hit. Hits inside a row are sorted by program id.
    """
    grouped: dict[str, list[TopicHit]] = {}
    for program in corpus.programs:
        for topic_value, strength in _hits_for_program(program).items():
            grouped.setdefault(topic_value, []).append(
                TopicHit(program.id, strength)
            )
    rows: list[TopicRow] = []
    for topic in corpus.meta.topics:
        hits = grouped.get(topic.id.value, [])
        if topic.id.value not in REQUIRED_TOPIC_IDS and not hits:
            continue
        ordered = tuple(sorted(hits, key=lambda hit: hit.program_id.value))
        rows.append(TopicRow(topic.id, ordered))
    return tuple(rows)
