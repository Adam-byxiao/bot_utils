#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音质量分析GUI工具启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from SpeechQualityAnalyzer import SpeechQualityAnalyzerApp
    import wx
    
    def main():
        """主函数"""
        app = wx.App(False)
        frame = SpeechQualityAnalyzerApp()
        app.MainLoop()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所需的依赖包:")
    print("pip install wxPython numpy scipy matplotlib librosa soundfile dtw")
    input("按回车键退出...")
except Exception as e:
    print(f"运行错误: {e}")
    input("按回车键退出...") 