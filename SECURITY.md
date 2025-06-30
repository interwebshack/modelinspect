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

## 🔐 Digital Signature Policy

All release container images published to GHCR are signed using [Cosign](https://docs.sigstore.dev/cosign/).  

To verify a signature:

```bash
cosign verify --key cosign.pub ghcr.io/interwebshack/ai-forensics:v1.0.0
```
You can retrieve the public verification key here:
* `/keys/cosign.pub`
* [View Raw](https://raw.githubusercontent.com/interwebshack/ai-forensics/main/keys/cosign.pub)

**🔏 Public Key Fingerprint (SHA-256)**
```bash
7f:53:ae:96:3e:12:9d:45:8c:fa:4a:e1:91:fe:91:0a:e8:bc:af:f9:... (truncated)
```
We rotate keys annually. Previous public keys and verification history are archived in `/keys/`.
To generate the fingerprint:

```bash
openssl dgst -sha256 cosign.pub
```
