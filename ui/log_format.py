"""Parses parser console messages into structured entries for the UI."""

import html
import re
from typing import TypedDict

from core.i18n import banner_words


_BANNER_WORDS = "|".join(re.escape(word) for word in banner_words())
_BANNER_RE = re.compile(
    rf"^-{{2,}}\s*(?:{_BANNER_WORDS})\s+(?P<marketplace>\S+)\s*-{{2,}}$"
)
_PROBLEM_RE = re.compile(r"^\|\|\|\s*(?P<message>.+?)\s*\|\|\|$", re.S)
_DONE_RE = re.compile(r"^<{2,}\s*(?P<message>.+?)\s*>{2,}$", re.S)
_NOTE_RE = re.compile(r"^-{2,}(?P<message>[^-].*?)-{2,}$", re.S)
_FIELD_RE = re.compile(r"^-\s+(?P<key>[^:\n]+):\s*(?P<value>.*)$", re.S)
_ERRORBANG_RE = re.compile(r"^!{2,}\s*(?P<message>.+?)\s*!{2,}$", re.S)

_URL_RE = re.compile(r"https?://[^\s<>\"]+")


class LogEntry(TypedDict):
    kind: str
    marketplace: str
    key: str
    value: str
    message: str


def linkify(text: str) -> str:
    """Escapes HTML and turns URLs into clickable links."""

    result: list[str] = []
    position = 0
    for match in _URL_RE.finditer(text):
        result.append(html.escape(text[position : match.start()]))
        url = match.group(0)
        escaped = html.escape(url, quote=True)
        result.append(f'<a href="{escaped}">{escaped}</a>')
        position = match.end()
    result.append(html.escape(text[position:]))
    return "".join(result).replace("\n", "<br>")


def parse_entry(text: str) -> LogEntry:
    """Parses a single journal entry (ANSI codes already stripped)."""

    entry: LogEntry = {
        "kind": "plain",
        "marketplace": "",
        "key": "",
        "value": "",
        "message": "",
    }
    stripped = text.strip()

    if match := _BANNER_RE.match(stripped):
        entry["kind"] = "banner"
        entry["marketplace"] = match.group("marketplace")
        entry["message"] = html.escape(f"New order {entry['marketplace']}")
        return entry

    if match := _PROBLEM_RE.match(stripped):
        entry["kind"] = "problem"
        entry["message"] = linkify(match.group("message"))
        return entry

    if match := _ERRORBANG_RE.match(stripped):
        entry["kind"] = "problem"
        entry["message"] = linkify(match.group("message"))
        return entry

    if match := _DONE_RE.match(stripped):
        entry["kind"] = "done"
        entry["message"] = linkify(match.group("message"))
        return entry

    if match := _FIELD_RE.match(stripped):
        entry["kind"] = "field"
        entry["key"] = match.group("key").strip()
        entry["value"] = linkify(match.group("value").strip())
        return entry

    if match := _NOTE_RE.match(stripped):
        entry["kind"] = "note"
        entry["message"] = linkify(match.group("message").strip())
        return entry

    entry["message"] = linkify(stripped)
    return entry
