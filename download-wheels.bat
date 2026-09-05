@echo off
chcp 65001 > nul
title 下载离线依赖包（需联网运行）

REM ============================================
REM  在有互联网的机器上运行此脚本
REM  生成 wheels/ 目录和 python/ 嵌入式环境
REM ============================================

echo [1/4] 下载嵌入式 Python ...
if not exist "python\python.exe" (
    if not exist "python-3.13.7-embed-amd64.zip" (
        echo 正在下载 python-3.13.7-embed-amd64.zip ...
        curl -L -o python-3.13.7-embed-amd64.zip https://www.python.org/ftp/python/3.13.7/python-3.13.7-embed-amd64.zip
        if errorlevel 1 (
            echo 下载失败，请手动下载: https://www.python.org/ftp/python/3.13.7/python-3.13.7-embed-amd64.zip
            pause
            exit /b 1
        )
    )
    echo 解压嵌入式 Python ...
    mkdir python 2>nul
    tar -xf python-3.13.7-embed-amd64.zip -C python
)

REM 启用 pip: 取消 python313._pth 中 import site 的注释
echo [2/4] 配置嵌入式 Python ...
powershell -Command "(Get-Content python\python313._pth) -replace '^#import site', 'import site' | Set-Content python\python313._pth"

REM 安装 pip 到嵌入式 Python
if not exist "python\Scripts\pip.exe" (
    echo 安装 pip ...
    if not exist "get-pip.py" (
        curl -L -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    )
    python\python.exe get-pip.py
)

REM 下载所有依赖 whl 到 wheels 目录
echo [3/4] 下载依赖包到 wheels/ ...
mkdir wheels 2>nul
python\python.exe -m pip download -r requirements.txt -d wheels -i https://mirrors.aliyun.com/pypi/simple/
if errorlevel 1 (
    echo 部分包下载失败，请检查网络后重试
    pause
    exit /b 1
)

REM 预下载 RapidOCR 模型
echo [4/4] 预下载 RapidOCR 模型 ...
python\python.exe -c "from rapidocr import RapidOCR; RapidOCR()"
echo.
echo ============================================
echo  下载完成！
echo  目录结构:
echo    python/     - 嵌入式 Python 运行环境
echo    wheels/     - 离线依赖包
echo    resources/  - 资源文件(含模型)
echo ============================================
echo.
echo 接下来请将整个项目文件夹复制到目标机器,
echo 然后运行 install-offline.bat 安装依赖,
echo 最后运行 StartWD.bat 启动程序。
echo.
pause
