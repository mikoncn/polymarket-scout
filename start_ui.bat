@echo off
:: 设置终端编码为 UTF-8
chcp 65001 >nul
title Polymarket Scout - 图形化指挥中心
echo [Mikon AI Army] 正在启动图形化配置界面...
echo.
echo 正在打开浏览器访问 http://localhost:5000 ...

:: 启动浏览器
start http://localhost:5000

:: 启动 Flask 服务器
python server.py
pause
