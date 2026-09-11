"""
tools/diagnose_gpu.py
---------------------
Read-only GPU and CUDA/cuDNN environment diagnostic tool for the OCR project.
Reports environment, package versions, DLL paths, and validates Paddle GPU operations.
This script does NOT modify any system or project state.
"""

import os
import sys
import ctypes
from pathlib import Path

def get_file_version_windows(file_path: str):
    """Retrieve Windows PE FileVersion if available."""
    try:
        import win32api
        info = win32api.GetFileVersionInfo(file_path, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        return f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
    except Exception:
        return None

def query_cudnn_get_version(dll_path: str, bin_dir: str):
    """Call cudnnGetVersion C API via ctypes."""
    try:
        old_path = os.environ.get("PATH", "")
        if bin_dir not in old_path:
            os.environ["PATH"] = bin_dir + ";" + old_path
        cookie = None
        if hasattr(os, "add_dll_directory"):
            try:
                cookie = os.add_dll_directory(bin_dir)
            except Exception:
                pass
        
        dll = ctypes.CDLL(dll_path)
        dll.cudnnGetVersion.restype = ctypes.c_size_t
        raw_v = dll.cudnnGetVersion()
        major = raw_v // 10000
        minor = (raw_v % 10000) // 100
        patch = raw_v % 100
        return f"{raw_v} ({major}.{minor}.{patch})"
    except Exception as e:
        return f"Error querying cudnnGetVersion: {e}"

def main():
    print("=" * 60)
    print("       OCR PROJECT GPU ENVIRONMENT DIAGNOSTIC")
    print("=" * 60)

    # 1. Python Executable & Version
    print("\n[1] Python & Environment")
    print(f"  Executable        : {sys.executable}")
    print(f"  Python Version    : {sys.version.split()[0]}")
    prefix = sys.prefix
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    is_venv = prefix != base_prefix
    print(f"  Virtual Env Active: {is_venv}")
    print(f"  Prefix (VENV)     : {prefix}")
    print(f"  Base Prefix       : {base_prefix}")

    # 2. Environment Variables
    print("\n[2] CUDA Environment Variables & PATH")
    cuda_vars = ["CUDA_PATH", "CUDA_HOME", "CUDA_ROOT", "CUDNN_PATH", "VIRTUAL_ENV"]
    for var in cuda_vars:
        val = os.environ.get(var, "<UNSET>")
        print(f"  {var:<18}: {val}")

    print("\n  Relevant PATH Entries containing 'cuda', 'cudnn', or 'nvidia':")
    path_entries = os.environ.get("PATH", "").split(";")
    rel_entries = [p for p in path_entries if any(k in p.lower() for k in ["cuda", "cudnn", "nvidia", ".venv-gpu"])]
    if rel_entries:
        for p in rel_entries[:10]:
            print(f"    - {p}")
    else:
        print("    (None found in PATH)")

    # 3. Installed NVIDIA/Paddle Packages
    print("\n[3] Pip Package Versions (nvidia / cuda / cudnn / paddle)")
    try:
        import importlib.metadata as metadata
        dists = metadata.distributions()
        relevant_pkgs = []
        for d in dists:
            name = d.metadata["Name"]
            if any(k in name.lower() for k in ["nvidia", "cuda", "cudnn", "paddle"]):
                relevant_pkgs.append((name, d.version))
        relevant_pkgs.sort(key=lambda x: x[0].lower())
        for name, ver in relevant_pkgs:
            print(f"  {name:<28}: {ver}")
    except Exception as e:
        print(f"  Error reading package metadata: {e}")

    # 4. cuDNN DLL Discovery & Inspection
    print("\n[4] cuDNN DLL Locations & Runtime Version")
    venv_cudnn_bin = Path(prefix) / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin"
    cudnn_dll = venv_cudnn_bin / "cudnn64_9.dll"
    if cudnn_dll.exists():
        print(f"  Found cuDNN DLL   : {cudnn_dll}")
        api_ver = query_cudnn_get_version(str(cudnn_dll), str(venv_cudnn_bin))
        print(f"  cuDNN C API Version: {api_ver}")
        win_ver = get_file_version_windows(str(cudnn_dll))
        if win_ver:
            print(f"  Windows FileVersion: {win_ver}")
    else:
        print(f"  cuDNN DLL not found at expected location: {cudnn_dll}")

    # 5. PaddlePaddle & CUDA Initialization
    print("\n[5] PaddlePaddle Framework & GPU Execution")
    try:
        import paddle
        print(f"  Paddle Version    : {paddle.__version__}")
        print(f"  CUDA Compiled     : {paddle.is_compiled_with_cuda()}")
        if paddle.is_compiled_with_cuda():
            print(f"  Paddle CUDA Ver   : {paddle.version.cuda()}")
            dev_count = paddle.device.cuda.device_count()
            print(f"  GPU Device Count  : {dev_count}")
            if dev_count > 0:
                gpu_name = paddle.device.cuda.get_device_name(0)
                print(f"  GPU 0 Name        : {gpu_name}")
                print(f"  Current Device    : {paddle.device.get_device()}")

                # Small GPU Tensor Operation
                print("\n  Testing minimal GPU tensor operation...")
                t = paddle.to_tensor([10.0, 20.0, 30.0], place=paddle.CUDAPlace(0))
                res = t * 2.0
                print(f"  Tensor calculation: t * 2.0 = {res.numpy()} on {res.place}")
                print("  [SUCCESS] GPU tensor computation executed cleanly.")
    except Exception as e:
        print(f"  [ERROR] Paddle GPU operation failed: {e}")

    print("\n" + "=" * 60)
    print("             DIAGNOSTIC COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
