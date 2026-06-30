# Atelier Skill

Public skill bundle for Atelier.

This repository contains the public skills used by Atelier, Stella, Stella Factory,
Probe, Release, and local agent orchestration workflows.

Version: `0.2.0`
Updated: `2026-06-30`

## Included

- Stella and Stella Factory operating skills
- Agent orchestration and autonomous development skills
- Probe, release, audit, frontend, writing, and workflow skills
- Public skill references and scripts that do not require personal credentials

## Excluded

- Private deployment automation
- Private company database skills
- Private company knowledge wiki skills
- Internal R&D orchestrators and infrastructure endpoints
- All runtime state (`SOT/`, `sessions/`, `daily/`, logs, caches)
- Personal API keys, tokens, passwords, keychain entry names, and internal credential templates

Private deployment automation remains in the private skill repository and is not
mirrored here.

## Public Sanitization

The public bundle is sanitized before release. See
[`PUBLIC_SANITIZATION.md`](PUBLIC_SANITIZATION.md) and run:

```bash
./scripts/public_safety_check.sh
```

## Installation

Atelier installs this bundle from the Plugin & Skills tab. The installer copies
the public skill folders into local skill roots without deleting existing local
skills.

---
Last updated: 2026-06-30 — 41 skills (public Stella sanitized, private/API/runtime content excluded)
