@echo off
chcp 65001 > nul
title Screen OCR Watchdog

REM 优先使用项目内嵌入式 Python，回退到系统 Python
if exist "python\python.exe" (
    set PY=python\python.exe
) else (
    set PY=python
)

:begin
cls
echo 1.单机使用
echo 2.双机使用（串口隔离-内网）
echo 3.双机使用（串口隔离-外网）
echo 4.显示操作说明
echo 5.编辑配置文档
echo 6.编辑关键词典
echo 7.编辑联系人信息
echo 8.安装Python
echo 9.安装wheels
echo i.离线安装（无互联网环境）
echo q.退出


set /p  APPID="请选择:"
if %APPID%==q goto end
if %APPID%==i goto install
if %APPID%==9 goto nine
if %APPID%==8 goto eight
if %APPID%==7 goto seven
if %APPID%==6 goto six
if %APPID%==5 goto five
if %APPID%==4 goto four
if %APPID%==3 goto three
if %APPID%==2 goto two
if %APPID%==1 goto one
goto begin

:one
%PY% -m pip install -q -r requirements.txt
%PY% pad-ocr-watchdog.py --UseSerial no

cls
goto begin
:two
%PY% -m pip install -q -r requirements.txt
%PY% pad-ocr-watchdog.py --UseSerial yes

cls
goto begin
:three
%PY% serial2Email.py
pause>nul
cls
goto begin
:four
cls
type .\说明书.txt
echo .
pause
goto begin

:five
notepad .\setup.ini
cls
goto begin

:six
notepad .\alert_words.txt
cls
goto begin

:seven
notepad .\alert_words.txt
cls
goto begin

:eight
start .\python-3.8.10-amd64.exe
cls
goto begin

:nine
%PY% -m pip install -q -r requirements.txt
cls
goto begin

:install
call install-offline.bat
goto begin

:end
echo 程序退出.
rem pause>nul
