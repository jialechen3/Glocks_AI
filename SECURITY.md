# Security Checklist

Use this checklist before pushing changes or connecting a backend.

## Safe to publish

- `manifest.json` may contain a Google OAuth client ID. That is generally public metadata, not a secret.
- UI, extension logic, and non-secret configuration defaults are safe to publish.

## Never commit

- OAuth access tokens
- refresh tokens
- Google client secrets
- `.env` files with private credentials
- private keys, PEM files, or service account JSON files

## Development guidance

- Remove debug logs that print tokens or mailbox contents.
- Prefer short-lived access tokens and avoid writing them to disk.
- Use HTTPS for any backend communication.
- Add user confirmation before destructive inbox operations.
- Limit Gmail permissions to the minimum scopes required.
- Review pull requests for accidental secret exposure before merging.

## If a secret is exposed

1. Revoke or rotate the credential immediately.
2. Remove the secret from the codebase and commit history if needed.
3. Update `.gitignore` or configuration structure to prevent a repeat.
4. Re-test authentication using a new credential.
