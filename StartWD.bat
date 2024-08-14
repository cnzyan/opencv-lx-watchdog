@echo off
chcp 65001 > nul

REM python -m venv venv
REM pip install --user -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

:begin
cls
echo 1.单机使用 
echo 2.双机使用（串口隔离-内网） 
echo 3.双机使用（串口隔离-外网） 
echo 4.显示操作说明 
echo 5.编辑配置文档 
echo 6.编辑关键词典 
echo 7.安装Python 
echo 8.安装wheels 
echo 9.退出 


set /p  APPID="请选择:"
if %APPID%==9 goto end
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
python check-requirements.py
python pad-ocr-watchdog.py --UseSerial no

cls
goto begin
:two
python check-requirements.py
python pad-ocr-watchdog.py --UseSerial yes

cls
goto begin
:three
python check-requirements.py
python serial2Email.py
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
start .\python-3.8.10-amd64.exe

cls
goto begin
:eight
python check-requirements.py

cls
goto begin
:end
echo 程序退出.
pause>nul