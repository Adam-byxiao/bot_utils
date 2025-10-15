@echo off
chcp 65001 >nul
title 设备上下电压测试工具

echo ========================================
echo 设备上下电压测试工具
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 检查必要文件
if not exist "device_power_test.py" (
    echo 错误: 未找到 device_power_test.py 文件
    pause
    exit /b 1
)

if not exist "device_power_test_config.py" (
    echo 错误: 未找到 device_power_test_config.py 文件
    pause
    exit /b 1
)

:: 检查ADB
adb version >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到ADB工具
    echo 请确保已安装ADB并添加到系统PATH
    echo.
    set /p continue="是否继续? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

echo 开始运行设备上下电压测试...
echo.

:: 运行测试
python run_power_test.py %*

echo.
echo 测试完成，按任意键退出...
pause >nul
