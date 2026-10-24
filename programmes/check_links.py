"""French pages, link check, and the survey command."""

from __future__ import annotations

import enum
import os
import re
import socket
import ssl
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from contextlib import redirect_stdout
from dataclasses import dataclass, replace
from io import StringIO
from pathlib import Path

_PROGRAMMES_DIR = Path(__file__).resolve().parent
_ROOT_ON_PATH = str(_PROGRAMMES_DIR)
if sys.path[0] != _ROOT_ON_PATH:
    sys.path.insert(0, _ROOT_ON_PATH)

import domain

_USER_AGENT = "mastering-compute-infrastructure-check-links/1.0"
_PAGE_URL = re.compile(r"https?://[^\s)\]]+")
_USAGE = (
    "usage: python programmes/check_links.py "
    "[--timeout SECONDS] [--check | --render | --self-test | --help]"
)

LANGUAGE_FR = {
    domain.Language.FR: "français",
    domain.Language.EN: "anglais",
    domain.Language.FR_EN: "français et anglais",
}
STRENGTH_FR = {
    domain.Strength.CORE: "tronc",
    domain.Strength.ELECTIVE: "électif",
    domain.Strength.PROJECT: "projet ou mémoire",
    domain.Strength.HARDWARE: "accès matériel",
}
PROJECT_KIND_FR = {
    domain.ProjectKind.PROJECT: "Projet",
    domain.ProjectKind.THESIS: "Mémoire",
    domain.ProjectKind.EITHER: "Projet ou mémoire",
}
STUDY_KIND_FR = {
    domain.StudyKind.MOOC: "MOOC",
    domain.StudyKind.BOOK: "livre",
    domain.StudyKind.COURSE: "cours",
}


class _Usage(Exception):
    pass


class _RedirectLimitError(Exception):
    pass


class _FiveRedirects(urllib.request.HTTPRedirectHandler):
    max_repeats = 1000
    max_redirections = 1000

    def __init__(self) -> None:
        super().__init__()
        self._hops = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._hops += 1
        if self._hops > 5:
            try:
                fp.close()
            except OSError:
                pass
            raise _RedirectLimitError()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class BlockKind(enum.Enum):
    TIMEOUT = "timeout"
    DNS = "dns"
    CONNECTION = "connection"
    TLS = "tls"
    RATE_LIMIT = "rate_limit"
    REDIRECT_LIMIT = "redirect_limit"


@dataclass(frozen=True)
class FetchOk:
    http_status: int
    final_url: str


@dataclass(frozen=True)
class FetchMissing:
    http_status: int
    final_url: str


@dataclass(frozen=True)
class FetchForbidden:
    http_status: int
    final_url: str


@dataclass(frozen=True)
class FetchBlocked:
    kind: BlockKind
    detail: str


@dataclass(frozen=True)
class FetchOther:
    http_status: int
    final_url: str


LinkStatus = FetchOk | FetchMissing | FetchForbidden | FetchBlocked | FetchOther


@dataclass(frozen=True)
class UrlResult:
    url: domain.HttpUrl
    status: LinkStatus
    citations: tuple[domain.Citation, ...]


@dataclass(frozen=True)
class LinkReport:
    results: tuple[UrlResult, ...]


def output_pages() -> tuple[str, ...]:
    """Return index.md, then each Region value plus .md, then synthese.md."""
    return (
        "index.md",
        *(f"{region.value}.md" for region in domain.Region),
        "synthese.md",
    )


def load_corpus() -> domain.Corpus:
    """Import records, build Corpus, and validate it.

    The records import stays inside this function so --self-test can run
    before records.py exists.
    """
    import records

    programs = records.PROGRAMS
    if not isinstance(programs, tuple):
        programs = tuple(programs)
    corpus = domain.Corpus(meta=records.META, programs=programs)
    domain.validate(corpus)
    return corpus


def _iso(accessed: domain.AccessDate) -> str:
    return f"{accessed.year:04d}-{accessed.month:02d}-{accessed.day:02d}"


def _finish(lines: list[str]) -> str:
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def _urls_in_pages(texts: Iterable[str]) -> set[str]:
    found: set[str] = set()
    for text in texts:
        found.update(_PAGE_URL.findall(text))
    return found


def _assert_page_urls(corpus: domain.Corpus, texts: Iterable[str]) -> None:
    found = _urls_in_pages(texts)
    cited = {citation.url.value for citation in domain.iter_sources(corpus)}
    errors = [f"url {url} is on a page and not cited" for url in found - cited]
    errors.extend(
        f"url {url} is cited and missing on the pages" for url in cited - found
    )
    if errors:
        raise domain.CorpusError(tuple(sorted(errors)))


def render(corpus: domain.Corpus) -> dict[str, str]:
    """Return UTF-8 page text for every output_pages() name.

    Each value uses LF, no BOM, and one trailing newline. Keys equal
    output_pages(). Page wording is nested in this function. Sort with
    Python's default str order, never a locale order. Read minima from
    MIN_COUNTS when writing the method paragraph.
    """
    label_of = {topic.id.value: topic.label_fr for topic in corpus.meta.topics}
    gap_title = {gap.id.value: gap.title_fr for gap in corpus.meta.gaps}
    citations = domain.iter_sources(corpus)
    program_order: list[str] = []
    for citation in citations:
        if isinstance(citation.owner, domain.ProgramId) and citation.owner.value not in program_order:
            program_order.append(citation.owner.value)
    rank = {program_id: index for index, program_id in enumerate(program_order)}
    programs = tuple(sorted(corpus.programs, key=lambda program: rank[program.id.value]))
    program_by_id = {program.id.value: program for program in corpus.programs}
    rows = domain.matrix(corpus)

    def region_title(region: domain.Region) -> str:
        titles = {
            domain.Region.FRANCE: "France",
            domain.Region.USA: "États-Unis",
            domain.Region.CHINE: "Chine",
            domain.Region.MONDE: "Reste du monde",
        }
        return titles[region]

    def cite(source: domain.Source) -> str:
        return f"{source.url.value} consulté le {_iso(source.accessed)}"

    def unknown(reason_fr: str) -> str:
        return f"Non vérifié. {reason_fr}"

    def absent(note_fr: str, source: domain.Source) -> str:
        return f"Non indiqué sur la page. {note_fr}. {cite(source)}."

    def topic_labels(topic_ids: tuple[domain.TopicId, ...]) -> str:
        return ", ".join(label_of.get(topic_id.value, topic_id.value) for topic_id in topic_ids)

    def ended(text: str) -> str:
        if text.endswith("."):
            return text
        return f"{text}."

    def described_sentence(short_fr: str, detail_fr: str, topic_ids: tuple[domain.TopicId, ...], source: domain.Source) -> str:
        body = f"{short_fr}. {ended(detail_fr)}"
        if topic_ids:
            body = f"{body} Sujets : {topic_labels(topic_ids)}."
        return f"{body} {cite(source)}."

    def language_text(language: domain.ProgramLanguage) -> str:
        if isinstance(language, domain.Language):
            return LANGUAGE_FR[language]
        if isinstance(language, domain.OtherLanguage):
            return language.label_fr
        if isinstance(language, domain.LanguageUnknown):
            return unknown(language.reason_fr)
        raise TypeError(type(language).__name__)

    def credit_text(credits: domain.Credits) -> str:
        if isinstance(credits, domain.Ects):
            return f"{credits.value} ECTS"
        if isinstance(credits, domain.UsCredits):
            return f"{credits.value} crédits US"
        if isinstance(credits, domain.OtherCredits):
            return f"{credits.value} {credits.label_fr}"
        if isinstance(credits, domain.CreditsUnknown):
            return unknown(credits.reason_fr)
        if isinstance(credits, domain.CreditsAbsent):
            return absent(credits.note_fr, credits.source)
        raise TypeError(type(credits).__name__)

    def credit_lines(credits: domain.Credits) -> list[str]:
        if isinstance(credits, (domain.CreditsUnknown, domain.CreditsAbsent)):
            return [credit_text(credits)]
        if isinstance(credits, (domain.Ects, domain.UsCredits, domain.OtherCredits)):
            return [credit_text(credits), "", cite(credits.source)]
        raise TypeError(type(credits).__name__)

    def course_lines(group: domain.CourseGroup) -> list[str]:
        if isinstance(group, domain.CoursesUnknown):
            return [unknown(group.reason_fr)]
        if isinstance(group, domain.CoursesAbsent):
            return [absent(group.note_fr, group.source)]
        if isinstance(group, domain.ListedCourses):
            lines = [cite(group.evidence), ""]
            if not group.items:
                lines.append("La page officielle n'en liste aucun.")
                return lines
            for course in group.items:
                lines.append(
                    "- "
                    + described_sentence(
                        course.short_fr,
                        course.detail_fr,
                        course.topics,
                        course.source,
                    )
                )
            return lines
        raise TypeError(type(group).__name__)

    def project_lines(project: domain.Project) -> list[str]:
        if isinstance(project, domain.ProjectUnknown):
            return [unknown(project.reason_fr)]
        if isinstance(project, domain.ProjectAbsent):
            return [absent(project.note_fr, project.source)]
        if isinstance(project, domain.ProjectDescribed):
            body = project.body
            return [
                PROJECT_KIND_FR[project.kind],
                "",
                described_sentence(body.short_fr, body.detail_fr, body.topics, body.source),
            ]
        raise TypeError(type(project).__name__)

    def hardware_lines(hardware: domain.Hardware) -> list[str]:
        if isinstance(hardware, domain.HardwareUnknown):
            return [unknown(hardware.reason_fr)]
        if isinstance(hardware, domain.HardwareAbsent):
            return [absent(hardware.note_fr, hardware.source)]
        if isinstance(hardware, domain.Described):
            return [
                described_sentence(
                    hardware.short_fr,
                    hardware.detail_fr,
                    hardware.topics,
                    hardware.source,
                )
            ]
        raise TypeError(type(hardware).__name__)

    def prerequisite_lines(prerequisites: domain.Prerequisites) -> list[str]:
        if isinstance(prerequisites, domain.PrerequisitesUnknown):
            return [unknown(prerequisites.reason_fr)]
        if isinstance(prerequisites, domain.PrerequisitesAbsent):
            return [absent(prerequisites.note_fr, prerequisites.source)]
        if isinstance(prerequisites, domain.PrerequisitesListed):
            lines = [cite(prerequisites.evidence), ""]
            if not prerequisites.items:
                lines.append("La page officielle n'en liste aucun.")
                return lines
            for item in prerequisites.items:
                lines.append(
                    f"- {item.short_fr}. {ended(item.detail_fr)} {cite(item.source)}."
                )
            return lines
        raise TypeError(type(prerequisites).__name__)

    def place_label(placement: domain.Placement) -> str:
        if isinstance(placement, domain.InFrance):
            return f"{placement.city}, France"
        if isinstance(placement, domain.InUsa):
            return f"{placement.city}, {placement.state}, États-Unis"
        if isinstance(placement, domain.InChina):
            return f"{placement.city}, Chine"
        if isinstance(placement, domain.Elsewhere):
            return f"{placement.city}, {placement.country}"
        raise TypeError(type(placement).__name__)

    def markdown_links(program: domain.Program) -> str:
        """One Markdown link per distinct program URL, in citation order.

        A space before "]" keeps the link-text URL from running into the
        destination. The page scan stops at whitespace or ")".
        """
        parts: list[str] = []
        seen: set[str] = set()
        for citation in citations:
            if citation.owner != program.id or citation.url.value in seen:
                continue
            seen.add(citation.url.value)
            url = citation.url.value
            parts.append(f"[{url}]({url}) consulté le {_iso(citation.accessed)}")
        return "<br>".join(parts)

    def core_cell(group: domain.CourseGroup) -> str:
        if isinstance(group, domain.ListedCourses):
            if not group.items:
                return "La page officielle n'en liste aucun."
            return ", ".join(course.short_fr for course in group.items)
        if isinstance(group, domain.CoursesUnknown):
            return unknown(group.reason_fr)
        if isinstance(group, domain.CoursesAbsent):
            return absent(group.note_fr, group.source)
        raise TypeError(type(group).__name__)

    def hardware_cell(hardware: domain.Hardware) -> str:
        if isinstance(hardware, domain.Described):
            return hardware.short_fr
        if isinstance(hardware, domain.HardwareUnknown):
            return unknown(hardware.reason_fr)
        if isinstance(hardware, domain.HardwareAbsent):
            return absent(hardware.note_fr, hardware.source)
        raise TypeError(type(hardware).__name__)

    def index_table(selected: list[domain.Program]) -> list[str]:
        lines = [
            "| École | Programme | Crédits | Langue | Cours de tronc | Accès matériel | Lien |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for program in selected:
            cells = [
                program.school,
                program.program_name,
                credit_text(program.credits),
                language_text(program.language),
                core_cell(program.core),
                hardware_cell(program.hardware),
                markdown_links(program),
            ]
            lines.append("| " + " | ".join(cells) + " |")
        return lines

    def program_block(program: domain.Program) -> list[str]:
        def section(title: str, body: list[str]) -> list[str]:
            return [f"### {title}", "", *body]

        parts = [
            [
                f"## {program.school}, {program.program_name}",
                "",
                f"Identifiant : `{program.id.value}`",
            ],
            section("Page officielle", [cite(program.home)]),
            section("Lieu", [place_label(program.placement)]),
            section("Langue", [language_text(program.language)]),
            section("Crédits", credit_lines(program.credits)),
            section("Cours de tronc", course_lines(program.core)),
            section("Électifs", course_lines(program.electives)),
            section("Projet ou mémoire", project_lines(program.project)),
            section("Accès matériel", hardware_lines(program.hardware)),
            section("Prérequis", prerequisite_lines(program.prerequisites)),
        ]
        lines: list[str] = []
        for index, part in enumerate(parts):
            if index:
                lines.append("")
            lines.extend(part)
        return lines

    def count_phrase(count: int) -> str:
        if count == 1:
            return "1 programme"
        return f"{count} programmes"

    def hit_counts(row: domain.TopicRow | None) -> dict[domain.Region, int]:
        counts = {region: 0 for region in domain.Region}
        if row is None:
            return counts
        for hit in row.hits:
            program = program_by_id[hit.program_id.value]
            counts[domain.region_of(program.placement)] += 1
        return counts

    def index_page() -> str:
        minima = domain.MIN_COUNTS
        lines = [
            "# Masters en HPC et calcul distribué",
            "",
            "## Méthode",
            "",
            (
                "Le corpus publié compte au moins "
                f"{minima[domain.Region.FRANCE]} masters en France, "
                f"{minima[domain.Region.USA]} aux États-Unis, "
                f"{minima[domain.Region.CHINE]} en Chine et "
                f"{minima[domain.Region.MONDE]} dans le reste du monde. "
                "Chaque crédit, cours, projet, accès matériel ou prérequis est soit "
                "une source officielle consultée en octobre 2026, soit une mention "
                "explicite que le fait n'est pas vérifié."
            ),
            "",
        ]
        for paragraph in corpus.meta.method_note_fr:
            lines.append(paragraph)
            lines.append("")
        lines.append("## Critères de sélection")
        lines.append("")
        for paragraph in corpus.meta.selection_note_fr:
            lines.append(paragraph)
            lines.append("")
        for region in (domain.Region.FRANCE, domain.Region.USA, domain.Region.CHINE):
            lines.append(f"## {region_title(region)}")
            lines.append("")
            selected = [
                program
                for program in programs
                if domain.region_of(program.placement) is region
            ]
            lines.extend(index_table(selected))
            lines.append("")
        lines.append("## Reste du monde")
        lines.append("")
        monde = [
            program
            for program in programs
            if domain.region_of(program.placement) is domain.Region.MONDE
        ]
        grouped: list[tuple[str, list[domain.Program]]] = []
        for program in monde:
            country = program.placement.country
            if grouped and grouped[-1][0] == country:
                grouped[-1][1].append(program)
            else:
                grouped.append((country, [program]))
        for country, group in grouped:
            lines.append(f"### {country}")
            lines.append("")
            lines.extend(index_table(group))
            lines.append("")
        lines.append("## À retenir")
        lines.append("")
        for takeaway in corpus.meta.takeaways_fr:
            lines.append(f"- {takeaway}")
        return _finish(lines)

    def region_page(region: domain.Region) -> str:
        if region is domain.Region.FRANCE:
            intro = "Ces masters sont une voie d'inscription réaliste depuis Paris."
        else:
            intro = (
                "Ces pages décrivent le curriculum. "
                "Elles ne décrivent pas un projet de déménagement."
            )
        lines = [f"# {region_title(region)}", "", intro, ""]
        selected = [
            program
            for program in programs
            if domain.region_of(program.placement) is region
        ]
        for index, program in enumerate(selected):
            if index:
                lines.append("")
            lines.extend(program_block(program))
        return _finish(lines)

    def synthese_page() -> str:
        lines = [
            "# Synthèse",
            "",
            "## Fréquence des sujets",
            "",
            "| Sujet | France | États-Unis | Chine | Monde | Total |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        row_by_topic = {row.topic_id.value: row for row in rows}
        for row in rows:
            counts = hit_counts(row)
            total = sum(counts.values())
            lines.append(
                f"| {label_of[row.topic_id.value]} | {counts[domain.Region.FRANCE]} | "
                f"{counts[domain.Region.USA]} | {counts[domain.Region.CHINE]} | "
                f"{counts[domain.Region.MONDE]} | {total} |"
            )
        lines.append("")
        lines.append("## Programmes par sujet")
        lines.append("")
        for row in rows:
            lines.append(f"### {label_of[row.topic_id.value]}")
            lines.append("")
            if not row.hits:
                lines.append("Aucun programme.")
            else:
                for hit in row.hits:
                    program = program_by_id[hit.program_id.value]
                    strength = STRENGTH_FR[hit.strength].capitalize()
                    lines.append(
                        f"- {program.school}, {program.program_name}. {strength}."
                    )
            lines.append("")
        lines.append("## Rôle")
        lines.append("")
        for paragraph in corpus.meta.role_need_fr:
            lines.append(paragraph)
            lines.append("")
        lines.append("## Lacunes")
        lines.append("")
        total_programs = len(corpus.programs)
        for gap in corpus.meta.gaps:
            lines.append(f"### {gap.title_fr}")
            lines.append("")
            if not gap.topic_ids:
                lines.append("Aucun sujet du registre n'est rattaché à cette lacune.")
            else:
                for topic_id in gap.topic_ids:
                    row = row_by_topic.get(topic_id.value)
                    counts = hit_counts(row)
                    hit_total = sum(counts.values())
                    lines.append(
                        f"{label_of.get(topic_id.value, topic_id.value)}. "
                        f"{count_phrase(hit_total)} sur {count_phrase(total_programs)}. "
                        f"France {counts[domain.Region.FRANCE]}, "
                        f"États-Unis {counts[domain.Region.USA]}, "
                        f"Chine {counts[domain.Region.CHINE]}, "
                        f"Monde {counts[domain.Region.MONDE]}."
                    )
            lines.append("")
            lines.append(gap.why_short_fr)
            lines.append("")
        lines.append("## Auto-formation")
        lines.append("")
        for step in sorted(corpus.meta.self_study, key=lambda item: item.order):
            titles = ", ".join(
                gap_title.get(gap_id.value, gap_id.value) for gap_id in step.gap_ids
            )
            body = step.body
            if isinstance(body, domain.StudyNone):
                lines.append(
                    f"{step.order}. {body.title_fr}. Aucune ressource gratuite retenue. "
                    f"{body.reason_fr} Lacunes : {titles}."
                )
            elif isinstance(body, domain.StudyResource):
                lines.append(
                    f"{step.order}. {body.title}. {STUDY_KIND_FR[body.kind]}. "
                    f"{cite(body.source)}. Lacunes : {titles}. {body.why_for_profile_fr}"
                )
            else:
                raise TypeError(type(body).__name__)
        return _finish(lines)

    pages = {
        "index.md": index_page(),
        "france.md": region_page(domain.Region.FRANCE),
        "usa.md": region_page(domain.Region.USA),
        "chine.md": region_page(domain.Region.CHINE),
        "monde.md": region_page(domain.Region.MONDE),
        "synthese.md": synthese_page(),
    }
    return {name: pages[name] for name in output_pages()}


def _write_pages(corpus: domain.Corpus, root: Path) -> None:
    """Validate, render, and replace the six pages under root.

    Validate before creating a temp file. Delete a leftover
    `.{name}.tmp` for those six names, write the temp file, then
    os.replace it onto the destination. Write no other filename.
    """
    domain.validate(corpus)
    pages = render(corpus)
    for name in output_pages():
        temporary = root / f".{name}.tmp"
        if temporary.is_file():
            temporary.unlink()
        temporary.write_bytes(pages[name].encode("utf-8"))
        os.replace(temporary, root / name)


def _require_match(corpus: domain.Corpus, root: Path) -> None:
    """Validate, render, and raise CorpusError when a page is missing or differs."""
    domain.validate(corpus)
    pages = render(corpus)
    errors: list[str] = []
    for name in output_pages():
        path = root / name
        if not path.is_file():
            errors.append(f"missing page {name}")
            continue
        if path.read_bytes() != pages[name].encode("utf-8"):
            errors.append(f"page {name} does not match the corpus")
    if errors:
        raise domain.CorpusError(tuple(sorted(errors)))


def _from_status(status: int, final_url: str) -> LinkStatus:
    if 200 <= status <= 299:
        return FetchOk(status, final_url)
    if status == 404:
        return FetchMissing(status, final_url)
    if status == 403:
        return FetchForbidden(status, final_url)
    if status == 429:
        return FetchBlocked(BlockKind.RATE_LIMIT, str(status))
    return FetchOther(status, final_url)


def _kind_of(reason: object) -> BlockKind:
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return BlockKind.TIMEOUT
    if isinstance(reason, socket.gaierror):
        return BlockKind.DNS
    if isinstance(reason, ssl.SSLError):
        return BlockKind.TLS
    text = str(reason).casefold()
    if "timed out" in text or "timeout" in text:
        return BlockKind.TIMEOUT
    if "certificate" in text or "ssl" in text or "tls" in text:
        return BlockKind.TLS
    if (
        "getaddrinfo" in text
        or "name or service not known" in text
        or "nodename nor servname" in text
        or "temporary failure in name resolution" in text
    ):
        return BlockKind.DNS
    return BlockKind.CONNECTION


def fetch_url(url: domain.HttpUrl, timeout_s: float) -> LinkStatus:
    """GET the URL once with urllib and classify the outcome. See Link checker."""
    opener = urllib.request.build_opener(_FiveRedirects)
    request = urllib.request.Request(
        url.value,
        headers={"User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with opener.open(request, timeout=timeout_s) as response:
            final_url = response.geturl()
            status = response.status
            response.read()
            return _from_status(status, final_url)
    except _RedirectLimitError:
        return FetchBlocked(BlockKind.REDIRECT_LIMIT, "redirect limit")
    except urllib.error.HTTPError as err:
        try:
            if str(err).startswith("The HTTP server returned a redirect error"):
                return FetchBlocked(BlockKind.REDIRECT_LIMIT, "redirect limit")
            if err.code == 429:
                return FetchBlocked(BlockKind.RATE_LIMIT, str(err))
            return _from_status(err.code, err.geturl())
        finally:
            err.close()
    except urllib.error.URLError as err:
        return FetchBlocked(_kind_of(err.reason), str(err))
    except (TimeoutError, socket.timeout) as err:
        return FetchBlocked(BlockKind.TIMEOUT, str(err))
    except ssl.SSLError as err:
        return FetchBlocked(BlockKind.TLS, str(err))
    except socket.gaierror as err:
        return FetchBlocked(BlockKind.DNS, str(err))
    except OSError as err:
        return FetchBlocked(BlockKind.CONNECTION, str(err))


def check_links(
    citations: tuple[domain.Citation, ...],
    fetch: Callable[[domain.HttpUrl], LinkStatus],
) -> LinkReport:
    """Fetch each distinct URL once, in first-citation order, and keep every citation."""
    order: list[str] = []
    grouped: dict[str, list[domain.Citation]] = {}
    urls: dict[str, domain.HttpUrl] = {}
    for citation in citations:
        key = citation.url.value
        if key not in grouped:
            order.append(key)
            grouped[key] = []
            urls[key] = citation.url
        grouped[key].append(citation)
    results = tuple(
        UrlResult(urls[key], fetch(urls[key]), tuple(grouped[key])) for key in order
    )
    return LinkReport(results)


def exit_code(report: LinkReport) -> int:
    """Return 1 if any FetchMissing, else 3 if any FetchForbidden, else 4 if any FetchBlocked or FetchOther, else 0.

    Exit 2 belongs to main.
    """
    statuses = [result.status for result in report.results]
    if any(isinstance(status, FetchMissing) for status in statuses):
        return 1
    if any(isinstance(status, FetchForbidden) for status in statuses):
        return 3
    if any(isinstance(status, (FetchBlocked, FetchOther)) for status in statuses):
        return 4
    return 0


def _status_key(status: LinkStatus) -> str:
    if isinstance(status, FetchOk):
        return "ok"
    if isinstance(status, FetchMissing):
        return "missing"
    if isinstance(status, FetchForbidden):
        return "forbidden"
    if isinstance(status, FetchBlocked):
        return "blocked"
    return "other"


def _print_result(result: UrlResult) -> None:
    print(f"- url: {result.url.value}")
    status = result.status
    if isinstance(status, FetchBlocked):
        print(f"  kind: {status.kind.value}")
        print(f"  detail: {status.detail}")
    else:
        print(f"  http_status: {status.http_status}")
        print(f"  final_url: {status.final_url}")
    print("  citations:")
    for citation in result.citations:
        print(f"    - {citation.owner.value} {citation.field.value}")


def _print_report(report: LinkReport) -> None:
    counts = {key: 0 for key in ("ok", "missing", "forbidden", "blocked", "other")}
    grouped: dict[str, list[UrlResult]] = {key: [] for key in counts}
    for result in report.results:
        key = _status_key(result.status)
        counts[key] += 1
        grouped[key].append(result)
    print("integrity: ok")
    print(f"urls: {len(report.results)}")
    print(f"ok: {counts['ok']}")
    print(f"missing: {counts['missing']}")
    print(f"forbidden: {counts['forbidden']}")
    print(f"blocked: {counts['blocked']}")
    print(f"other: {counts['other']}")
    for key in ("ok", "missing", "forbidden", "blocked", "other"):
        if counts[key] == 0:
            continue
        print()
        print(f"{key}:")
        for result in grouped[key]:
            _print_result(result)


def _print_integrity(errors: tuple[str, ...]) -> None:
    print("integrity: failed")
    for error in errors:
        print(f"- {error}")


def _parse_timeout(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise _Usage() from None
    if value != value or value <= 0 or value > 120:
        raise _Usage()
    return value


def _parse_args(argv: list[str]) -> tuple[str, float]:
    mode = "default"
    timeout = 20.0
    seen_timeout = False
    index = 0
    modes = {"--check": "check", "--render": "render", "--self-test": "self-test", "--help": "help"}
    while index < len(argv):
        arg = argv[index]
        if arg in modes:
            if mode != "default":
                raise _Usage()
            mode = modes[arg]
            index += 1
            continue
        if arg == "--timeout":
            if seen_timeout or index + 1 >= len(argv):
                raise _Usage()
            timeout = _parse_timeout(argv[index + 1])
            seen_timeout = True
            index += 2
            continue
        raise _Usage()
    if seen_timeout and mode != "default":
        raise _Usage()
    return mode, timeout


def _fixture() -> tuple[domain.Meta, domain.Program, domain.Corpus]:
    home = domain.Source(
        url=domain.HttpUrl("https://example.invalid/nuages-imaginaire"),
        accessed=domain.AccessDate(2026, 10, 24),
    )
    cuda_page = domain.Source(
        url=domain.HttpUrl("https://example.invalid/nuages-cuda"),
        accessed=domain.AccessDate(2026, 10, 24),
    )
    program = domain.Program(
        id=domain.ProgramId("fr-nuages-imaginaire"),
        placement=domain.InFrance(city="Villefictive"),
        school="Université des Nuages Fictifs",
        program_name="Master imaginaire en brume distribuée",
        language=domain.Language.FR,
        credits=domain.Ects(value=120, source=home),
        home=home,
        core=domain.ListedCourses(
            items=(
                domain.Course(
                    short_fr="Algorithmique des cumulonimbus",
                    detail_fr="Cours fictif de tronc sur le découpage des nuages.",
                    source=home,
                    topics=(domain.TopicId("architecture"), domain.TopicId("mpi")),
                ),
            ),
            evidence=home,
        ),
        electives=domain.ListedCourses(
            items=(
                domain.Course(
                    short_fr="CUDA pour les licornes",
                    detail_fr="Électif fictif. Aucun GPU réel n'est décrit.",
                    source=cuda_page,
                    topics=(domain.TopicId("cuda"),),
                ),
            ),
            evidence=cuda_page,
        ),
        project=domain.ProjectUnknown(
            reason_fr="La page exemple ne décrit aucun mémoire.",
        ),
        hardware=domain.HardwareUnknown(
            reason_fr="La page exemple ne cite aucun cluster.",
        ),
        prerequisites=domain.PrerequisitesListed(
            items=(
                domain.Prerequisite(
                    short_fr="Licence fictive en météorologie",
                    detail_fr="Prérequis inventé pour l'exemple.",
                    source=home,
                ),
            ),
            evidence=home,
        ),
    )
    meta = domain.Meta(
        topics=(
            domain.Topic(domain.TopicId("architecture"), "Architecture"),
            domain.Topic(domain.TopicId("mpi"), "MPI"),
            domain.Topic(domain.TopicId("cuda"), "CUDA"),
            domain.Topic(domain.TopicId("openmp"), "OpenMP"),
        ),
        gaps=(),
        self_study=(),
        method_note_fr=("Note de méthode fictive.",),
        selection_note_fr=("Note de sélection fictive.",),
        takeaways_fr=("Conclusion fictive.",),
        role_need_fr=("Rôle fictif pour l'exemple.",),
    )
    return meta, program, domain.Corpus(meta=meta, programs=(program,))


def _self_test() -> int:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    meta, program, corpus = _fixture()
    pages = render(corpus)
    citations = domain.iter_sources(corpus)
    rows = domain.matrix(corpus)
    by_topic = {row.topic_id.value: row for row in rows}
    check(
        tuple(row.topic_id.value for row in rows)
        == ("architecture", "mpi", "cuda", "openmp"),
        "matrix topic order",
    )
    check(
        by_topic["architecture"].hits == (domain.TopicHit(program.id, domain.Strength.CORE),),
        "architecture strength",
    )
    check(
        by_topic["mpi"].hits == (domain.TopicHit(program.id, domain.Strength.CORE),),
        "mpi strength",
    )
    check(
        by_topic["cuda"].hits == (domain.TopicHit(program.id, domain.Strength.ELECTIVE),),
        "cuda strength",
    )
    check(by_topic["openmp"].hits == (), "openmp has no hit")
    france = pages["france.md"]
    check("Université des Nuages Fictifs" in france, "france names the school")
    check(
        "Non vérifié. La page exemple ne cite aucun cluster." in france,
        "france names the unverified cluster",
    )
    france_block = """## Université des Nuages Fictifs, Master imaginaire en brume distribuée

Identifiant : `fr-nuages-imaginaire`

### Page officielle

https://example.invalid/nuages-imaginaire consulté le 2026-10-24

### Lieu

Villefictive, France

### Langue

français

### Crédits

120 ECTS

https://example.invalid/nuages-imaginaire consulté le 2026-10-24

### Cours de tronc

https://example.invalid/nuages-imaginaire consulté le 2026-10-24

- Algorithmique des cumulonimbus. Cours fictif de tronc sur le découpage des nuages. Sujets : Architecture, MPI. https://example.invalid/nuages-imaginaire consulté le 2026-10-24.

### Électifs

https://example.invalid/nuages-cuda consulté le 2026-10-24

- CUDA pour les licornes. Électif fictif. Aucun GPU réel n'est décrit. Sujets : CUDA. https://example.invalid/nuages-cuda consulté le 2026-10-24.

### Projet ou mémoire

Non vérifié. La page exemple ne décrit aucun mémoire.

### Accès matériel

Non vérifié. La page exemple ne cite aucun cluster.

### Prérequis

https://example.invalid/nuages-imaginaire consulté le 2026-10-24

- Licence fictive en météorologie. Prérequis inventé pour l'exemple. https://example.invalid/nuages-imaginaire consulté le 2026-10-24.
"""
    check(france_block in france, "france section matches the worked example")
    extracted = _urls_in_pages(pages.values())
    cited = {citation.url.value for citation in citations}
    check(extracted == cited, "page urls equal iter_sources")
    try:
        _assert_page_urls(corpus, pages.values())
    except domain.CorpusError as err:
        check(False, "url gate " + "; ".join(err.errors))
    check(
        tuple(citation.field.value for citation in citations)
        == (
            "home",
            "credits",
            "core-evidence",
            "core-course",
            "electives-evidence",
            "elective-course",
            "prerequisites-evidence",
            "prerequisite",
        ),
        "citation fields",
    )
    distinct: list[str] = []
    for citation in citations:
        if citation.url.value not in distinct:
            distinct.append(citation.url.value)
    check(
        distinct
        == [
            "https://example.invalid/nuages-imaginaire",
            "https://example.invalid/nuages-cuda",
        ],
        "distinct citation order",
    )
    check(
        all(
            (citation.accessed.year, citation.accessed.month, citation.accessed.day)
            == (2026, 10, 24)
            for citation in citations
        ),
        "access dates are 2026-10-24",
    )
    try:
        domain.validate(corpus)
        check(False, "validate accepted the fixture")
    except domain.CorpusError as err:
        needed = {
            "france has 1 program, minimum is 6",
            "usa has 0 programs, minimum is 6",
            "chine has 0 programs, minimum is 5",
            "monde has 0 programs, minimum is 8",
            "missing required topic id performance",
            "missing required gap id ray",
        }
        missing = needed - set(err.errors)
        check(not missing, "validate missing " + ", ".join(sorted(missing)))
        check(tuple(err.errors) == tuple(sorted(err.errors)), "validate errors are sorted")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        raised = False
        try:
            _write_pages(corpus, root)
        except domain.CorpusError:
            raised = True
        names = [path.name for path in root.iterdir()]
        check(raised, "write_pages raises CorpusError")
        check(names == [], "write_pages creates no file")
    gone = domain.HttpUrl("https://example.invalid/gone")
    secret = domain.HttpUrl("https://example.invalid/secret")
    slow = domain.HttpUrl("https://example.invalid/slow")
    ok_url = domain.HttpUrl("https://example.invalid/ok")
    missing = UrlResult(gone, FetchMissing(404, gone.value), ())
    forbidden = UrlResult(secret, FetchForbidden(403, secret.value), ())
    blocked = UrlResult(slow, FetchBlocked(BlockKind.TIMEOUT, "timed out"), ())
    other = UrlResult(ok_url, FetchOther(500, ok_url.value), ())
    ok = UrlResult(ok_url, FetchOk(200, ok_url.value), ())
    check(exit_code(LinkReport((missing, forbidden))) == 1, "exit missing and forbidden")
    check(exit_code(LinkReport((forbidden,))) == 3, "exit forbidden")
    check(exit_code(LinkReport((blocked,))) == 4, "exit blocked")
    check(exit_code(LinkReport((other,))) == 4, "exit other")
    check(exit_code(LinkReport((ok,))) == 0, "exit ok")
    check(exit_code(LinkReport((missing, other))) == 1, "exit missing before other")
    check(
        output_pages()
        == ("index.md", "france.md", "usa.md", "chine.md", "monde.md", "synthese.md"),
        "output pages",
    )
    check(tuple(pages) == output_pages(), "render keys")
    for name, text in pages.items():
        check("\r" not in text and not text.startswith("\ufeff"), f"{name} encoding")
        check(text.endswith("\n") and not text.endswith("\n\n"), f"{name} trailing newline")
        check("Generated" not in text and "<!--" not in text, f"{name} has no generator banner")
    check(
        "Le corpus publié compte au moins 6 masters en France, 6 aux États-Unis, 5 en Chine et 8 dans le reste du monde."
        in pages["index.md"],
        "method minima",
    )
    check(
        "| Sujet | France | États-Unis | Chine | Monde | Total |\n| --- | --- | --- | --- | --- | --- |\n| Architecture | 1 | 0 | 0 | 0 | 1 |\n| MPI | 1 | 0 | 0 | 0 | 1 |\n| CUDA | 1 | 0 | 0 | 0 | 1 |\n| OpenMP | 0 | 0 | 0 | 0 | 0 |"
        in pages["synthese.md"],
        "frequency table",
    )
    check(
        "### Architecture\n\n- Université des Nuages Fictifs, Master imaginaire en brume distribuée. Tronc."
        in pages["synthese.md"],
        "architecture bullet",
    )
    check(
        "### CUDA\n\n- Université des Nuages Fictifs, Master imaginaire en brume distribuée. Électif."
        in pages["synthese.md"],
        "cuda bullet",
    )
    check("### OpenMP\n\nAucun programme." in pages["synthese.md"], "openmp empty row")
    index_row = (
        "| Université des Nuages Fictifs | Master imaginaire en brume distribuée | 120 ECTS | français | "
        "Algorithmique des cumulonimbus | Non vérifié. La page exemple ne cite aucun cluster. | "
        "[https://example.invalid/nuages-imaginaire](https://example.invalid/nuages-imaginaire) consulté le 2026-10-24<br>"
        "[https://example.invalid/nuages-cuda](https://example.invalid/nuages-cuda) consulté le 2026-10-24 |"
    )
    check(index_row in pages["index.md"], "index row")
    home = program.home
    absent_credits = replace(
        program,
        credits=domain.CreditsAbsent(note_fr="Aucun volume sur la page exemple", source=home),
    )
    absent_pages = render(domain.Corpus(meta, (absent_credits,)))
    check(
        "Non indiqué sur la page. Aucun volume sur la page exemple. "
        "https://example.invalid/nuages-imaginaire consulté le 2026-10-24."
        in absent_pages["france.md"],
        "credits absence sentence",
    )
    check(
        domain.Field.CREDITS
        in [citation.field for citation in domain.iter_sources(domain.Corpus(meta, (absent_credits,)))],
        "credits absence is cited",
    )
    unknown_credits = replace(
        program,
        credits=domain.CreditsUnknown(reason_fr="Volume absent du dossier."),
    )
    check(
        domain.Field.CREDITS
        not in [
            citation.field
            for citation in domain.iter_sources(domain.Corpus(meta, (unknown_credits,)))
        ],
        "unknown credits are not cited",
    )
    absent_core = replace(
        program,
        core=domain.CoursesAbsent(note_fr="Aucun tronc sur la page exemple", source=home),
    )
    core_fields = [
        citation.field.value
        for citation in domain.iter_sources(domain.Corpus(meta, (absent_core,)))
    ]
    check("core-evidence" in core_fields, "core absence is cited")
    check("core-course" not in core_fields, "core absence has no course citation")
    absent_project = replace(
        program,
        project=domain.ProjectAbsent(note_fr="Aucun mémoire sur la page exemple", source=home),
    )
    check(
        "project"
        in [
            citation.field.value
            for citation in domain.iter_sources(domain.Corpus(meta, (absent_project,)))
        ],
        "project absence is cited",
    )
    hardware = domain.Described(
        short_fr="Cluster fictif",
        detail_fr="Une machine inventée pour le test.",
        source=home,
        topics=(domain.TopicId("openmp"),),
    )
    hardware_only = replace(program, hardware=hardware)
    hardware_rows = {
        row.topic_id.value: row
        for row in domain.matrix(domain.Corpus(meta, (hardware_only,)))
    }
    check(
        hardware_rows["openmp"].hits == (domain.TopicHit(program.id, domain.Strength.HARDWARE),),
        "hardware-only topic counts",
    )
    muted = replace(
        program,
        language=domain.LanguageUnknown(reason_fr="La page ne nomme pas la langue."),
    )
    muted_page = render(domain.Corpus(meta, (muted,)))["france.md"]
    check("Non vérifié. La page ne nomme pas la langue." in muted_page, "language unknown")
    check("### Langue\n\nfrançais\n" not in muted_page, "language unknown is not French")
    for field in ("method_note_fr", "selection_note_fr", "takeaways_fr", "role_need_fr"):
        values = {
            "topics": meta.topics,
            "gaps": (),
            "self_study": (),
            "method_note_fr": meta.method_note_fr,
            "selection_note_fr": meta.selection_note_fr,
            "takeaways_fr": meta.takeaways_fr,
            "role_need_fr": meta.role_need_fr,
        }
        values[field] = ("Il y a 1 omission.",)
        try:
            domain.Meta(**values)
            check(False, f"digit accepted in {field}")
        except ValueError:
            pass
    try:
        domain.Gap(
            domain.GapId("ray"),
            "Ray",
            (),
            "Il en manque 2.",
        )
        check(False, "digit accepted in why_short_fr")
    except ValueError:
        pass
    gap = domain.Gap(
        domain.GapId("ray"),
        "Ray",
        (domain.TopicId("cuda"),),
        "Les pages ne traitent pas ce logiciel.",
    )
    step = domain.StudyStep(
        order=1,
        gap_ids=(gap.id,),
        body=domain.StudyResource(
            id=domain.StudyId("mooc-ray"),
            title="MOOC fictif",
            kind=domain.StudyKind.MOOC,
            source=home,
            why_for_profile_fr="Utile pour le rôle visé.",
        ),
    )
    gap_meta = replace(meta, gaps=(gap,), self_study=(step,))
    gap_page = render(domain.Corpus(gap_meta, (program,)))["synthese.md"]
    check(
        "CUDA. 1 programme sur 1 programme. France 1, États-Unis 0, Chine 0, Monde 0."
        in gap_page,
        "gap hit phrase",
    )
    check(
        "1. MOOC fictif. MOOC. https://example.invalid/nuages-imaginaire consulté le 2026-10-24. "
        "Lacunes : Ray. Utile pour le rôle visé."
        in gap_page,
        "study resource line",
    )
    none_step = domain.StudyStep(
        order=1,
        gap_ids=(gap.id,),
        body=domain.StudyNone(
            id=domain.StudyId("rien-ray"),
            title_fr="Pas de MOOC retenu",
            reason_fr="Aucune ressource gratuite ne couvre ce point.",
        ),
    )
    none_page = render(
        domain.Corpus(replace(meta, gaps=(gap,), self_study=(none_step,)), (program,))
    )["synthese.md"]
    check(
        "1. Pas de MOOC retenu. Aucune ressource gratuite retenue. "
        "Aucune ressource gratuite ne couvre ce point. Lacunes : Ray."
        in none_page,
        "study none line",
    )
    owner = program.id
    accessed = home.accessed
    sample = LinkReport(
        (
            UrlResult(
                gone,
                FetchMissing(404, gone.value),
                (
                    domain.Citation(gone, accessed, owner, domain.Field.HOME),
                ),
            ),
            UrlResult(
                secret,
                FetchForbidden(403, secret.value),
                (
                    domain.Citation(secret, accessed, owner, domain.Field.CORE_COURSE),
                ),
            ),
        )
    )
    buffer = StringIO()
    with redirect_stdout(buffer):
        _print_report(sample)
    expected_report = (
        "integrity: ok\n"
        "urls: 2\n"
        "ok: 0\n"
        "missing: 1\n"
        "forbidden: 1\n"
        "blocked: 0\n"
        "other: 0\n"
        "\n"
        "missing:\n"
        "- url: https://example.invalid/gone\n"
        "  http_status: 404\n"
        "  final_url: https://example.invalid/gone\n"
        "  citations:\n"
        "    - fr-nuages-imaginaire home\n"
        "\n"
        "forbidden:\n"
        "- url: https://example.invalid/secret\n"
        "  http_status: 403\n"
        "  final_url: https://example.invalid/secret\n"
        "  citations:\n"
        "    - fr-nuages-imaginaire core-course\n"
    )
    check(buffer.getvalue() == expected_report, "report shape")
    blocked_report = LinkReport(
        (
            UrlResult(
                slow,
                FetchBlocked(BlockKind.TIMEOUT, "timed out"),
                (domain.Citation(slow, accessed, owner, domain.Field.HARDWARE),),
            ),
        )
    )
    blocked_buffer = StringIO()
    with redirect_stdout(blocked_buffer):
        _print_report(blocked_report)
    blocked_text = blocked_buffer.getvalue()
    check("kind: timeout" in blocked_text, "blocked kind")
    check("detail: timed out" in blocked_text, "blocked detail")
    check("http_status" not in blocked_text, "blocked omits http_status")
    fetched: list[str] = []

    def fake_fetch(url: domain.HttpUrl) -> LinkStatus:
        fetched.append(url.value)
        return FetchOk(200, url.value)

    report = check_links(citations, fake_fetch)
    check(fetched == distinct, "fetch order")
    check(len(report.results[0].citations) == 6, "first url keeps every citation")
    check(len(report.results[1].citations) == 2, "second url keeps every citation")
    check("records" not in sys.modules, "self-test does not import records")
    if failures:
        print("self-test: failed")
        for failure in failures:
            print(failure)
        return 2
    print("self-test: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one legal command. Catch CorpusError, ValueError, and ImportError, print integrity: failed, and return 2.

    Let other exceptions propagate. Pass Path(__file__).resolve().parent
    as root for --render, --check, and the default command. The default
    command passes a one-argument fetch that calls fetch_url with the
    chosen timeout. After the pages match, it fetches the URL set printed
    on those pages, which must equal iter_sources.
    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        mode, timeout = _parse_args(argv)
    except _Usage:
        print(_USAGE)
        return 2
    if mode == "help":
        print(_USAGE)
        return 0
    try:
        if mode == "self-test":
            return _self_test()
        corpus = load_corpus()
        root = Path(__file__).resolve().parent
        if mode == "render":
            _write_pages(corpus, root)
            print("rendered:")
            for name in output_pages():
                print(f"- {name}")
            return 0
        if mode == "check":
            _require_match(corpus, root)
            print("integrity: ok")
            return 0
        _require_match(corpus, root)
        texts = [(root / name).read_text(encoding="utf-8") for name in output_pages()]
        _assert_page_urls(corpus, texts)
        report = check_links(
            domain.iter_sources(corpus),
            lambda cited: fetch_url(cited, timeout),
        )
        _print_report(report)
        return exit_code(report)
    except domain.CorpusError as err:
        _print_integrity(err.errors)
        return 2
    except ValueError as err:
        _print_integrity((str(err),))
        return 2
    except ImportError:
        _print_integrity(("records.py is missing",))
        return 2


if __name__ == "__main__":
    sys.exit(main())
