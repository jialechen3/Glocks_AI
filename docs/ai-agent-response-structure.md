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
