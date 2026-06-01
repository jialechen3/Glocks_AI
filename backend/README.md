# FastAPI Backend

This backend accepts a Gmail access token from the Chrome extension, fetches message data from the Gmail API, and returns a normalized email payload that is easier to feed into AI pipelines.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Start the server:

```bash
uvicorn backend.main:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## Current endpoint

- `POST /api/gmail/prepare`

Example request body:

```json
{
  "access_token": "ya29....",
  "user_command": "Analyze my unread messages and organize them into structured labels.",
  "gmail_query": "is:unread",
  "max_results": 10
}
```

## Phase 1 data contract

The prepare layer now normalizes Gmail message data before any analyzer uses it:

- missing subjects become `(no subject)`
- sender and recipient addresses are normalized
- snippets and body text are whitespace-cleaned
- HTML bodies are reduced to plain text
- long bodies are truncated to a safe model-friendly size

The future AI analyzer schema is defined in `backend/agent_models.py` so the request and response contract is stable before model logic is added.
