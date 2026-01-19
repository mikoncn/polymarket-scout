@echo off
:: 设置终端编码为 UTF-8
chcp 65001 >nul
title Polymarket Scout - Web 界面
echo [Mikon AI Army] 正在启动 Web 配置界面...
echo.
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

python server.py
pause
