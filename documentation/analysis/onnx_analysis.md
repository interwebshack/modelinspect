# ONNX File Format Analysis (AI Forensics)

The `.onnx` (Open Neural Network Exchange) format is a cross-platform, framework-agnostic representation of deep learning models. It is widely used for exporting models from PyTorch, TensorFlow, and other frameworks into a portable, standardized binary format.

This document explains the ONNX file structure and how **AI Forensics** validates `.onnx` files for consistency, integrity, and potential security threats.

---

## 📦 ONNX File Structure

ONNX files use **Protocol Buffers (protobuf)** to encode a model as a single `.onnx` binary file. The internal structure conforms to the `onnx.ModelProto` message schema.

Key sections inside the ONNX file:

1. **ModelProto (protobuf root object)**
2. **Graph (nodes and tensors)**
3. **Initializers (weights)**
4. **Inputs/Outputs**
5. **Metadata properties**

---

## 🔑 ModelProto Schema Overview

```protobuf
message ModelProto {
  int64 ir_version;
  string producer_name;
  string producer_version;
  string domain;
  int64 model_version;
  repeated OperatorSetIdProto opset_import;
  GraphProto graph;
  repeated StringStringEntryProto metadata_props;
}
```

### Important Fields:

| Field               | Purpose                                     |
|---------------------|---------------------------------------------|
| `ir_version`        | ONNX IR spec version                        |
| `producer_name`     | Exporting tool (e.g., `pytorch`)            |
| `opset_import`      | Operator sets used by model                 |
| `graph`             | Contains computation nodes and weights      |
| `metadata_props`    | Arbitrary key-value model metadata          |

---

## 📐 Graph Structure

The `graph` object includes:
- **Nodes** (operators like MatMul, Relu, Conv)
- **Inputs / Outputs**
- **Initializers** (tensors holding model parameters)
- **ValueInfoProto** (shape/type annotations)

---

## 💾 Tensor Encoding

ONNX tensors are binary-encoded using the `TensorProto` structure:

- Raw tensor data stored as a byte array (`raw_data`)
- Metadata includes:
  - `dims`: shape
  - `data_type`: enum (e.g., `FLOAT`, `INT64`)
  - `name`: identifier

Supported tensor types include:

| Data Type         | Bytes | Notes               |
|-------------------|--------|---------------------|
| `FLOAT`           | 4      | 32-bit IEEE float   |
| `DOUBLE`          | 8      | 64-bit float        |
| `INT64`           | 8      | 64-bit signed int   |
| `INT32`           | 4      | 32-bit signed int   |
| `UINT8`           | 1      | Unsigned byte       |
| `BOOL`            | 1      | Boolean             |
| `FLOAT16`         | 2      | 16-bit float        |
| `BFLOAT16`        | 2      | Optional support    |

---

## 🧪 AI Forensics Validation Checklist

### ✅ Structural Checks

- Validates top-level `ModelProto` using ONNX protobuf schema
- Confirms presence of `graph`, `opset_import`, and `model_version`
- Confirms tensor metadata matches data layout

### 📏 Tensor and Node Checks

- Verifies tensor shapes, dtypes, and raw byte lengths
- Flags unused initializers or hidden tensors
- Detects large tensors or abnormal sizes (>2GB)
- Identifies malformed operator inputs

### 🔍 Metadata and Security Checks

- Inspects `metadata_props` for unusual or spoofed values
- Verifies `producer_name` and `opset_import` match known values
- Detects suspicious operators (e.g., `Loop`, `Scan`, `CustomOp`)
- Flags models with dynamic shape inference abuse

---

## 🚨 Red Flags Detected by AI Forensics

| Condition                        | Severity | Explanation                                |
|----------------------------------|----------|--------------------------------------------|
| Corrupted or missing `graph`     | ❌       | Invalid or truncated ONNX model            |
| Unknown `opset_import` domain    | ⚠️       | Potential custom/untrusted ops             |
| Unused tensors >500MB            | ⚠️       | Possible payload injection                 |
| Unknown metadata keys            | ⚠️       | Spoofed producer/version info              |
| Dynamic tensor shapes            | ⚠️       | Potential for runtime abuse                |
| Overlapping tensor names         | ❌       | Graph confusion or manipulation            |

---

## 🔏 Integrity & Provenance

- **SHA-256 fingerprints** of model binary and individual tensors
- **SBOM generation** includes:
  - Operator set
  - Input/output shapes
  - Tensor count and types
- **Optional signature and attestation** with Cosign/DSSE

---

## 📝 Summary Table

| Section            | What to Expect                                 |
|--------------------|-------------------------------------------------|
| `ModelProto`        | Complete model metadata and graph              |
| `Graph`             | Fully connected, no missing nodes              |
| `Initializers`      | Tensors with proper dtype and shape            |
| `Metadata`          | Includes `producer_name`, `domain`, etc.       |
| `Opsets`            | Imported and known operator sets               |

---

## 🧷 Security Features

- Binary-safe, protobuf-encoded format
- Easily parsed with no code execution
- Supports deterministic analysis
- No embedded Python objects or scripts

---
