#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 时间戳转换脚本
将 TTS 数据文件中的时间戳从北京时间转换为 UTC 时间（增加 8 小时）
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def convert_timestamp_to_utc(timestamp_str):
    """
    将北京时间时间戳转换为 UTC 时间
    只转换北京时间格式的记录（小时 >= 10），保持 UTC 时间记录不变
    输入格式: "2025/10/16 18:12:40.104"
    输出格式: "2025/10/16 10:12:40.104"
    """
    try:
        # 解析时间戳
        dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S.%f")
        
        # 检查是否是北京时间（小时 >= 10，通常北京时间在 10:xx-23:xx 范围）
        # UTC 时间通常在 00:xx-09:xx 范围
        if dt.hour >= 10:
            # 这是北京时间，需要转换为 UTC 时间
            utc_dt = dt - timedelta(hours=8)
            converted = utc_dt.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]  # 保留3位毫秒
            return converted
        else:
            # 这已经是 UTC 时间，不需要转换
            return timestamp_str
            
    except Exception as e:
        print(f"时间戳转换错误: {timestamp_str}, 错误: {e}")
        return timestamp_str  # 如果转换失败，返回原始时间戳

def convert_tts_file(input_file, output_file=None):
    """
    转换 TTS 数据文件中的所有时间戳
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return False
    
    # 如果没有指定输出文件，则覆盖原文件
    if output_file is None:
        output_file = input_file
    
    try:
        # 读取原始数据
        print(f"正在读取文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"文件包含 {len(data)} 条记录")
        
        # 转换时间戳
        converted_count = 0
        for record in data:
            if 'timestamp' in record:
                original_timestamp = record['timestamp']
                converted_timestamp = convert_timestamp_to_utc(original_timestamp)
                record['timestamp'] = converted_timestamp
                converted_count += 1
                
                # 显示前几个转换示例
                if converted_count <= 5:
                    print(f"转换示例 {converted_count}: {original_timestamp} -> {converted_timestamp}")
        
        # 保存转换后的数据
        print(f"正在保存到文件: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"转换完成! 共转换了 {converted_count} 条时间戳记录")
        return True
        
    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python convert_tts_timestamps.py <输入文件> [输出文件]")
        print("如果不指定输出文件，将覆盖原文件")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=" * 60)
    print("TTS 时间戳转换工具")
    print("将北京时间转换为 UTC 时间（-8小时）")
    print("=" * 60)
    
    success = convert_tts_file(input_file, output_file)
    
    if success:
        print("\n✅ 转换成功完成!")
    else:
        print("\n❌ 转换失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()