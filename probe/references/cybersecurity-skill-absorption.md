# Cybersecurity Skill Absorption for Probe

Source: `mukul975/Anthropic-Cybersecurity-Skills` at commit `0f429d0f96ee`, Apache-2.0.

## Source Assessment

- The upstream library is a broad AI-agent cybersecurity knowledge base: 754 skills, 4,216 files, 2,384 Markdown files, and GitHub API metadata showing roughly 10k stars at review time.
- Its strongest design pattern is progressive disclosure: scan metadata first, then load only the few matching skills.
- Each skill usually carries `When to Use`, `Prerequisites`, workflow steps, verification/output sections, references, and a helper script.
- The raw frontmatter needs normalization before routing. README says 26 domains, but the cloned metadata has 45 raw `subdomain` labels because of variants such as `identity-access-management`, `identity-and-access-management`, `zero-trust`, and `zero-trust-architecture`.
- About 120 skill names are offensive or dual-use by wording alone. These are useful for authorized validation design, but Probe must not silently become a red-team executor.

## Absorption Principle

Probe remains an independent verification gate. It should not become `security-router`, `pentest-router`, or an exploit launcher.

The upstream skills are absorbed as:

1. A security domain index for selecting the right verification lens.
2. Runtime QA assertions that strengthen Probe's current Playwright evidence loop.
3. Report vocabulary that maps findings to security families without requiring the user to choose a security framework.
4. Guardrails that preserve Probe's existing isolation contract.

## Probe Capability Upgrades

Existing Probe capability | Upgrade absorbed from upstream
--- | ---
Combinatorial browser testing | Add security state combinations such as auth state, role, viewport, locale, and route class.
Network/console capture | Capture all response headers for header, cookie, mixed-content, and sensitive-URL checks.
LLM judge | Use upstream skill metadata to narrow judge prompts to the relevant domain rather than asking generic visual questions.
Markdown report | Add security-specific evidence vocabulary: checked URL, missing headers, cookie attributes, sensitive parameter samples.
Release gate | Treat critical security assertion failures as release-blocking evidence, not cosmetic QA.

## What Probe Should Handle Directly

These fit Probe because they are evidence-driven, low-side-effect checks against the same browser surface Probe already controls:

- HTTP security headers: CSP, HSTS, `X-Content-Type-Options`, frame protection, referrer policy, permissions policy.
- Cookie attributes: `Secure`, `HttpOnly`, `SameSite`.
- Mixed-content detection on HTTPS pages.
- Sensitive-looking URL query parameters in captured requests.
- Basic API/UI authorization smoke tests when the plan provides separate roles or seeded cookies.
- Phishing/brand checks only as passive analysis of provided emails, domains, or pages.

## What Probe Must Not Absorb Directly

These stay behind explicit security tooling, authorization, and isolation:

- Credential dumping, password cracking, C2 setup, exploit execution, post-exploitation, wireless cracking, social engineering, or phishing campaign operation.
- Network-wide scanning or third-party target probing without a declared authorized scope.
- Malware execution or sandbox detonation outside a dedicated lab.
- Any workflow that requires privileged access, real customer data, live financial systems, or destructive changes.

Route those to `security-router` or `pentest-router` with explicit scope and keep Probe as the independent verifier of outputs and safe runtime surfaces.

## Current Integration Files

- `references/cybersecurity-skills-index.json`: distilled metadata index of the 754 upstream skills.
- `scripts/checks.py`: adds security assertions.
- `scripts/runner.py`: records response headers needed by those assertions.
- `templates/security-probe-plan.example.yml`: starter plan for a web security smoke probe.

## Recommended Routing Rules

Intent | Primary owner | Probe role
--- | --- | ---
Code security review | `security-router` | Verify fixed UI/API behavior after remediation.
Runtime web security smoke | `Probe` | Run `securityHeaders`, `cookieSecurity`, `noMixedContent`, and `noSensitiveUrlParams`.
Full penetration test | `pentest-router` | Consume final artifacts and verify remediation evidence.
Incident or phishing triage | Security skill/reference | Use Probe only for passive page/email/domain evidence collection.
Release with UI/API surface | `Release` | Invoke Probe as Phase 6.5 gate; security failures block report-up.

## Index Use

When a security-oriented probe is requested:

1. Search `cybersecurity-skills-index.json` by target type and keywords.
2. Load at most three matching upstream skill references from the cloned or installed source.
3. Extract only defensive prerequisites, verification criteria, and output vocabulary.
4. Convert them into Probe plan assertions or LLM-judge prompts.
5. Do not run upstream `scripts/agent.py` helpers automatically.

