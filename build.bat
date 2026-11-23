@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem ============================================================
rem  CipherBox 打包脚本：生成单文件 exe -> dist\CipherBox.exe
rem  中间文件放在 build\ 目录，可以随时删除
rem ============================================================

set "APP_NAME=CipherBox"
set "ROOT=%~dp0"
set "ICON=%ROOT%build\app.ico"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 没有找到 python，请先安装 Python 3.10+ 并加入 PATH
    goto :fail
)

echo [1/4] 检查依赖...
python -c "import PyQt5, cryptography, bcrypt" >nul 2>nul
if errorlevel 1 (
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
)
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo       未安装 PyInstaller，正在安装...
    python -m pip install pyinstaller
    if errorlevel 1 goto :fail
)

echo [2/4] 运行测试...
python -c "import pytest" >nul 2>nul
if errorlevel 1 (
    echo       未安装 pytest，跳过测试
) else (
    python -m pytest -q
    if errorlevel 1 (
        echo [错误] 测试没有通过，已停止打包
        goto :fail
    )
)

echo [3/4] 生成图标...
python tools\make_icon.py "%ICON%"
if errorlevel 1 goto :fail

echo [4/4] PyInstaller 打包：单文件、无控制台窗口，大约需要一两分钟...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "%APP_NAME%" ^
    --icon "%ICON%" ^
    --add-data "%ROOT%gui\assets;gui\assets" ^
    --distpath "%ROOT%dist" ^
    --workpath "%ROOT%build\pyinstaller" ^
    --specpath "%ROOT%build" ^
    main.py
if errorlevel 1 goto :fail

echo.
echo 打包完成：%ROOT%dist\%APP_NAME%.exe
pause
exit /b 0

:fail
echo.
echo [失败] 打包没有完成，请查看上面的错误信息
pause
exit /b 1
