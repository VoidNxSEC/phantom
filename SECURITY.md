# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

We take the security of Phantom seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Email**: marcosfpina@protonmail.com

Please include the following information:

- Type of vulnerability
- Full path of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### What to Expect

- **Initial Response**: Within 48 hours, we'll acknowledge receipt of your report
- **Status Updates**: We'll keep you informed about progress toward a fix
- **Fix Timeline**: We aim to release patches within 90 days for critical issues
- **Credit**: With your permission, we'll publicly acknowledge your contribution

### Preferred Languages

We prefer all communications to be in **English** or **Portuguese**.

---

## Security Update Process

1. **Vulnerability is reported** privately to maintainers
2. **Maintainers confirm** the issue and determine severity
3. **Patch is developed** in a private branch
4. **Security advisory** is prepared
5. **Patch is released** with security advisory
6. **Public disclosure** 7 days after patch release

---

## Security Best Practices for Users

### When Using Phantom

#### 1. Environment Variables
Never commit secrets to Git:

```bash
# ❌ BAD: Hardcoding keys in code
OPENAI_API_KEY = "sk-proj-..."

# ✅ GOOD: Using environment variables
export OPENAI_API_KEY="sk-proj-..."
export DEEPSEEK_API_KEY="sk-..."
```

#### 2. Input Validation
Always validate user-provided file paths:

```python
from pathlib import Path

def safe_read_file(user_path: str) -> str:
    # Resolve to absolute path
    path = Path(user_path).resolve()

    # Ensure it's within allowed directory
    allowed_dir = Path("/safe/directory").resolve()
    if not str(path).startswith(str(allowed_dir)):
        raise ValueError("Path outside allowed directory")

    return path.read_text()
```

#### 3. LLM Prompts
Be cautious with user input in LLM prompts:

```python
# ❌ BAD: Direct user input injection
prompt = f"Analyze this: {user_input}"

# ✅ GOOD: Sanitize and validate
from phantom.pipeline import DataSanitizer

sanitizer = DataSanitizer()
clean_input = sanitizer.remove_pii(user_input)
prompt = f"Analyze this: {clean_input}"
```

#### 4. API Endpoints
Secure your Phantom API:

```python
from fastapi import Depends, HTTPException
from phantom.api import app

@app.post("/process")
async def process_document(
    file: UploadFile,
    api_key: str = Depends(verify_api_key)  # Add authentication
):
    # Rate limiting
    # Input validation
    # Size limits
    ...
```

#### 5. Dependency Management
Keep dependencies up-to-date:

```bash
# Check for vulnerabilities
pip-audit

# For Rust dependencies
cargo audit

# Update flake.lock (NixOS)
nix flake update
```

---

## Known Security Considerations

### 1. LLM Prompt Injection
**Risk**: Malicious users may craft inputs to manipulate LLM outputs

**Mitigation**:
- Sanitize user inputs before LLM processing
- Use structured output schemas (Pydantic)
- Implement output validation
- Set reasonable token limits

### 2. File System Access
**Risk**: Arbitrary file read/write through path traversal

**Mitigation**:
- Validate all file paths
- Use `pathlib.Path.resolve()` to normalize paths
- Restrict operations to sandboxed directories
- Never execute user-provided code

### 3. Resource Exhaustion
**Risk**: Processing large files can exhaust memory/GPU

**Mitigation**:
- Implement file size limits
- Use VRAM monitoring (`phantom.tools.vram_calculator`)
- Enable auto-throttling
- Set processing timeouts

### 4. Dependency Vulnerabilities
**Risk**: Third-party packages may contain vulnerabilities

**Mitigation**:
- Regular `pip-audit` and `cargo audit` runs
- Automated dependency updates (Dependabot)
- Pin specific versions in production
- Monitor security advisories

### 5. Secrets in Logs
**Risk**: API keys or sensitive data logged accidentally

**Mitigation**:
- Never log API keys or tokens
- Sanitize error messages
- Use structured logging
- Redact sensitive fields

---

## Security Features in Phantom

### Built-in Security

1. **PII Detection & Removal**
   ```python
   from phantom.pipeline import DataSanitizer

   sanitizer = DataSanitizer()
   clean_text = sanitizer.remove_pii(text)
   ```

2. **Input Validation**
   - Pydantic models for all data structures
   - Type checking with mypy
   - Runtime validation

3. **File Classification**
   - Magic byte verification
   - File integrity checks (SHA256, BLAKE3)
   - Malware pattern detection

4. **Resource Limits**
   - VRAM monitoring
   - Processing timeouts
   - Automatic throttling

5. **Audit Logging**
   - Comprehensive operation logs
   - Forensic-grade audit trails
   - Timestamp verification

---

## Security Checklist for Developers

When contributing code, ensure:

- [ ] No hardcoded secrets or API keys
- [ ] Input validation for all user-provided data
- [ ] Output sanitization before returning to user
- [ ] Error messages don't leak sensitive information
- [ ] File operations are restricted to safe directories
- [ ] No arbitrary code execution (eval, exec, etc.)
- [ ] Dependencies are up-to-date
- [ ] Tests include security edge cases
- [ ] Documentation includes security considerations

---

## Security Testing

### Automated Security Checks

Our CI/CD pipeline includes:

```bash
# Python security audit
pip-audit

# Rust security audit
cargo audit

# Dependency vulnerability scanning
safety check

# Static analysis
bandit -r src/

# Secret detection
detect-secrets scan
```

### Manual Security Testing

When testing features:

1. **Input Fuzzing**: Test with malicious inputs
2. **Path Traversal**: Try `../../../etc/passwd`
3. **Injection**: Test prompt injection attacks
4. **Rate Limiting**: Verify API rate limits work
5. **Authentication**: Test auth bypass attempts

---

## Responsible Disclosure

We kindly ask security researchers to:

- **Allow us time** to fix vulnerabilities before public disclosure (90 days)
- **Avoid exploiting** the vulnerability beyond proof-of-concept
- **Not access** or modify other users' data
- **Not perform** denial-of-service attacks

### Hall of Fame

We recognize responsible security researchers who help us:

- [Your name here] - Issue description (Month Year)

---

## Security Resources

### For Users

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [MITRE ATT&CK for LLMs](https://atlas.mitre.org/)
- [LLM Security Best Practices](https://llmsecurity.net/)

### For Developers

- [Secure Coding Guidelines](https://www.securecoding.cert.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Rust Security Guidelines](https://anssi-fr.github.io/rust-guide/)

---

## Questions?

For security-related questions that are not vulnerabilities:

- **GitHub Discussions**: Tag with "security"
- **Email**: marcosfpina@protonmail.com

For vulnerabilities, **always use private email**.

---

## License

This security policy is part of Phantom and is licensed under the MIT License.

---

**Last Updated**: January 2026
**Version**: 2.0.0
