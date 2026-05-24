from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .gmail_client import GmailClientError, prepare_gmail_messages
from .models import GmailPrepareRequest, GmailPrepareResponse


app = FastAPI(
    title="Glooks AI Backend",
    version="0.1.0",
    description="FastAPI backend for preparing Gmail messages for AI workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/gmail/prepare", response_model=GmailPrepareResponse)
async def prepare_gmail_payload(request: GmailPrepareRequest) -> GmailPrepareResponse:
    try:
        emails = await prepare_gmail_messages(
            access_token=request.access_token,
            max_results=request.max_results,
            query=request.gmail_query,
        )
    except GmailClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return GmailPrepareResponse(
        user_command=request.user_command,
        total_emails=len(emails),
        emails=emails,
    )
