# Glooks Mail AI Assistant

Glooks Mail AI Assistant is a Chrome extension project for managing Gmail with natural-language instructions. The goal is to let a user talk to an agent and ask it to do useful inbox work such as deleting spam, organizing messages into categories, or preparing email context for more advanced automation.

## What it does

- Authenticates the user with Google through Chrome Identity.
- Requests Gmail access with the `gmail.modify` scope.
- Provides a simple popup where the user can type commands such as:
  - "Delete spam emails from the last 7 days"
  - "Categorize my inbox into work, personal, and promotions"
  - "Find newsletters and mark them as read"

## Current project status

This repository currently contains:

- a React popup frontend powered by Vite
- a Chrome extension shell for OAuth and popup hosting
- a FastAPI backend for Gmail extraction and AI preparation

The AI execution layer is not fully implemented yet. Right now, the project authenticates with Gmail and is structured so you can add either:

- direct Gmail API calls from the extension, or
- a secure backend service that receives short-lived tokens and performs inbox actions

## Why this project is useful

Email is high-friction work. This project aims to reduce inbox overload by turning manual email cleanup into a conversational workflow. Instead of clicking through filters and labels, a user can describe the outcome they want and let the assistant handle repetitive tasks.

## Security notes

This project handles Gmail access, so security matters.

- Do not commit OAuth tokens, `.env` files, private keys, or backend secrets.
- Google OAuth client IDs are not secrets, but client secrets and refresh tokens are.
- Access tokens should never be logged to the console or stored permanently in the extension.
- If you add a backend, only send tokens over HTTPS and validate the token audience and scopes server-side.
- Keep the requested OAuth scope as narrow as possible for the product behavior you need.

See [SECURITY.md](SECURITY.md) for a short checklist before publishing or deploying.

## Local setup

1. Clone the repository.
2. Install frontend dependencies with `npm install`.
3. Build the extension with `npm run build`.
4. Open Chrome and go to `chrome://extensions`.
5. Enable Developer Mode.
6. Click `Load unpacked` and select the `dist` folder.
7. Start the backend if you want live Gmail extraction with `python -m uvicorn backend.main:app --reload`.

## Frontend structure

- `src/` contains the React popup app
- `public/` contains extension files that Vite copies into `dist/`
- `popup.html` is the Vite HTML entry for the popup
- `backend/` contains the FastAPI service
- `docs/` contains planning and interface specs such as the AI agent response contract

## Suggested next steps

- Build the natural-language command parser and action planner.
- Add Gmail API message retrieval and safe action previews.
- Add a backend only if you need heavier AI orchestration or secure server-side processing.
- Introduce confirmation flows before destructive actions like permanent delete.
- Add tests and a mock inbox workflow before wide release.

## Repository safety

This repo was prepared for public GitHub publishing with basic safeguards:

- common secret files are ignored
- access token logging was removed
- security guidance is included for future development

## License

Add a license before distributing commercially or inviting open-source contributions.
