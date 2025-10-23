#!/usr/bin/env python3
"""
语音代理监控GUI启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import wx
except ImportError:
    print("错误: 未安装wxPython")
    print("请运行: pip install wxpython")
    sys.exit(1)

from voice_monitor_gui import main

if __name__ == "__main__":
    print("启动语音代理监控GUI...")
    print("使用前请确保:")
    print("1. 已建立SSH端口转发: ssh root@device_ip -L 9222:localhost:9222")
    print("2. Chrome已启动调试模式: chrome --remote-debugging-port=9222")
    print("3. 在chrome://inspect中打开Bot Controller的DevTools")
    print()
    
    main()