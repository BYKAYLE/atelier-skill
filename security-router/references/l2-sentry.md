---
name: sentry-security-review
version: "1.0.2"
description: |
  Use when reviewing code for HIGH-confidence security vulnerabilities with data flow tracking and framework-aware analysis.
  Minimizes false positives through 3-tier confidence system. Designed for auto-invocation via security-router.
  Source: github.com/getsentry/skills (CC-BY-SA-4.0 License)
---

# Security Review Skill

Identify exploitable security vulnerabilities in code. Report only **HIGH CONFIDENCE** findings.

## Scope: Research vs. Reporting

- **Report on**: Only the specific file, diff, or code provided
- **Research**: The ENTIRE codebase to build confidence before reporting

Before flagging any issue, MUST research:
- Where does this input actually come from? (Trace data flow)
- Is there validation/sanitization elsewhere?
- How is this configured? (settings, config files, middleware)
- What framework protections exist?

**Do NOT report issues based solely on pattern matching.**

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** | Vulnerable pattern + attacker-controlled input confirmed | **Report** with severity |
| **MEDIUM** | Vulnerable pattern, input source unclear | **Note** as "Needs verification" |
| **LOW** | Theoretical, best practice, defense-in-depth | **Do not report** |

## Do Not Flag

- Test files, dead code, documentation strings
- Patterns using **constants** or **server-controlled configuration**
- Code paths requiring prior authentication (note auth requirement instead)

### Server-Controlled Values (NOT Attacker-Controlled)
| Source | Example | Why Safe |
|--------|---------|----------|
| Django settings | `settings.API_URL` | Set via config/env at deployment |
| Environment variables | `os.environ.get('DATABASE_URL')` | Deployment configuration |
| Config files | `config.yaml`, `app.config['KEY']` | Server-side files |
| Hardcoded values | `BASE_URL = "https://api.internal"` | Compile-time constants |

### Framework-Mitigated Patterns
| Pattern | Why Usually Safe |
|---------|-----------------|
| Django `{{ variable }}` | Auto-escaped by default |
| React `{variable}` | Auto-escaped by default |
| ORM `User.objects.filter(id=input)` | Parameterized queries |

**Only flag when:** `{{ var|safe }}`, `mark_safe(user_input)`, `dangerouslySetInnerHTML`, `.raw()` with interpolation

## Review Process

### 1. Detect Context → Load relevant references
### 2. Load Language Guide (by file extension/imports)
### 3. Load Infrastructure Guide (if applicable)
### 4. Research Before Flagging — trace data flow, check settings vs user input
### 5. Verify Exploitability — confirm attacker-controlled input
### 6. Report HIGH Confidence Only

## Severity Classification

| Severity | Examples |
|----------|----------|
| **Critical** | RCE, SQL injection to data, auth bypass, hardcoded secrets |
| **High** | Stored XSS, SSRF to metadata, IDOR to sensitive data |
| **Medium** | Reflected XSS, CSRF on state-changing, path traversal |
| **Low** | Missing headers, verbose errors, weak algorithms in non-critical |

## Quick Patterns — Always Flag

```
eval(user_input)           # Any language
pickle.loads(user_data)    # Python
yaml.load(user_data)       # Python (not safe_load)
unserialize($user_data)    # PHP
shell=True + user_input    # Python subprocess
innerHTML = userInput       # DOM XSS
password = "hardcoded"     # Secrets
```

## Quick Patterns — Check Context First

```
requests.get(settings.API_URL)      # SAFE: server-controlled
requests.get(request.GET['url'])    # FLAG: user-controlled
hashlib.md5(file_content)           # SAFE: checksum
hashlib.md5(password)               # FLAG: password hashing
```

## Output Format

```markdown
## Security Review: [File/Component Name]

### Summary
- **Findings**: X (Y Critical, Z High, ...)
- **Risk Level**: Critical/High/Medium/Low
- **Confidence**: High/Mixed

### Findings
#### [VULN-001] [Vulnerability Type] (Severity)
- **Location**: `file.py:123`
- **Confidence**: High
- **Issue**: [What the vulnerability is]
- **Impact**: [What an attacker could do]
- **Evidence**: [Vulnerable code snippet]
- **Fix**: [How to remediate]

### Needs Verification
#### [VERIFY-001] [Potential Issue]
- **Location**: `file.py:456`
- **Question**: [What needs to be verified]
```
