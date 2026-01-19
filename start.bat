@echo off
:: 设置终端编码为 UTF-8
chcp 65001 >nul
title Polymarket Scout - Mikon AI Army
echo [Mikon AI Army] 正在启动 Polymarket 侦察兵...
echo.

:: 检查环境并运行
set PYTHONUNBUFFERED=1
python scout.py

echo.
echo 扫描已结束。结果已同步保存至 markets_list.txt
pause
