# Security Policy

The AI Forensics team and community take security bugs in `ai-forensics` seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

## 🔒 Supported Versions

The following versions of `ai-forensics` are actively supported and receive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅                 |
| < 1.0   | ❌                 |

## 🛡️ Reporting Security Issues  

To report a security issue, please use the GitHub Security Advisory ["Report a Vulnerability"](https://github.com/interwebshack/ai-forensics/security/advisories/new) tab.

The AI Forensics team will send a response indicating the next steps in handling your report. After the initial reply to your report, the security team will keep you informed of the progress towards a fix and full announcement, and may ask for additional information or guidance.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Affected version(s)  
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)  
- Full paths of source file(s) related to the manifestation of the issue  
- The location of the affected source code (tag/branch/commit or direct URL)  
- Any special configuration required to reproduce the issue  
- Step-by-step instructions to reproduce the issue  
- Proof-of-concept or exploit code (if possible)  
- Impact of the issue, including how an attacker might exploit the issue  
- Suggested fix (if known)  

This information will help us triage your report more quickly.  

Report security bugs in third-party modules to the person or team maintaining the module.

## 🔐 Disclosure Policy

We follow responsible disclosure. Critical vulnerabilities will be patched before public disclosure. If you are a researcher or user with early insights, we will credit you in the changelog unless anonymity is requested.  

## 💬 Preferred Languages

We prefer all communications to be in English.

## 🔐 Additional Security Info  

- Signed source code and artifact integrity enforcement using [Cosign](https://docs.sigstore.dev/cosign/)  
- GitHub Actions enforce fingerprint verification for source files and bundles  
- Container images are scanned with Trivy and Grype during CI

For implementation details, see [SECURITY-IMPLEMENTATION.md](./docs/security/SECURITY-IMPLEMENTATION.md).