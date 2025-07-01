# GitHub Actions Workflows for AI Forensics

This document describes each automated workflow in this repository, the conditions under which it runs, and its purpose in ensuring the integrity, security, and reliability of the codebase and container images.

---

## ✅ Summary Table

| Workflow Name       | File                     | Trigger                     | Description                                |
|---------------------|--------------------------|-----------------------------|--------------------------------------------|
| Pytest + Coverage   | `test.yml`               | Push/PR → `main`            | Run unit tests, generate `coverage.xml`    |
| Matrix Testing      | `test-matrix.yml`        | Push/PR → `main`            | Run tests on multiple Python versions      |
| SonarCloud Scan     | `sonarqube.yml`          | After `test.yml` success    | Static analysis + Quality Gate             |
| Build Container     | `build-container.yml`    | Push/PR → `main`            | Build and tag `:latest` image              |
| Release & Signing   | `release.yml`            | Push tag: `v*`              | Build + tag image, sign with Cosign        |
| Verify Signature    | `verify.yml`             | After `release.yml`         | Verify signature of release images         |

---

## 🧪 `test.yml` – Pytest + Coverage Report

**Trigger:** On push and pull request to `main` branch.

- Installs dependencies via Poetry
- Runs `pytest` with coverage
- Uploads `coverage.xml` as a GitHub artifact for reuse by SonarCloud

> Artifact shared: `coverage-report/coverage.xml`

---

## 🧪 `test-matrix.yml` – Multi-Python Testing

**Trigger:** On push and pull request to `main` branch.

- Runs unit tests against Python 3.10 and 3.11
- Confirms compatibility before release

---

## 🔎 `sonarqube.yml` – SonarCloud Quality Scan

**Trigger:** On `workflow_run` (when `test.yml` completes successfully)

- Downloads `coverage.xml` from test job
- Runs static analysis with SonarCloud
- Enforces Quality Gate policy (optional fail)

> Requires GitHub secret: `SONAR_TOKEN`  
> SonarCloud project must exist: `yourgithubuser_ai-forensics`

---

## 🐳 `build-container.yml` – Container Build on Push

**Trigger:** On push and pull request to `main`

- Builds container using BuildKit
- Tags image as `ghcr.io/yourgithubuser/ai-forensics:latest`
- Optional: Add vulnerability scans (Trivy, Grype) in future steps

---

## 🚀 `release.yml` – Tagged Release Build + Cosign Signing

**Trigger:** On tag push (`v*`, e.g., `v1.0.0`)

- Builds and pushes container tagged as `:v1.0.0` and `:latest`
- Signs both tags using [Sigstore Cosign](https://docs.sigstore.dev/cosign/)
- Cosign key is retrieved from GitHub Secrets

> 🔐 Required secrets:

| Secret Name         | Description                            |
|---------------------|----------------------------------------|
| `COSIGN_PRIVATE_KEY`| Contents of your `cosign.key` file     |
| `COSIGN_PASSWORD`   | Password used when generating the key  |

---

## 🔐 `verify.yml` – Signature Verification

**Trigger:** After `release.yml` succeeds (manual or automatic)

- Verifies the Cosign signature of the built image
- Can be extended to enforce signature policy before promotion

> Uses the public key file `cosign.pub`, checked into the `/keys` folder (or stored in secrets)

---

## 📁 Secrets Used Across Workflows

| Secret Name         | Used By           | Purpose                                  |
|---------------------|-------------------|------------------------------------------|
| `SONAR_TOKEN`       | `sonarqube.yml`   | Authenticate with SonarCloud             |
| `COSIGN_PRIVATE_KEY`| `release.yml`     | Used to sign container image             |
| `COSIGN_PASSWORD`   | `release.yml`     | Unlock Cosign private key                |

---

## 🔑 Code Signing Policy

AI Forensics enforces digital signatures on all released artifacts:

- **Every tagged image is signed** using Cosign and published to GHCR.
- **Signature verification** is performed in `verify.yml` using the public key `cosign.pub`.
- Future workflows may enforce signature verification **prior to deployment** or promotion.

> Cosign public key should be published in [`SECURITY.md`](./SECURITY.md) or `/keys/cosign.pub`.

---

## 🧪 Development Notes

- All Python code is typed and tested with `pytest`
- CI jobs are isolated by concern (test, scan, build)
- Inter-job dependencies use GitHub Artifacts (not `needs`)
- Reusable composite actions may be added in future for common setup

---

## 🔗 Related Files

- [SECURITY.md](./SECURITY.md) – Reporting vulnerabilities and signature policy
- [CONTRIBUTING.md](./CONTRIBUTING.md) – Dev setup, test instructions
- [`sonar-project.properties`](./sonar-project.properties) – SonarCloud config

---

## 🔐 Recommended Triggers and Events

| Event               | Use Case                             | Workflow                                 |
| ------------------- | ------------------------------------ | ---------------------------------------- |
| `push` to `main`    | Routine development + CI             | `sign-verify.yml`, `build-container.yml` |
| `pull_request`      | Validate contributor code integrity  | `sign-verify.yml`                        |
| `push` tag `v*.*.*` | Production release                   | `tag-release.yml`                        |
| `workflow_dispatch` | Manual integrity build or deployment | All workflows (optional)                 |
| `deployment`        | Trigger before prod deployment       | `cosign-verify.yml`                      |

Need to refactor these two tables to the actual workflow
| Workflow Name           | Function                                     | Tools Involved                      |
| ----------------------- | -------------------------------------------- | ----------------------------------- |
| `lint.yml`              | Code style & quality                         | `ruff` or `flake8`, `black`, `mypy` |
| `sast.yml`              | Static security analysis                     | `bandit`, GitHub CodeQL             |
| `openssf-scorecard.yml` | OpenSSF Scorecard compliance & hygiene check | `ossf/scorecard-action`             |

---

## 🧩 Workflow Implementation Order

| Step | Action                           | Workflow              |
| ---- | -------------------------------- | --------------------- |
| 1    | Developer pushes code            | `sign-verify.yml`     |
| 2    | Maintainer tags release          | `tag-release.yml`     |
| 3    | Build container (auto or manual) | `build-container.yml` |
| 4    | Deploy to prod                   | `cosign-verify.yml`   |

---

## Continue Development

* 🔐 Separate GitHub environments for staging/prod?
* 📋 Pre-commit Git hooks to warn if manifest is outdated?
* 🛡 A status badge for “Integrity Verified” in your README?

