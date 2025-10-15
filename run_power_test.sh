#!/bin/bash

# 设备上下电压测试工具启动脚本

echo "========================================"
echo "设备上下电压测试工具"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查必要文件
if [ ! -f "device_power_test.py" ]; then
    echo "错误: 未找到 device_power_test.py 文件"
    exit 1
fi

if [ ! -f "device_power_test_config.py" ]; then
    echo "错误: 未找到 device_power_test_config.py 文件"
    exit 1
fi

# 检查ADB
if ! command -v adb &> /dev/null; then
    echo "警告: 未找到ADB工具"
    echo "请确保已安装ADB并添加到系统PATH"
    echo
    read -p "是否继续? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

echo "开始运行设备上下电压测试..."
echo

# 运行测试
python3 run_power_test.py "$@"

echo
echo "测试完成"
