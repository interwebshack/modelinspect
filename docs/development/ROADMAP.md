# 🧭 AI Forensics Roadmap

_This roadmap outlines the major milestones, planned features, and architectural enhancements for the AI Forensics tool. This tool provides binary-level inspection and policy enforcement for machine learning model artifacts such as `.safetensors`, `.pth`, and `.gguf`, with support for provenance, attestation, and compliance._

---

## 🎯 Vision

AI Forensics aims to provide a modular, secure, and extensible toolchain to **analyze, validate, and attest** ML model binaries. It is designed for environments where **security, compliance, and explainability** are paramount, including **classified or air-gapped networks**.

---

## 🗺️ Roadmap Overview

| Milestone                         | Status     | Description                                                                 |
|----------------------------------|------------|-----------------------------------------------------------------------------|
| ✅ Core Format Parsers            | Completed  | Parsers for `.safetensors`, `.pth`, and `.gguf` with binary inspection     |
| ✅ Rule Engine + Policy File      | Completed  | Configurable YAML-based rule engine for policy enforcement                 |
| ✅ Rich Console UI                | Completed  | Colorful, readable CLI output using `rich`                                 |
| ✅ Violation & Metadata Model     | Completed  | Standardized violation and metadata schema                                 |
| ✅ JSON/HTML Report Export        | Completed  | Export results for human and machine readability                           |
| ✅ Pickle Inspection in .pth      | Completed  | Parse embedded pickles inside `.pth` safely without `torch.load()`         |
| ✅ Entropy & Magic Byte Scanners  | Completed  | Binary heuristic scanners to detect embedded archives or payloads          |
| ✅ SBOM Generation (CycloneDX/SPDX) | Completed | Generate and optionally sign SBOMs for each artifact                       |
| ✅ Provenance & Lineage Metadata  | Completed  | Capture artifact origin, source URL, and fingerprinting metadata           |
| ✅ Artifact Bundling (ZIP)        | Completed  | Export all evidence and reports into a single zip bundle                   |
| ✅ Cosign Signature Support       | Completed  | Sign SBOM and metadata reports with Sigstore/Cosign                        |
| ✅ Cosign Transparency Log        | Completed  | Integration with Rekor for immutable signing log                           |
| 🔄 Multi-threaded Scanning        | In Progress| Improve performance of binary analysis on large files                      |
| 🔜 UI Dashboard                   | Planned    | Web-based frontend to upload artifacts and view reports                    |
| 🔜 Plugin Architecture            | Planned    | Allow third-party format parsers and rules                                 |
| 🔜 YARA Integration               | Planned    | Support user-defined YARA rules for model payload analysis                 |
| 🔜 Cloud-Hosted Integration       | Planned    | Integrate with Harbor, S3, GitLab, etc. for publishing reports             |
| 🔜 In-Toto Provenance Chain       | Planned    | Secure software supply chain with in-toto attestations                     |
| 🔜 Containerized Forensics Engine | Planned    | Isolated sandbox execution and self-contained provenance collection        |
| 🔜 Source Code Signing            | Planned    | Attest to integrity of the AI Forensics tool code itself (Repro + Cosign)  |

---

## 🧩 Format Support

| Format       | Status     | Notes                                                                 |
|--------------|------------|-----------------------------------------------------------------------|
| `.safetensors` | ✅ Done     | Header + tensor shape/type inspection + binary payload scanning       |
| `.pth`         | ✅ Done     | Zip inspection, PickleScanner, and suspicious blob detection          |
| `.gguf`        | ✅ Done     | Tensor and metadata validation with binary heuristics                 |
| `.onnx`        | ⏳ Planned  | Graph structure, operator listing, and constant tensor inspection     |
| `.tflite`      | ⏳ Planned  | Flatbuffer schema parsing and opcode/weight verification              |

---

## ⚙️ Security & Signing

| Feature                             | Status     | Description                                                                 |
|------------------------------------|------------|-----------------------------------------------------------------------------|
| Artifact Signing with Cosign       | ✅ Done     | Sign SBOM + report bundles                                                  |
| Rekor Transparency Log             | ✅ Done     | Log signatures immutably in transparency ledger                             |
| Source Code Signing                | 🔜 Planned  | Verify the tool itself is tamper-free and signed by maintainers            |
| In-Toto Provenance Chain           | 🔜 Planned  | Supply chain attestation support for all forensic actions                   |
| Containerized Forensics Execution | 🔜 Planned  | Run forensic tool in hardened sandbox container with audit traceability     |

---

## 📦 Export & Integration Features

- ✅ JSON + HTML export
- ✅ CycloneDX & SPDX SBOM generation
- ✅ Cosign signature and attestation bundle
- ✅ ZIP bundling for offline archive
- 🔜 GitLab CI template with compliance report export
- 🔜 Harbor integration with annotations and attestation metadata

---

## ⚖️ Compliance Features

| Feature                       | Status     |
|------------------------------|------------|
| DISA STIG Mapping            | 🔜 Planned  |
| NIST 800-53 / 800-190 Controls| 🔜 Planned  |
| Policy-Driven Attestation    | ✅ Done     |
| Signed Report Chain          | ✅ Done     |
| Artifact Tamper Checks       | ✅ Done     |

---

## 📅 Timeline (Tentative)

| Quarter       | Focus Area                                         |
|---------------|----------------------------------------------------|
| Q2 2025       | ✅ Core implementation and format support          |
| Q3 2025       | ⚙️ Multi-threaded analysis, UI mockup, YARA support|
| Q4 2025       | ☁️ Cloud integrations, compliance mappings, in-toto |
| Q1 2026       | 🌐 Public release with plugin API & dashboard       |

---

## ✍️ Contributing

We welcome contributions via:
- New format parsers
- New rule types
- Improvements to HTML reports or SBOM generators
- STIG/NIST compliance profiles

See `CONTRIBUTING.md` for guidelines.

---

## 📌 Future Ideas

- Integration with SBOM viewers
- Dependency tracing inside pickled models
- GPT-based assistant to explain violation results
- Export to PDF with signature + watermark
- Reproducibility check for exported tensors

---

## 🛡️ Security Model

- All file parsing avoids unsafe deserialization (`torch.load`, `pickle.load`)
- Sandboxed inspection for `.pth` files
- Binary heuristics detect packed or suspicious payloads
- Policy-based control of violations and export behavior
- Signature verification for source authenticity
- Source and artifact signature verification for authenticity
- Configurable policy enforcement with override modes
- Containerized forensics engine for isolated scans (planned)
- Provenance capture and Rekor logging for signatures

---

## 🧠 Related Projects

- [`modelinspect`](https://github.com/openai/modelinspect) - Core inspection logic
- [`sigstore/cosign`](https://github.com/sigstore/cosign) - Digital signing
- [`cyclonedx-python`](https://github.com/CycloneDX/cyclonedx-python-lib) - SBOM export
- [`harbor`](https://goharbor.io) - OCI registry integration

---

## 📣 Feedback & Contact

To suggest features or report issues:
- Open an issue on GitLab
- Contact the maintainers directly
- Participate in roadmap discussions

---
