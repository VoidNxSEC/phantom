# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | ✅        |
| < 2.0   | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability in Phantom, please report it
**privately** — do not open a public issue.

1. Email: security@voidnix.dev
2. Or open a **private** GitHub advisory on this repository

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Severity estimate (Critical / High / Medium / Low)

Response time target: 48 hours for initial acknowledgement.

## Security Measures

- **Dependency scanning**: `pip-audit` and `safety` run on every CI push
- **Secret scanning**: `trufflehog` scans every commit for leaked credentials
- **Input validation**: All API endpoints use Pydantic models with strict typing
- **No secrets in repo**: `.env` files and credentials are gitignored;
  SOPS is recommended for secret management
- **Pre-commit hooks**: `ruff`, trailing-whitespace, large-file guard, merge-conflict detection
- **TLS in transit**: Phantom API is intended to run behind a TLS-terminating proxy in production

## Out of Scope

- Vulnerabilities in third-party dependencies are reported upstream
- Issues in archived/experimental code (`.archive/`) are not tracked

## License

Apache License 2.0 — see [LICENSE](LICENSE).
