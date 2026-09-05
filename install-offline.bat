@echo off
chcp 65001 > nul
title 离线安装依赖

REM ============================================
REM  在目标无互联网机器上运行此脚本
REM  从 wheels/ 目录离线安装所有依赖
REM ============================================

echo 正在检查 python 目录 ...
if not exist "python\python.exe" (
    echo [错误] 未找到 python\python.exe
    echo 请确保嵌入式 Python 已放在 python 目录中。
    echo 运行 download-wheels.bat（在有网机器上）可自动准备。
    pause
    exit /b 1
)

echo 正在检查 wheels 目录 ...
if not exist "wheels" (
    echo [错误] 未找到 wheels 目录
    echo 请先在有网机器上运行 download-wheels.bat 下载依赖包。
    pause
    exit /b 1
)

echo.
echo [1/2] 离线安装 pip 依赖 ...
python\python.exe -m pip install --no-index --find-links=wheels -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

REM 检查 RapidOCR 模型文件是否存在
echo [2/2] 检查 RapidOCR 模型 ...
python\python.exe -c "from rapidocr import RapidOCR; e=RapidOCR(); print('模型检查通过')" 2>nul
if errorlevel 1 (
    echo [提示] RapidOCR 模型文件缺失，尝试从 resources/models 复制 ...
    if exist "resources\models" (
        python\python.exe -c "import rapidocr, os, shutil; src='resources\\models'; dst=os.path.join(os.path.dirname(rapidocr.__file__),'models'); [shutil.copy2(os.path.join(src,f),os.path.join(dst,f)) for f in os.listdir(src) if f.endswith('.onnx')]"
        echo 模型文件已复制。
    ) else (
        echo [警告] 未找到 resources\models 目录，首次启动程序时需要联网下载模型。
    )
)

echo.
echo ============================================
echo  离线安装完成！
echo  运行 StartWD.bat 启动程序
echo ============================================
echo.
pause
