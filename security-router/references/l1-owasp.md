---
name: owasp-security
version: "1.0.0"
description: |
  Use when applying OWASP 2025 security knowledge to code, including Top 10:2025, ASVS 5.0, and Agentic AI Security patterns.
  Provides 20+ language-specific vulnerability patterns. Acts as a security textbook for safe coding.
  Designed to be auto-invoked via security-router rather than called directly.
---

# OWASP Security Best Practices Skill

Apply these security standards when writing or reviewing code.

## Quick Reference: OWASP Top 10:2025

| # | Vulnerability | Key Prevention |
|---|---------------|----------------|
| A01 | Broken Access Control | Deny by default, enforce server-side, verify ownership |
| A02 | Security Misconfiguration | Harden configs, disable defaults, minimize features |
| A03 | Supply Chain Failures | Lock versions, verify integrity, audit dependencies |
| A04 | Cryptographic Failures | TLS 1.2+, AES-256-GCM, Argon2/bcrypt for passwords |
| A05 | Injection | Parameterized queries, input validation, safe APIs |
| A06 | Insecure Design | Threat model, rate limit, design security controls |
| A07 | Auth Failures | MFA, check breached passwords, secure sessions |
| A08 | Integrity Failures | Sign packages, SRI for CDN, safe serialization |
| A09 | Logging Failures | Log security events, structured format, alerting |
| A10 | Exception Handling | Fail-closed, hide internals, log with context |

## Security Code Review Checklist

### Input Handling
- [ ] All user input validated server-side
- [ ] Using parameterized queries (not string concatenation)
- [ ] Input length limits enforced
- [ ] Allowlist validation preferred over denylist

### Authentication & Sessions
- [ ] Passwords hashed with Argon2/bcrypt (not MD5/SHA1)
- [ ] Session tokens have sufficient entropy (128+ bits)
- [ ] Sessions invalidated on logout
- [ ] MFA available for sensitive operations

### Access Control
- [ ] Authorization checked on every request
- [ ] Using object references user cannot manipulate
- [ ] Deny by default policy
- [ ] Privilege escalation paths reviewed

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] TLS for all data in transit
- [ ] No sensitive data in URLs/logs
- [ ] Secrets in environment/vault (not code)

### Error Handling
- [ ] No stack traces exposed to users
- [ ] Fail-closed on errors (deny, not allow)
- [ ] All exceptions logged with context
- [ ] Consistent error responses (no enumeration)

## Secure Code Patterns

### SQL Injection Prevention
```python
# UNSAFE
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# SAFE
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Command Injection Prevention
```python
# UNSAFE
os.system(f"convert {filename} output.png")
# SAFE
subprocess.run(["convert", filename, "output.png"], shell=False)
```

### Password Storage
```python
# UNSAFE
hashlib.md5(password.encode()).hexdigest()
# SAFE
from argon2 import PasswordHasher
PasswordHasher().hash(password)
```

### Access Control
```python
# UNSAFE
@app.route('/api/user/<user_id>')
def get_user(user_id):
    return db.get_user(user_id)
# SAFE
@app.route('/api/user/<user_id>')
@login_required
def get_user(user_id):
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)
    return db.get_user(user_id)
```

### Fail-Closed Pattern
```python
# UNSAFE - Fail-open
def check_permission(user, resource):
    try:
        return auth_service.check(user, resource)
    except Exception:
        return True  # DANGEROUS!
# SAFE - Fail-closed
def check_permission(user, resource):
    try:
        return auth_service.check(user, resource)
    except Exception as e:
        logger.error(f"Auth check failed: {e}")
        return False
```

## Agentic AI Security (OWASP 2026)

| Risk | Description | Mitigation |
|------|-------------|------------|
| ASI01: Goal Hijack | Prompt injection alters agent objectives | Input sanitization, goal boundaries, behavioral monitoring |
| ASI02: Tool Misuse | Tools used in unintended ways | Least privilege, fine-grained permissions, validate I/O |
| ASI03: Privilege Abuse | Credential escalation across agents | Short-lived scoped tokens, identity verification |
| ASI04: Supply Chain | Compromised plugins/MCP servers | Verify signatures, sandbox, allowlist plugins |
| ASI05: Code Execution | Unsafe code generation/execution | Sandbox execution, static analysis, human approval |
| ASI06: Memory Poisoning | Corrupted RAG/context data | Validate stored content, segment by trust level |
| ASI07: Agent Comms | Spoofing between agents | Authenticate, encrypt, verify message integrity |
| ASI08: Cascading Failures | Errors propagate across systems | Circuit breakers, graceful degradation, isolation |
| ASI09: Trust Exploitation | Social engineering via AI | Label AI content, user education, verification steps |
| ASI10: Rogue Agents | Compromised agents acting maliciously | Behavior monitoring, kill switches, anomaly detection |

## ASVS 5.0 Key Requirements

### Level 1 (All Applications)
- Passwords minimum 12 characters, check against breached lists
- Rate limiting on authentication, Session tokens 128+ bits, HTTPS everywhere

### Level 2 (Sensitive Data)
- MFA for sensitive operations, Cryptographic key management
- Comprehensive security logging, Input validation on all parameters

### Level 3 (Critical Systems)
- HSM for keys, Threat modeling documentation
- Advanced monitoring, Penetration testing validation

## Language-Specific Security Quirks (Top 10)

### JavaScript/TypeScript
**Risks:** Prototype pollution, XSS, eval injection
**Watch for:** `eval()`, `innerHTML`, `document.write()`, `__proto__`

### Python
**Risks:** Pickle RCE, format string injection, shell injection
**Watch for:** `pickle`, `eval()`, `exec()`, `os.system()`, `shell=True`

### Java
**Risks:** Deserialization RCE, XXE, JNDI injection
**Watch for:** `ObjectInputStream`, `Runtime.exec()`, XML parsers

### C#
**Risks:** BinaryFormatter RCE, SQL injection, path traversal
**Watch for:** `BinaryFormatter`, `TypeNameHandling.All`

### PHP
**Risks:** Type juggling, file inclusion, object injection
**Watch for:** `==` vs `===`, `include/require`, `unserialize()`

### Go
**Risks:** Race conditions, template injection, slice bounds
**Watch for:** Goroutine data races, `template.HTML()`, `unsafe`

### Ruby
**Risks:** Mass assignment, YAML deserialization, regex DoS
**Watch for:** `YAML.load`, `Marshal.load`, `eval`, `.permit!`

### Rust
**Risks:** Unsafe blocks, FFI boundaries, integer overflow in release
**Watch for:** `unsafe`, FFI calls, `.unwrap()` on untrusted input

### Swift/Kotlin
**Risks:** Force unwrapping, platform interop null safety
**Watch for:** `!` operator, Java interop nulls

### C/C++
**Risks:** Buffer overflow, use-after-free, format string
**Watch for:** `strcpy`, `sprintf`, `gets`, manual memory management

## When to Apply
- Writing authentication/authorization code
- Handling user input or external data
- Implementing cryptography or password storage
- Reviewing code for security vulnerabilities
- Building AI agent systems
- Working with third-party dependencies
