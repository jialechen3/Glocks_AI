from pydantic import BaseModel, Field


class PreparedEmail(BaseModel):
    message_id: str
    thread_id: str | None = None
    label_ids: list[str] = Field(default_factory=list)
    subject: str | None = None
    from_address: str | None = None
    to_address: str | None = None
    date: str | None = None
    snippet: str | None = None
    body_text: str | None = None


class GmailPrepareRequest(BaseModel):
    access_token: str = Field(min_length=1)
    user_command: str = Field(min_length=1)
    gmail_query: str | None = None
    max_results: int = Field(default=10, ge=1, le=50)


class GmailPrepareResponse(BaseModel):
    user_command: str
    total_emails: int
    emails: list[PreparedEmail]
