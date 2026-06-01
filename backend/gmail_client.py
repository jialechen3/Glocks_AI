import base64
from typing import Any

import httpx

from .models import PreparedEmail
from .normalization import (
    normalize_address,
    normalize_body_text,
    normalize_snippet,
    normalize_subject,
)


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailClientError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _decode_base64url(value: str | None) -> str | None:
    if not value:
        return None

    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(f"{value}{padding}").decode(
            "utf-8", errors="replace"
        )
    except Exception:
        return None


def _header_map(headers: list[dict[str, Any]] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for header in headers or []:
        name = header.get("name")
        value = header.get("value")
        if name and value:
            result[name.lower()] = value
    return result


def _extract_body_text(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    parts = payload.get("parts") or []

    if mime_type in {"text/plain", "text/html"} and body_data:
        return _decode_base64url(body_data)

    for part in parts:
        text = _extract_body_text(part)
        if text:
            return text

    return None


def _prepare_email(message: dict[str, Any]) -> PreparedEmail:
    payload = message.get("payload") or {}
    headers = _header_map(payload.get("headers"))

    return PreparedEmail(
        message_id=message.get("id", ""),
        thread_id=message.get("threadId"),
        label_ids=message.get("labelIds") or [],
        subject=normalize_subject(headers.get("subject")),
        from_address=normalize_address(headers.get("from")),
        to_address=normalize_address(headers.get("to")),
        date=headers.get("date"),
        snippet=normalize_snippet(message.get("snippet")),
        body_text=normalize_body_text(_extract_body_text(payload)),
    )


async def prepare_gmail_messages(
    access_token: str,
    max_results: int,
    query: str | None = None,
) -> list[PreparedEmail]:
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        list_response = await client.get(
            f"{GMAIL_API_BASE}/messages",
            headers=headers,
            params={
                "maxResults": max_results,
                **({"q": query} if query else {}),
            },
        )

        if list_response.status_code >= 400:
            raise GmailClientError(
                message=f"Gmail list request failed: {list_response.text}",
                status_code=list_response.status_code,
            )

        message_refs = list_response.json().get("messages", [])
        prepared_emails: list[PreparedEmail] = []

        for message_ref in message_refs:
            message_id = message_ref.get("id")
            if not message_id:
                continue

            detail_response = await client.get(
                f"{GMAIL_API_BASE}/messages/{message_id}",
                headers=headers,
                params={"format": "full"},
            )

            if detail_response.status_code >= 400:
                raise GmailClientError(
                    message=f"Gmail message request failed: {detail_response.text}",
                    status_code=detail_response.status_code,
                )

            prepared_emails.append(_prepare_email(detail_response.json()))

    return prepared_emails
