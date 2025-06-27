# GGUF File Format Analysis (AI Forensics)

The `.gguf` file format (GPT-Generated Unified Format) is a binary serialization standard used primarily by [ggml](https://github.com/ggerganov/ggml)-based projects such as `llama.cpp`. It provides a secure, portable, and extensible structure for storing large language model weights and metadata.

This document explains the layout, expected contents, and how the **AI Forensics** tool validates `.gguf` files for structural integrity, version consistency, and security risks.

---

## 📦 GGUF File Structure

```text
+------------------------+--------------------+-----------------+----------------+
|   Magic (GGUF)        | Version (uint32)   | Metadata KV     | Tensor Blocks  |
+------------------------+--------------------+-----------------+----------------+
```

- **Magic**: ASCII `"GGUF"` — 4 bytes
- **Version**: 32-bit little-endian unsigned integer
- **Metadata KV Block**: Structured metadata as typed key-value pairs
- **Tensor Blocks**: Raw tensors, quantized or floating-point

---

## 🔑 Metadata Key-Value Block

This section encodes model metadata using typed key-value pairs in binary TLV format.

Examples of common keys:
- `general.architecture` → `"llama"`
- `tokenizer.ggml.model` → `"gpt2"`
- `llama.embedding_length` → `4096`
- `tokenizer.ggml.bos_token_id` → `1`

Supported types:
- Strings
- Integers (signed/unsigned)
- Floats
- Arrays
- Binary blobs

---

## 🧮 Tensor Block Layout

Each tensor entry includes:
- **Name**: e.g., `model.layers.0.attn.q_proj.weight`
- **Dtype**: e.g., `Q4_0`, `Q8_1`, `F16`, `F32`
- **Shape**: List of dimensions
- **Offset**: Byte offset into the file

Quantization types supported:
- `Q4_0`, `Q4_1`
- `Q5_0`, `Q5_1`
- `Q8_0`, `Q8_1`
- `F16`, `F32`

---

## 🧭 GGUF Version Differences

### ✅ Currently Known Versions

| Version | Status       | Description                                                       |
|---------|--------------|-------------------------------------------------------------------|
| `1`     | Deprecated   | Basic metadata; limited fields                                    |
| `2`     | Current      | Richer metadata, quantization types, tokenizer info               |
| `3+`    | Reserved     | Not yet defined; AI Forensics will flag as unsupported            |

### 🔄 GGUF v1

- Minimal metadata (e.g., `general.architecture`)
- Simple tensors and dtype support
- No tokenizer-specific fields

### ✅ GGUF v2 (Current Standard)

- Expected tokenizer metadata fields
- More dtype support (`Q5_1`, `Q8_0`, `Q6_K`)
- Improved tensor alignment
- Extended metadata fields

---

## 🧪 Version Integrity Validation

AI Forensics performs strict version-to-content alignment:

| Check Item                | v1                        | v2                        |
|---------------------------|----------------------------|----------------------------|
| Metadata richness         | Minimal                    | Extended                   |
| Quantization support      | Basic                      | Wide support               |
| Tokenizer fields          | Rare                       | Expected                   |
| Alignment requirements    | Loose                      | 32/64-byte aligned         |
| Array/blob metadata       | Not supported              | Supported                  |

### ❗ Mismatches are flagged:

| Condition                                            | Severity | Description                           |
|-----------------------------------------------------|----------|---------------------------------------|
| Declares v2 but lacks tokenizer fields              | ⚠️       | Suspicious export or tampered         |
| Declares v1 but contains v2-only fields             | ⚠️       | Invalid version-content alignment     |
| Unknown version                                     | ❌       | Hard failure                          |

---

## 🛡️ AI Forensics Scanning Logic

### ✅ Header Validation

- Confirms `"GGUF"` magic string
- Verifies version is in known set `{1, 2}`
- Flags unknown or invalid versions

### 📏 Tensor Checks

- Tensor offsets must be aligned
- No overlaps or ghost tensors
- Dtypes must be recognized
- Tensor size must match shape and dtype

### 🔬 Metadata Checks

- Mandatory keys must exist (e.g., `general.architecture`)
- Tokenizer fields verified for v2
- Flags unexpected blobs or oversized metadata

---

## 📝 Summary Table

| Component         | What to Expect                                          |
|------------------|----------------------------------------------------------|
| Header            | `"GGUF"` + version in {1, 2}                             |
| KV Metadata       | Rich key set with typed values                          |
| Tensor Blocks     | Quantized or float tensors, properly shaped             |
| Alignment         | 32-byte or 64-byte alignment for performance            |
| Version Match     | Structure must match version rules                      |

---

## 🧷 Security Notes

- No code execution or deserialization
- Deterministic structure
- Suitable for offline inspection
- Each tensor is fingerprinted via SHA-256
- SBOM and attestation optional but supported

---
