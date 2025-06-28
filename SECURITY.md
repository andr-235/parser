# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** create public issues for security vulnerabilities.

### Private Reporting
1. Use GitHub Security Advisory: Repository → Security → Advisories
2. Email: security@example.com (replace with actual email)
3. Expected response: 48 hours

### Disclosure Timeline
- Initial response: 48 hours
- Assessment: 5 business days
- Fix development: Varies by severity
- Public disclosure: After fix deployment

### What to Include
- Type of issue (e.g. buffer overflow, SQL injection, XSS, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Measures

### Code Security
- All dependencies are regularly updated via Dependabot
- Code is scanned with CodeQL for security vulnerabilities
- Secret scanning is enabled to prevent credential leaks
- All commits are signed with GPG keys

### Infrastructure Security
- VK API tokens are stored as GitHub secrets
- Database credentials use environment variables
- Docker containers run with non-root users
- All network communication uses TLS/SSL

### Development Security
- Branch protection rules require code reviews
- All CI/CD workflows use minimal permissions
- Security tests are part of the CI pipeline
- Regular security audits are conducted
