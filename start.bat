@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem ============================================================
rem  CipherBox 调试启动脚本
rem    start.bat        带控制台启动程序，报错信息直接显示在这个窗口
rem    start.bat test   运行全部自动化测试
rem ============================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 没有找到 python，请先安装 Python 3.10+ 并加入 PATH
    goto :fail
)

python -c "import PyQt5, cryptography, bcrypt" >nul 2>nul
if errorlevel 1 (
    echo [提示] 缺少依赖，正在安装 requirements.txt ...
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
)

rem 调试选项：程序崩溃时打印 Python 调用栈；输出不缓冲，日志即时可见
set "PYTHONFAULTHANDLER=1"
set "PYTHONUNBUFFERED=1"

if /i "%~1"=="test" goto :test

echo 正在启动 CipherBox（调试模式，关闭程序窗口后返回）...
python main.py
if errorlevel 1 goto :fail
exit /b 0

:test
echo 正在运行测试...
python -m pytest -v
if errorlevel 1 goto :fail
pause
exit /b 0

:fail
echo.
echo [失败] 请查看上面的错误信息
pause
exit /b 1
