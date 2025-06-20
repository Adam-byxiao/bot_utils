#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文字体支持
"""

import matplotlib.pyplot as plt
import numpy as np
import platform
import matplotlib.font_manager as fm

def setup_chinese_font():
    """设置中文字体支持"""
    # 根据操作系统设置合适的中文字体
    system = platform.system()
    
    if system == 'Windows':
        # Windows系统字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi']
    elif system == 'Darwin':  # macOS
        # macOS系统字体
        chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti']
    else:  # Linux
        # Linux系统字体
        chinese_fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Liberation Sans']
    
    # 检查可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    print(f"系统: {system}")
    print(f"可用字体数量: {len(available_fonts)}")
    
    for font in chinese_fonts:
        if font in available_fonts:
            print(f"找到中文字体: {font}")
            plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
            break
    else:
        print("未找到合适的中文字体，使用默认字体")
    
    plt.rcParams['axes.unicode_minus'] = False

def test_chinese_display():
    """测试中文显示"""
    setup_chinese_font()
    
    # 创建测试图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # 生成测试数据
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    
    # 绘制波形图
    ax1.plot(x, y1, label='正弦波', color='blue')
    ax1.plot(x, y2, label='余弦波', color='red')
    ax1.set_title('音频波形图测试 - 中文字体支持')
    ax1.set_xlabel('时间 (秒)')
    ax1.set_ylabel('振幅')
    ax1.legend()
    ax1.grid(True)
    
    # 绘制频谱图
    ax2.specgram(y1, Fs=10, cmap='viridis')
    ax2.set_title('频谱图测试 - 中文标题')
    ax2.set_xlabel('时间 (秒)')
    ax2.set_ylabel('频率 (Hz)')
    
    plt.tight_layout()
    plt.show()
    
    print("中文字体测试完成！如果图表中的中文标题正常显示，说明字体设置成功。")

if __name__ == "__main__":
    test_chinese_display() 