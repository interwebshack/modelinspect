# SafeTensors File Format Analysis (AI Forensics)

This document explains the structure of [Safetensors](https://github.com/huggingface/safetensors#safetensors) files and how **AI Forensics** safely inspects `.safetensors` files by analyzing metadata, verifying structure, and detecting potentially malicious or unsafe content — all without executing any model code.  

---

## SafeTensors Format Overview  

The `.safetensors` format is purpose-built for storing AI model weights in a **secure, efficient, and deterministic** way.  It was developed to address the security concerns around formats like `.pt` or `.pkl`, which can execute arbitrary Python code during loading — a serious attack surface in untrusted environments.

**Key characteristics of SafeTensors:**

* Stores tensors in a **simple binary format**  
* Avoids using Python object serialization (like `pickle`)  
* Guarantees **no code execution risk** during loading — making it safe for use in security-sensitive or forensic workflows  
* Supports **zero-copy memory-mapping** for fast and efficient tensor access
* Includes a **JSON-based header** containing metadata such as tensor names, shapes, and data types  

## 📦 SafeTensors File Layout

```text
+----------------------+----------------------+-------------------+
|  Header Length (u64) |      Header JSON     |     Tensor Data   |
+----------------------+----------------------+-------------------+
       (8 bytes)         (Header Length bytes)    (remaining bytes)
```

### 1. Header Length (u64)

- First 8 bytes of the file.
- Unsigned 64-bit little-endian integer.
- Indicates length (in bytes) of the JSON header that follows.

### 2. Header (JSON)

- UTF-8 encoded metadata describing tensors.
- Maps tensor names to dictionaries with:
  - `dtype`: e.g., `"F32"`, `"I64"`, `"BF16"`
  - `shape`: list of ints (e.g., `[1000, 512]`)
  - `data_offsets`: two integers indicating the start and end offset in the tensor data section

Example:

```json
{
  "model.weight": {
    "dtype": "F32",
    "shape": [256, 256],
    "data_offsets": [0, 262144]
  },
  "__metadata__": {
    "format": "pt",
    "quantization": "none"
  }
}
```

### 3. Tensor Data

- Raw binary tensor data.
- Stored in the order defined by offsets in the header.
- Not compressed or encoded — direct memory-mapped layout.

---

## 📘 Supported Dtypes

| Dtype  | Description            | Bytes per Element |
|--------|------------------------|-------------------|
| `F16`  | 16-bit float           | 2                 |
| `F32`  | 32-bit float           | 4                 |
| `F64`  | 64-bit float           | 8                 |
| `I8`   | 8-bit signed int       | 1                 |
| `U8`   | 8-bit unsigned int     | 1                 |
| `I16`  | 16-bit signed int      | 2                 |
| `I32`  | 32-bit signed int      | 4                 |
| `I64`  | 64-bit signed int      | 8                 |
| `BF16` | bfloat16               | 2                 |

---

## ✅ AI Forensics Validation Checklist

### Header Integrity

- Verifies first 8 bytes match length of UTF-8 JSON
- Confirms JSON is valid and parseable
- Confirms all keys have `dtype`, `shape`, and `data_offsets`
- Checks `__metadata__` structure (if present)

### Tensor Shape & Size

- Confirms `shape × dtype size == offset size`
- Validates offset bounds against file length
- Flags overlapping or missing tensor regions

### Binary Heuristics & Threat Detection

- Flags ghost tensors (in header but no data)
- Flags tensors with misaligned or huge size (>2GB)
- Detects use of suspicious dtypes (`U8` for model weights)
- Flags malformed or spoofed metadata

### Metadata Integrity

- Validates known fields in `__metadata__`
- Compares against allowlist of expected keys (e.g., `format`, `quantization`, `producer`)
- Records unknown fields for reporting

---

## 🔐 Why SafeTensors Is Safer

| Feature                    | SafeTensors | Pickle-Based Files (.pt/.pth) |
|---------------------------|-------------|-------------------------------|
| Deterministic layout      | ✅          | ❌                            |
| Human-readable metadata   | ✅          | ❌                            |
| No code execution         | ✅          | ❌                            |
| Offline-safe              | ✅          | ❌                            |
| Fast binary parsing       | ✅          | ⚠️ (requires `torch.load`)    |

---

## 🚨 Red Flags Detected by AI Forensics

| Condition                      | Flag Level | Explanation                          |
|-------------------------------|------------|--------------------------------------|
| Overlapping `data_offsets`    | ❌         | Memory corruption or tampering       |
| Huge tensor size (>2GB)       | ⚠️         | Possible obfuscation or attack       |
| Unknown dtype                 | ❌         | Unsupported or crafted data type     |
| Ghost tensor in header        | ⚠️         | Header declares data that isn't real |
| Malformed `__metadata__`      | ⚠️         | Spoofed or unexpected content        |

---

## 📝 Summary Table

| Field          | Description                                  |
|----------------|----------------------------------------------|
| Header Length  | 8-byte little-endian integer                 |
| Header JSON    | UTF-8 JSON map of tensor metadata            |
| Tensor Data    | Binary blob of tensor contents               |
| Alignment      | Not required but expected to be sequential   |
| Signature      | External signature optional (AI Forensics supports) |

---

## 🧷 Security Controls

- Entire file can be fingerprinted via SHA-256
- Each tensor individually hashed
- SBOM and digital signatures supported for provenance tracking
- Offline-safe inspection enabled (no execution during parsing)

---
