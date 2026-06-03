from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from email.utils import parseaddr

from .agent_models import (
    ActionType,
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    Intent,
    MessageGroup,
    RiskLevel,
    SuggestedAction,
)
from .normalization import normalize_body_text, normalize_snippet, normalize_subject


PROMOTION_KEYWORDS = {
    "sale",
    "discount",
    "offer",
    "promo",
    "deal",
    "coupon",
    "limited time",
    "shop now",
    "save big",
    "clearance",
    "free shipping",
}
NEWSLETTER_KEYWORDS = {
    "newsletter",
    "weekly",
    "daily",
    "digest",
    "roundup",
    "edition",
    "brief",
    "bulletin",
    "unsubscribe",
    "manage preferences",
}
MEETING_KEYWORDS = {
    "meeting",
    "sync",
    "agenda",
    "calendar",
    "project",
    "deadline",
    "client",
    "manager",
    "team",
    "follow up",
    "review",
    "standup",
}
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
}
PROMOTION_SENDERS = {
    "deals",
    "offers",
    "promo",
    "marketing",
    "sale",
    "shop",
    "store",
}
NEWSLETTER_SENDERS = {
    "newsletter",
    "digest",
    "updates",
    "brief",
    "bulletin",
}
GROUP_DESCRIPTIONS = {
    "Work": "Messages related to meetings, teams, projects, or company communication.",
    "Promotions": "Marketing and sales emails that are likely non-urgent.",
    "Newsletters": "Recurring updates, digests, and subscription-style messages.",
}


@dataclass(slots=True)
class ClassifiedEmail:
    message_id: str
    categories: set[str]
    has_unsubscribe_hint: bool


def analyze_request(request: AgentAnalyzeRequest) -> AgentAnalyzeResponse:
    intent = infer_intent(request.user_command)
    if not request.emails:
        return AgentAnalyzeResponse(
            intent=intent,
            summary="No emails were provided for analysis.",
            needs_confirmation=False,
            risk_level=RiskLevel.LOW,
            suggested_actions=[],
            groups=[],
            warnings=[],
        )

    classified = [classify_email(email) for email in request.emails]
    grouped_ids = build_groups(classified)
    groups = [
        MessageGroup(
            group_name=group_name,
            description=GROUP_DESCRIPTIONS[group_name],
            message_ids=message_ids,
        )
        for group_name, message_ids in grouped_ids.items()
        if message_ids
    ]

    suggested_actions = build_actions(intent, grouped_ids, classified)
    needs_confirmation = any(
        action.action_type
        in {
            ActionType.APPLY_LABEL,
            ActionType.ARCHIVE,
            ActionType.TRASH,
            ActionType.UNSUBSCRIBE_CANDIDATE,
        }
        for action in suggested_actions
    )
    risk_level = determine_risk_level(intent, suggested_actions)
    warnings = build_warnings(intent, suggested_actions)
    summary = build_summary(grouped_ids, suggested_actions)

    return AgentAnalyzeResponse(
        intent=intent,
        summary=summary,
        needs_confirmation=needs_confirmation,
        risk_level=risk_level,
        suggested_actions=suggested_actions,
        groups=groups,
        warnings=warnings,
    )


def infer_intent(user_command: str) -> Intent:
    text = user_command.lower()
    if any(keyword in text for keyword in {"delete", "trash", "remove"}):
        return Intent.DELETE_EMAILS
    if "unsubscribe" in text:
        return Intent.UNSUBSCRIBE_CANDIDATES
    if "mark" in text and "read" in text:
        return Intent.MARK_AS_READ
    if "newsletter" in text:
        return Intent.FIND_NEWSLETTERS
    if "summarize" in text or "summary" in text:
        return Intent.SUMMARIZE_EMAILS
    if "promotion" in text or "promo" in text or "clean" in text:
        return Intent.CLEAN_PROMOTIONS
    if any(keyword in text for keyword in {"organize", "label", "sort", "group"}):
        return Intent.ORGANIZE_INBOX
    return Intent.UNKNOWN


def classify_email(email) -> ClassifiedEmail:
    subject = normalize_subject(email.subject).lower()
    snippet = (normalize_snippet(email.snippet) or "").lower()
    body = (normalize_body_text(email.body_text) or "").lower()
    content = " ".join(part for part in {subject, snippet, body} if part)
    sender = extract_email_address(email.from_address)
    sender_local, _, sender_domain = sender.partition("@")

    has_unsubscribe_hint = any(
        hint in content for hint in {"unsubscribe", "manage preferences", "email preferences"}
    )

    is_newsletter = has_unsubscribe_hint or contains_any(content, NEWSLETTER_KEYWORDS) or contains_any(
        sender_local, NEWSLETTER_SENDERS
    )
    is_work = (
        sender_domain
        and sender_domain not in PUBLIC_EMAIL_DOMAINS
        and contains_any(content, MEETING_KEYWORDS)
    )
    is_promotion = (
        contains_any(content, PROMOTION_KEYWORDS)
        or contains_any(sender_local, PROMOTION_SENDERS)
        or "CATEGORY_PROMOTIONS" in email.label_ids
    )

    categories: set[str] = set()
    if is_work:
        categories.add("Work")
    if is_promotion and not is_work:
        categories.add("Promotions")
    if is_newsletter and not is_work:
        categories.add("Newsletters")

    return ClassifiedEmail(
        message_id=email.message_id,
        categories=categories,
        has_unsubscribe_hint=has_unsubscribe_hint,
    )


def build_groups(classified_emails: list[ClassifiedEmail]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in classified_emails:
        for category in sorted(item.categories):
            grouped[category].append(item.message_id)
    return {
        "Work": grouped.get("Work", []),
        "Promotions": grouped.get("Promotions", []),
        "Newsletters": grouped.get("Newsletters", []),
    }


def build_actions(
    intent: Intent,
    grouped_ids: dict[str, list[str]],
    classified_emails: list[ClassifiedEmail],
) -> list[SuggestedAction]:
    actions: list[SuggestedAction] = []

    if intent == Intent.ORGANIZE_INBOX:
        for group_name in ("Work", "Promotions", "Newsletters"):
            message_ids = grouped_ids[group_name]
            if message_ids:
                actions.append(
                    SuggestedAction(
                        action_type=ActionType.APPLY_LABEL,
                        target_message_ids=message_ids,
                        label_name=group_name,
                        reason=f"These messages match the {group_name.lower()} classification.",
                        confidence=0.85,
                    )
                )
        return actions

    if intent == Intent.CLEAN_PROMOTIONS and grouped_ids["Promotions"]:
        actions.append(
            SuggestedAction(
                action_type=ActionType.ARCHIVE,
                target_message_ids=grouped_ids["Promotions"],
                archive=True,
                reason="These messages contain promotional language and appear low priority.",
                confidence=0.84,
            )
        )
        return actions

    if intent == Intent.DELETE_EMAILS:
        target_ids = grouped_ids["Promotions"] + grouped_ids["Newsletters"]
        if target_ids:
            actions.append(
                SuggestedAction(
                    action_type=ActionType.TRASH,
                    target_message_ids=target_ids,
                    reason="These messages match low-priority promotional or newsletter patterns.",
                    confidence=0.8,
                )
            )
        else:
            actions.append(build_review_action(classified_emails))
        return actions

    if intent == Intent.UNSUBSCRIBE_CANDIDATES:
        unsubscribe_ids = [
            item.message_id for item in classified_emails if item.has_unsubscribe_hint and item.categories
        ]
        if unsubscribe_ids:
            actions.append(
                SuggestedAction(
                    action_type=ActionType.UNSUBSCRIBE_CANDIDATE,
                    target_message_ids=unsubscribe_ids,
                    reason="These messages include unsubscribe cues and look like recurring subscriptions.",
                    confidence=0.88,
                )
            )
        else:
            actions.append(build_review_action(classified_emails))
        return actions

    if intent == Intent.MARK_AS_READ:
        target_ids = grouped_ids["Promotions"] + grouped_ids["Newsletters"]
        if target_ids:
            actions.append(
                SuggestedAction(
                    action_type=ActionType.MARK_AS_READ,
                    target_message_ids=target_ids,
                    mark_read=True,
                    reason="These messages appear informational or promotional rather than urgent.",
                    confidence=0.82,
                )
            )
        return actions

    if intent == Intent.UNKNOWN and any(item.categories for item in classified_emails):
        actions.append(build_review_action(classified_emails))

    return actions


def build_review_action(classified_emails: list[ClassifiedEmail]) -> SuggestedAction:
    return SuggestedAction(
        action_type=ActionType.FLAG_FOR_REVIEW,
        target_message_ids=[item.message_id for item in classified_emails],
        reason="The request is higher risk than the current classifier can safely automate.",
        confidence=0.45,
    )


def determine_risk_level(intent: Intent, actions: list[SuggestedAction]) -> RiskLevel:
    if any(action.action_type in {ActionType.TRASH, ActionType.UNSUBSCRIBE_CANDIDATE} for action in actions):
        return RiskLevel.HIGH
    if any(action.action_type in {ActionType.APPLY_LABEL, ActionType.ARCHIVE, ActionType.MARK_AS_READ} for action in actions):
        return RiskLevel.MEDIUM
    if intent in {Intent.DELETE_EMAILS, Intent.UNSUBSCRIBE_CANDIDATES}:
        return RiskLevel.HIGH
    return RiskLevel.LOW


def build_warnings(intent: Intent, actions: list[SuggestedAction]) -> list[str]:
    warnings: list[str] = []
    if any(action.action_type in {ActionType.TRASH, ActionType.UNSUBSCRIBE_CANDIDATE} for action in actions):
        warnings.append("Destructive actions should require explicit user confirmation before execution.")
    if any(action.action_type == ActionType.APPLY_LABEL for action in actions):
        warnings.append("Confirm labels before applying them in bulk.")
    if any(action.action_type == ActionType.FLAG_FOR_REVIEW for action in actions):
        warnings.append("Low-confidence or high-risk requests should be reviewed before any action runs.")
    if intent == Intent.UNKNOWN and not actions:
        warnings.append("The request could not be mapped to a safe automated workflow.")
    return warnings


def build_summary(grouped_ids: dict[str, list[str]], actions: list[SuggestedAction]) -> str:
    counts = [
        f"{len(grouped_ids['Work'])} work emails" if grouped_ids["Work"] else None,
        f"{len(grouped_ids['Promotions'])} promotional emails" if grouped_ids["Promotions"] else None,
        f"{len(grouped_ids['Newsletters'])} newsletters" if grouped_ids["Newsletters"] else None,
    ]
    parts = [part for part in counts if part]
    if not parts:
        return "No strong work, promotional, or newsletter patterns were detected."
    summary = "Found " + ", ".join(parts[:-1] + ([parts[-1]] if len(parts) == 1 else [f"and {parts[-1]}"]))
    if any(action.action_type == ActionType.FLAG_FOR_REVIEW for action in actions):
        return summary + ". Some requested actions were flagged for manual review."
    return summary + "."


def contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def extract_email_address(raw_address: str | None) -> str:
    _, email_address = parseaddr(raw_address or "")
    return email_address.lower()
