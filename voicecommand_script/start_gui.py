#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS GUI 启动脚本
提供依赖检查和错误处理
"""

import sys
import os

def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []
    
    try:
        import wx
    except ImportError:
        missing_deps.append("wxPython")
    
    try:
        import paramiko
    except ImportError:
        missing_deps.append("paramiko")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    return missing_deps

def install_dependencies(deps):
    """安装缺失的依赖"""
    print("检测到缺失的依赖包，正在安装...")
    for dep in deps:
        print(f"安装 {dep}...")
        os.system(f"pip install {dep}")

def main():
    """主函数"""
    print("KWS 语音唤醒词监控工具 GUI")
    print("=" * 40)
    
    # 检查依赖
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"缺失依赖: {', '.join(missing_deps)}")
        response = input("是否自动安装？(y/n): ")
        if response.lower() in ['y', 'yes', '是']:
            install_dependencies(missing_deps)
        else:
            print("请手动安装依赖后重试:")
            print("pip install -r requirements.txt")
            return
    
    # 启动GUI
    try:
        print("启动GUI界面...")
        from KWS_GUI import KWSApp
        app = KWSApp()
        app.MainLoop()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有文件都在同一目录下")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()