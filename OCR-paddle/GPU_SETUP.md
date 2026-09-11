# GPU & CUDA/cuDNN Setup Guide

This document outlines the GPU environment configuration, dependencies, diagnostic procedures, and troubleshooting resolutions for the OCR pipeline project.

---

## 1. Environment Architecture

```
Antigravity / VS Code Workspace
        ↓
Python 3.12.10 (.venv-gpu)
        ↓
PaddlePaddle GPU 3.3.1 (CUDA 12.6 Build)
        ↓
cuDNN Runtime 9.9.0 (nvidia-cudnn-cu12 == 9.9.0.52)
        ↓
PaddleOCR 3.7.0 / PaddleX 3.7.2
        ↓
NVIDIA GeForce RTX 3050 A Laptop GPU (4GB VRAM, Compute 8.9)
```

### Why `.venv-gpu` is Used
- **Python 3.12 Compatibility**: PaddlePaddle GPU 3.3.1 pre-built wheels support Python 3.12. System Python 3.14 lacks CUDA/cuDNN GPU wheels for PaddlePaddle.
- **Dedicated Dependencies**: Contains self-contained CUDA 12 and cuDNN 9 runtime wheels (`nvidia-cudnn-cu12`, `nvidia-cuda-runtime-cu12`, `nvidia-cublas-cu12`) so that no system-wide CUDA toolkit installation is needed.
- **Isolation**: Prevents breaking or altering other Python environments on the host system.

---

## 2. Hardware & Driver Specifications

- **GPU**: NVIDIA GeForce RTX 3050 A Laptop GPU (4094 MiB)
- **Compute Capability**: 8.9
- **Driver Version**: 592.82
- **CUDA Driver API Capability**: 13.1
- **CUDA Runtime Version**: 12.6

---

## 3. Package Versions

| Package | Target Version | Source / Notes |
| :--- | :--- | :--- |
| `python` | 3.12.10 | Workspace interpreter: `.\.venv-gpu\Scripts\python.exe` |
| `paddlepaddle-gpu` | 3.3.1 | Built with CUDA 12.6, cuDNN 9.9 |
| `paddleocr` | 3.7.0 | OCR Engine (PaddleX v3 backend) |
| `nvidia-cudnn-cu12` | 9.9.0.52 | Aligns with PaddlePaddle 3.3.1 compiled cuDNN version |
| `nvidia-cuda-runtime-cu12` | 12.6.77 | CUDA 12.6 runtime libraries |
| `nvidia-cublas-cu12` | 12.6.4.1 | cuBLAS linear algebra backend |

---

## 4. Diagnostics & Troubleshooting: cuDNN Version Alignment

### Prior Warning Observed
```
WARNING: device: 0. The installed Paddle is compiled with CUDNN 9.9, but CUDNN version in your machine is 9.5, which may cause serious incompatible bug.
```

### Cause
The environment previously had `nvidia-cudnn-cu12 == 9.5.1.17` installed. PaddlePaddle 3.3.1 was compiled against cuDNN 9.9.0 (`90900`). At initialization, Paddle queried `cudnnGetVersion()` from `cudnn64_9.dll`, found version 9.5.1 (`90501`), and emitted a version mismatch warning.

### Resolution
Upgraded `nvidia-cudnn-cu12` to `9.9.0.52` strictly within `.venv-gpu`:
```powershell
.\.venv-gpu\Scripts\python.exe -m pip install nvidia-cudnn-cu12==9.9.0.52
```
This provided the exact `cudnn64_9.dll` version (9.9.0.52) expected by PaddlePaddle 3.3.1, eliminating the warning.

---

## 5. Diagnostic Commands & Verification

### Running the Diagnostic Tool
A dedicated read-only diagnostic script is provided:
```powershell
.\.venv-gpu\Scripts\python.exe tools\diagnose_gpu.py
```

### Quick Verification Commands

1. **Verify Python Interpreter**:
   ```powershell
   python -c "import sys; print(sys.executable)"
   ```
   *Expected: Points to `...\OCR\.venv-gpu\Scripts\python.exe`*

2. **Verify Paddle GPU Status**:
   ```powershell
   python -c "import paddle; print('Paddle:', paddle.__version__); print('CUDA Compiled:', paddle.is_compiled_with_cuda()); print('CUDA:', paddle.version.cuda()); print('GPU:', paddle.device.cuda.get_device_name(0))"
   ```

3. **Verify cuDNN Runtime DLL Version**:
   ```powershell
   (Get-Item '.\.venv-gpu\Lib\site-packages\nvidia\cudnn\bin\cudnn64_9.dll').VersionInfo.FileVersion
   ```
   *Expected: `9.9.0.52`*

4. **Verify Actual OCR Inference**:
   ```powershell
   python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='en', device='gpu:0'); r = ocr.predict(r'.\images\test.jpeg'); print('OCR SUCCESS')"
   ```
