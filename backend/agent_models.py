from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .models import PreparedEmail


class Intent(StrEnum):
    ORGANIZE_INBOX = "organize_inbox"
    CLEAN_PROMOTIONS = "clean_promotions"
    SUMMARIZE_EMAILS = "summarize_emails"
    FIND_NEWSLETTERS = "find_newsletters"
    MARK_AS_READ = "mark_as_read"
    DELETE_EMAILS = "delete_emails"
    UNSUBSCRIBE_CANDIDATES = "unsubscribe_candidates"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(StrEnum):
    APPLY_LABEL = "apply_label"
    MARK_AS_READ = "mark_as_read"
    ARCHIVE = "archive"
    TRASH = "trash"
    UNSUBSCRIBE_CANDIDATE = "unsubscribe_candidate"
    SUMMARIZE_THREAD = "summarize_thread"
    FLAG_FOR_REVIEW = "flag_for_review"


class SuggestedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: ActionType
    target_message_ids: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)
    label_name: str | None = None
    mark_read: bool | None = None
    archive: bool | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    unsubscribe_link: str | None = None


class MessageGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    message_ids: list[str] = Field(default_factory=list)


class AgentAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_command: str = Field(min_length=1)
    emails: list[PreparedEmail] = Field(default_factory=list)


class AgentAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    summary: str = Field(min_length=1)
    needs_confirmation: bool
    risk_level: RiskLevel
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    groups: list[MessageGroup] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
