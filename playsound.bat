@echo off
start .\ffplay.exe %1
ping -n 2 -w 500 0.0.0.1>nul
taskkill -f -im ffplay.exe