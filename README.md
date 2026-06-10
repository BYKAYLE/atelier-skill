# Atelier Skill

Public skill bundle for Atelier.

This repository contains the public skills used by Atelier, Stella, Stella Factory,
Probe, Release, and local agent orchestration workflows.

## Included

- Stella and Stella Factory operating skills
- Agent orchestration and autonomous development skills
- Probe, release, audit, frontend, writing, and workflow skills
- Public skill references and scripts that do not require personal credentials

## Excluded

- `deploy-pilot` — private deployment automation
- `kmd` — private company database skill
- `bk-wiki` — private company knowledge wiki
- `night-lab` — internal R&D orchestrator (internal infrastructure endpoints)
- All runtime state (`SOT/`, `sessions/`, `daily/`, logs, caches)
- Personal API keys, tokens, passwords, keychain entry names, and internal credential templates

Private deployment automation remains in the private `BYKAYLE/kansic-skill`
repository.

## Installation

Atelier installs this bundle from the Plugin & Skills tab. The installer copies
the public skill folders into local skill roots without deleting existing local
skills.

---
Last updated: 2026-06-10 — 41 skills (Opus 4.8 alignment pass: hook guard fixes, stale tool refs cleaned, stella slimmed 1049→888 lines)
