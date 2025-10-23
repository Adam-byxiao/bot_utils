#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 TTS 时间戳转换结果
"""

import json

def main():
    # 读取转换后的 TTS 数据
    with open('kws_analysis/realtime_parse_info_20251017_102600.json', 'r', encoding='utf-8') as f:
        tts_data = json.load(f)

    print('验证 TTS 时间戳转换结果:')
    print('=' * 50)

    # 检查时间戳格式
    beijing_time_records = []
    utc_time_records = []

    for i, record in enumerate(tts_data):
        timestamp = record['timestamp']
        hour = int(timestamp.split(' ')[1].split(':')[0])
        
        if hour >= 18:  # 可能是北京时间
            beijing_time_records.append((i, timestamp))
        else:  # 可能是 UTC 时间
            utc_time_records.append((i, timestamp))

    print(f'总记录数: {len(tts_data)}')
    print(f'疑似北京时间记录数: {len(beijing_time_records)}')
    print(f'疑似 UTC 时间记录数: {len(utc_time_records)}')

    if beijing_time_records:
        print()
        print('⚠️ 仍有北京时间记录未转换:')
        for i, (idx, timestamp) in enumerate(beijing_time_records[:5]):
            print(f'  记录 {idx}: {timestamp}')
    else:
        print()
        print('✅ 所有时间戳都已转换为 UTC 时间!')

    print()
    print('转换后的时间戳示例:')
    for i in range(5):
        print(f'  记录 {i}: {tts_data[i]["timestamp"]}')

if __name__ == "__main__":
    main()