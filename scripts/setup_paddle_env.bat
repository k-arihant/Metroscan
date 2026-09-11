@echo off
echo ============================================================
echo   METROSCAN PADDLE-GPU ENVIRONMENT SETUP (WINDOWS / NVIDIA)
echo ============================================================

echo [1/5] Checking for Conda...
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda not found in PATH. Please ensure Miniconda/Anaconda is installed.
    exit /b 1
)

echo [2/5] Creating Python 3.12 Conda environment: metroscan-gpu...
call conda create -n metroscan-gpu python=3.12 -y
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create conda environment.
    exit /b %ERRORLEVEL%
)

echo [3/5] Activating metroscan-gpu...
call conda activate metroscan-gpu

echo [4/5] Installing PaddlePaddle GPU 3.3.1 (CUDA 12.6) and cuDNN 9.9...
python -m pip install --upgrade pip setuptools wheel
python -m pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
python -m pip install nvidia-cudnn-cu12==9.9.0.52 nvidia-cuda-runtime-cu12==12.6.77 nvidia-cublas-cu12==12.6.4.1
python -m pip install paddleocr==3.7.0 opencv-python Pillow numpy scikit-image scipy

echo [5/5] Installing MetroScan backend dependencies...
python -m pip install fastapi==0.115.0 "uvicorn[standard]==0.30.0" python-multipart==0.0.9 pydantic==2.9.0 python-dotenv==1.0.1 google-genai reportlab requests supabase cloudinary

echo ============================================================
echo   SETUP COMPLETE! To activate: conda activate metroscan-gpu
echo ============================================================
