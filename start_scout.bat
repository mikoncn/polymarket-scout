@echo off
:: 设置终端编码为 UTF-8
chcp 65001 >nul
:: 设置不缓冲输出
set PYTHONUNBUFFERED=1

title Polymarket Scout - 闪电侦察行动
echo [Mikon AI Army] 正在按最新配置执行闪电侦察...
echo.

:: 直接运行核心侦察脚本
python scout.py

echo.
echo 侦察结束！结果已保存至 markets_list.txt
pause
