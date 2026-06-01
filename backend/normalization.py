import re
from email.utils import parseaddr
from html import unescape


MAX_SNIPPET_LENGTH = 500
MAX_BODY_LENGTH = 4000
MISSING_SUBJECT = "(no subject)"

_WHITESPACE_RE = re.compile(r"\s+")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize_whitespace(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = _WHITESPACE_RE.sub(" ", value).strip()
    return normalized or None


def truncate_text(value: str | None, limit: int) -> str | None:
    normalized = normalize_whitespace(value)
    if normalized is None:
        return None
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(limit - 3, 0)].rstrip() + "..."


def strip_html(html: str | None) -> str | None:
    if html is None:
        return None

    cleaned = _SCRIPT_STYLE_RE.sub(" ", html)
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    return normalize_whitespace(unescape(cleaned))


def normalize_subject(subject: str | None) -> str:
    return normalize_whitespace(subject) or MISSING_SUBJECT


def normalize_address(address: str | None) -> str | None:
    normalized = normalize_whitespace(address)
    if normalized is None:
        return None

    name, email_address = parseaddr(normalized)
    parsed_email = normalize_whitespace(email_address)
    parsed_name = normalize_whitespace(name)

    if parsed_name and parsed_email:
        return f"{parsed_name} <{parsed_email.lower()}>"
    if parsed_email:
        return parsed_email.lower()
    return normalized


def normalize_body_text(body_text: str | None) -> str | None:
    if body_text is None:
        return None

    maybe_html = "<" in body_text and ">" in body_text
    cleaned = strip_html(body_text) if maybe_html else normalize_whitespace(body_text)
    return truncate_text(cleaned, MAX_BODY_LENGTH)


def normalize_snippet(snippet: str | None) -> str | None:
    return truncate_text(snippet, MAX_SNIPPET_LENGTH)
