#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS错误分析工具启动脚本
提供简化的接口来运行KWS测试错误分析
"""

import os
import sys
import glob
from kws_error_analyzer import KWSErrorAnalyzer

def find_latest_files():
    """
    自动查找最新的TTS和KWS文件
    
    Returns:
        tuple: (tts_file, kws_file) 或 (None, None)
    """
    # 查找TTS JSON文件
    tts_pattern = os.path.join("..", "realtime_parse_info_*.json")
    tts_files = glob.glob(tts_pattern)
    
    # 查找KWS CSV文件
    kws_pattern = os.path.join("kws_output", "kws_data_*.csv")
    kws_files = glob.glob(kws_pattern)
    
    if not tts_files:
        print("未找到TTS记录文件 (realtime_parse_info_*.json)")
        return None, None
    
    if not kws_files:
        print("未找到KWS记录文件 (kws_output/kws_data_*.csv)")
        return None, None
    
    # 选择最新的文件
    latest_tts = max(tts_files, key=os.path.getmtime)
    latest_kws = max(kws_files, key=os.path.getmtime)
    
    return latest_tts, latest_kws

def main():
    """主函数"""
    print("KWS测试错误分析工具")
    print("=" * 40)
    
    # 检查命令行参数
    if len(sys.argv) == 3:
        # 用户指定了文件路径
        tts_file = sys.argv[1]
        kws_file = sys.argv[2]
    else:
        # 自动查找最新文件
        print("正在自动查找最新的TTS和KWS文件...")
        tts_file, kws_file = find_latest_files()
        
        if not tts_file or not kws_file:
            print("\n使用方法:")
            print("1. 自动模式: python run_kws_error_analysis.py")
            print("2. 手动模式: python run_kws_error_analysis.py <TTS_JSON_FILE> <KWS_CSV_FILE>")
            print("\n示例:")
            print("python run_kws_error_analysis.py ../realtime_parse_info_20251016_152145.json kws_output/kws_data_20251015_161706.csv")
            sys.exit(1)
    
    # 检查文件是否存在
    if not os.path.exists(tts_file):
        print(f"错误: TTS文件不存在: {tts_file}")
        sys.exit(1)
    
    if not os.path.exists(kws_file):
        print(f"错误: KWS文件不存在: {kws_file}")
        sys.exit(1)
    
    print(f"TTS文件: {tts_file}")
    print(f"KWS文件: {kws_file}")
    print("-" * 40)
    
    # 创建分析器并执行分析
    analyzer = KWSErrorAnalyzer()
    
    # 加载数据
    print("正在加载数据文件...")
    if not analyzer.load_tts_records(tts_file):
        print("加载TTS记录失败")
        sys.exit(1)
    
    if not analyzer.load_kws_records(kws_file):
        print("加载KWS记录失败")
        sys.exit(1)
    
    # 执行分析
    print("正在执行错误分析...")
    analyzer.analyze_records()
    
    # 保存结果
    print("正在保存分析结果...")
    output_file = analyzer.save_error_analysis()
    
    # 打印摘要
    analyzer.print_summary()
    
    if output_file:
        print(f"\n✅ 分析完成！")
        print(f"📄 错误分析结果已保存到: {output_file}")
        
        # 如果有错误记录，提示用户查看
        if analyzer.error_records:
            print(f"⚠️  发现 {len(analyzer.error_records)} 条错误记录，请查看输出文件了解详情")
        else:
            print("✅ 未发现错误记录，测试结果良好")
    else:
        print("❌ 保存分析结果失败")

if __name__ == "__main__":
    main()