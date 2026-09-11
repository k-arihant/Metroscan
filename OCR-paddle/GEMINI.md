# Antigravity Workspace Configuration & Rules

## Python Environment Execution
- This project MUST always use the GPU-enabled virtual environment located at:
  `${workspaceFolder}\.venv-gpu\Scripts\python.exe`
- Python version: 3.12.10
- GPU Framework: PaddlePaddle GPU 3.3.1 (CUDA 12, NVIDIA GeForce RTX 3050 Laptop GPU)
- NEVER use system Python 3.14 (`C:\Python314\python.exe`).
- All terminal executions, test runs, and OCR processing must execute via `.\.venv-gpu\Scripts\python.exe` or within the workspace terminal environment where `.\.venv-gpu\Scripts` is prepended to `PATH`.
