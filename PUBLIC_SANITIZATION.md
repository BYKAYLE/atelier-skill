# Public Sanitization Policy

This repository is the public Atelier skill bundle. It must stay safe to install
on a new machine and safe to publish on GitHub.

## Allowed

- Public workflow instructions.
- Public validation scripts.
- Public examples that use placeholders.
- Project-agnostic SOT templates.
- Defensive security guidance and low-side-effect verification checks.

## Not Allowed

- Real API keys, tokens, passwords, cookies, refresh tokens, private keys, or
  Keychain item names.
- Personal profiles, private preference memory, private chat transcripts, or
  runtime session logs.
- Machine-specific absolute paths.
- Production host credentials, internal deployment automation, or private
  database instructions.
- Auto-installers for private plugins or private skills.

## Release Checklist

Run this before tagging or releasing:

```bash
./scripts/public_safety_check.sh
git status --short
```

The safety check intentionally flags suspicious terms. Review each hit. A hit is
acceptable only when it is generic documentation about how to avoid secrets, not
an actual secret or private identifier.
