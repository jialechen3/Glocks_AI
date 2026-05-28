# AI Agent Response Structure

This document defines the response contract for the next AI agent stage in Glooks Mail AI Assistant.

The goal is to make the frontend, backend, and model layer all speak the same language before execution logic is added.

## Purpose

The AI agent should not directly delete, label, or archive emails. It should analyze prepared Gmail data and return a structured recommendation payload that the backend can validate and the frontend can preview.

This creates a 3-step flow:

1. `prepare`
2. `analyze`
3. `execute`

## Recommended endpoint

`POST /api/agent/analyze`

## Input shape

The agent endpoint should receive:

```json
{
  "user_command": "Analyze my unread messages and organize them into structured labels.",
  "emails": [
    {
      "message_id": "196f0c123abc",
      "thread_id": "196f0c123abd",
      "label_ids": ["INBOX", "UNREAD"],
      "subject": "Team sync moved to 4pm",
      "from_address": "manager@company.com",
      "to_address": "me@gmail.com",
      "date": "Tue, 27 May 2026 09:14:00 -0400",
      "snippet": "We need to move today's sync...",
      "body_text": "We need to move today's sync to 4pm."
    }
  ]
}
```

## Output shape

The agent should return JSON in this format:

```json
{
  "intent": "organize_inbox",
  "summary": "Found 6 promotional emails, 2 work emails, and 2 newsletters.",
  "needs_confirmation": true,
  "risk_level": "medium",
  "suggested_actions": [
    {
      "action_type": "apply_label",
      "target_message_ids": ["196f0c123abc"],
      "label_name": "Work",
      "reason": "The sender is from the user's work domain and the content is meeting-related."
    }
  ],
  "groups": [
    {
      "group_name": "Work",
      "description": "Messages related to meetings, managers, and company communication.",
      "message_ids": ["196f0c123abc"]
    }
  ],
  "warnings": [
    "No destructive actions should run without explicit user confirmation."
  ]
}
```

## Top-level fields

### `intent`

High-level interpretation of the user's request.

Suggested enum values:

- `organize_inbox`
- `clean_promotions`
- `summarize_emails`
- `find_newsletters`
- `mark_as_read`
- `delete_emails`
- `unsubscribe_candidates`
- `unknown`

### `summary`

A short natural-language explanation of what the agent found.

Guidelines:

- Keep it to 1 to 3 sentences
- Make it readable in the extension popup
- Do not include raw message bodies

### `needs_confirmation`

Boolean flag indicating whether a user must explicitly approve the proposed actions before execution.

Use `true` for:

- delete
- trash
- archive
- unsubscribe
- bulk relabeling

### `risk_level`

Suggested enum values:

- `low`
- `medium`
- `high`

Recommended meaning:

- `low`: safe read-only or reversible actions
- `medium`: bulk organization or state changes
- `high`: destructive or hard-to-reverse actions

### `suggested_actions`

An array of structured action proposals.

Each action should be self-contained and executable by backend logic without additional model interpretation.

### `groups`

Optional grouping output to help the UI render categories like Work, Promotions, Personal, Newsletters, or Follow Up.

### `warnings`

Optional list of user-visible warnings or backend safety notes.

## Suggested action object

Each item in `suggested_actions` should follow this shape:

```json
{
  "action_type": "apply_label",
  "target_message_ids": ["196f0c123abc"],
  "label_name": "Work",
  "reason": "The sender is from the user's work domain and the content is meeting-related."
}
```

### Required fields

- `action_type`
- `target_message_ids`
- `reason`

### Optional fields

- `label_name`
- `mark_read`
- `archive`
- `confidence`
- `unsubscribe_link`

## Suggested `action_type` values

- `apply_label`
- `mark_as_read`
- `archive`
- `trash`
- `unsubscribe_candidate`
- `summarize_thread`
- `flag_for_review`

## Group object

Each item in `groups` can follow this shape:

```json
{
  "group_name": "Promotions",
  "description": "Marketing and sales emails that are likely non-urgent.",
  "message_ids": ["196f0c200001", "196f0c200002"]
}
```

This is mainly useful for frontend rendering and future inbox analytics.

## Safety rules

The agent response should follow these rules:

1. Never assume the model can execute actions itself.
2. Never return free-form instructions that the backend has to interpret loosely.
3. Every executable action must map to a backend function.
4. Destructive actions must set `needs_confirmation` to `true`.
5. If confidence is low, return `flag_for_review` instead of a destructive action.

## Backend validation expectations

Before the backend accepts an agent response:

- validate the JSON with Pydantic
- verify every `target_message_ids` value exists in the prepared email set
- verify action types are supported
- reject unknown top-level fields if strict mode is enabled

## Example responses

### Example 1: inbox organization

```json
{
  "intent": "organize_inbox",
  "summary": "Found 4 work emails, 3 promotions, and 3 newsletters.",
  "needs_confirmation": true,
  "risk_level": "medium",
  "suggested_actions": [
    {
      "action_type": "apply_label",
      "target_message_ids": ["m1", "m2", "m3", "m4"],
      "label_name": "Work",
      "reason": "These messages are from work contacts and contain meeting or task language."
    },
    {
      "action_type": "apply_label",
      "target_message_ids": ["m5", "m6", "m7"],
      "label_name": "Promotions",
      "reason": "These messages contain marketing language, sale offers, and promo senders."
    }
  ],
  "groups": [
    {
      "group_name": "Work",
      "description": "Team and manager communication.",
      "message_ids": ["m1", "m2", "m3", "m4"]
    },
    {
      "group_name": "Promotions",
      "description": "Discounts, campaigns, and shopping emails.",
      "message_ids": ["m5", "m6", "m7"]
    }
  ],
  "warnings": [
    "Confirm labels before applying them in bulk."
  ]
}
```

### Example 2: destructive cleanup

```json
{
  "intent": "delete_emails",
  "summary": "Found 8 likely promotional emails that match the cleanup request.",
  "needs_confirmation": true,
  "risk_level": "high",
  "suggested_actions": [
    {
      "action_type": "trash",
      "target_message_ids": ["m10", "m11", "m12"],
      "reason": "These messages are low-priority promotions and match the user's cleanup request."
    },
    {
      "action_type": "unsubscribe_candidate",
      "target_message_ids": ["m10", "m12"],
      "reason": "These senders appear to be recurring marketing sources."
    }
  ],
  "groups": [],
  "warnings": [
    "Trash and unsubscribe actions should require explicit user confirmation."
  ]
}
```

## Recommended next implementation

After this doc, the next backend pieces should be:

1. `backend/agent_models.py`
2. `POST /api/agent/analyze`
3. a mock rule-based analyzer
4. frontend rendering for `summary`, `warnings`, and `suggested_actions`

Once that contract feels stable, the mock analyzer can be replaced with a real LLM call.

## Delivery plan

### Recommended language and framework

Use the existing stack instead of introducing a second backend language.

- Backend AI layer: `Python`
- API framework: `FastAPI`
- Data contracts and validation: `Pydantic`
- Gmail and external API access: `httpx`
- Frontend UI: `React` with `Vite`

### Why this stack

`Python + FastAPI` is the best fit for the AI layer here because:

- the backend already uses Python and FastAPI
- Pydantic makes model input and output validation strict and easy to maintain
- AI orchestration, prompt building, and JSON schema validation are simpler in Python than adding a second Node service
- Gmail data preparation is already implemented in Python, so the AI layer can reuse the same models directly

Do not move the AI orchestration into the browser extension. Keep the extension focused on auth, preview, and user approval. Put all AI calls and safety checks in the backend.

### Phase 1: stabilize the data contract

Goal: make sure prepared Gmail data is clean, consistent, and ready for model use.

Build next:

1. Add `backend/agent_models.py` with:
   - `AgentAnalyzeRequest`
   - `AgentAnalyzeResponse`
   - `SuggestedAction`
   - `MessageGroup`
2. Add strict enums for:
   - `intent`
   - `risk_level`
   - `action_type`
3. Normalize prepared email fields before analysis:
   - missing subject handling
   - sender parsing
   - safe body truncation
   - optional HTML cleanup

### Phase 2: ship a rule-based analyzer first

Goal: make the product useful before adding an LLM dependency.

Build next:

1. Create `backend/agent_service.py`
2. Add a deterministic analyzer that can:
   - detect promotions by sender and keywords
   - detect work emails by domain and meeting language
   - detect newsletters by recurring formats and unsubscribe hints
3. Return the exact response format defined in this document
4. Add unit tests for expected classifications and safety behavior

This gives you a safe baseline for UI work and backend execution mapping.

### Phase 3: add LLM analysis behind the same contract

Goal: improve classification quality without changing the frontend contract.

Recommended approach:

- Keep `POST /api/agent/analyze` unchanged
- Add an LLM-backed analyzer implementation behind an internal service boundary
- Pass only prepared and minimized email data into the model
- Force structured JSON output that matches `AgentAnalyzeResponse`

Suggested backend structure:

- `backend/agent_models.py`
- `backend/agent_service.py`
- `backend/rule_analyzer.py`
- `backend/llm_analyzer.py`
- `backend/prompt_builder.py`

### LLM integration recommendation

For AI hooking to the data, use:

- `Python` for orchestration
- a server-side LLM SDK client
- `Pydantic` models as the source of truth for request and response schemas

Implementation pattern:

1. `prepare_gmail_messages()` gathers Gmail data
2. `prompt_builder.py` converts that data into a compact analysis payload
3. `llm_analyzer.py` sends the request to the model
4. the response is validated into `AgentAnalyzeResponse`
5. unsupported or low-confidence actions are converted to `flag_for_review`

### Phase 4: frontend approval flow

Goal: make AI suggestions reviewable before any Gmail action runs.

Build next:

1. Render `summary`
2. Render grouped results
3. Show warnings and risk level clearly
4. Let the user approve or reject each suggested action
5. Send only approved actions to a future execute endpoint

### Phase 5: execution layer and safety

Goal: connect approved AI actions back to Gmail safely.

Build next:

1. Add `POST /api/agent/execute`
2. Map each `action_type` to an explicit backend function
3. Re-check message IDs against the prepared result set
4. Block destructive actions unless confirmation is present
5. Log all executed actions for auditability

### Recommended implementation order

1. `agent_models.py`
2. rule-based `agent_service.py`
3. `POST /api/agent/analyze`
4. frontend preview UI
5. LLM-backed analyzer
6. `POST /api/agent/execute`

### Architecture decision

For this project, the strongest path is:

- `React` in the extension for UX
- `Python + FastAPI` in the backend for Gmail prep, AI analysis, and execution
- one shared response contract enforced with `Pydantic`

Avoid splitting AI logic across both `Node` and `Python`. One backend language will keep the data flow simpler, cheaper to maintain, and much easier to debug.
