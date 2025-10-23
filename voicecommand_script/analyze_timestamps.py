#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 KWS 和 TTS 时间戳的关系
"""

from datetime import datetime, timedelta
import json

def main():
    # 读取原始 TTS 数据
    with open('kws_analysis/realtime_parse_info_20251017_102600.json', 'r', encoding='utf-8') as f:
        tts_data = json.load(f)

    print('时间戳关系分析:')
    print('=' * 50)

    # TTS 原始时间戳（北京时间）
    tts_time_str = tts_data[0]['timestamp']
    print(f'TTS 原始时间戳: {tts_time_str} (北京时间)')

    # KWS 时间戳（UTC）
    kws_time_str = '2025-10-16T10:12:41.278247Z'
    print(f'KWS 时间戳: {kws_time_str} (UTC)')

    # 将 KWS UTC 时间转换为北京时间进行比较
    kws_time_utc = datetime.fromisoformat(kws_time_str.rstrip('Z'))
    kws_time_beijing = kws_time_utc + timedelta(hours=8)
    print(f'KWS 转换为北京时间: {kws_time_beijing.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]}')

    # 解析 TTS 北京时间
    tts_time_beijing = datetime.strptime(tts_time_str, '%Y/%m/%d %H:%M:%S.%f')
    print(f'TTS 北京时间: {tts_time_beijing.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]}')

    # 计算时间差
    time_diff = (kws_time_beijing - tts_time_beijing).total_seconds()
    print(f'时间差: {time_diff:.3f} 秒')

    print()
    print('结论:')
    print('KWS 时间戳是 UTC 时间，TTS 时间戳是北京时间')
    print('需要将 TTS 时间戳转换为 UTC 时间（减去 8 小时）才能匹配')
    
    print()
    print('正确的转换方向:')
    # 将 TTS 北京时间转换为 UTC 时间
    tts_time_utc = tts_time_beijing - timedelta(hours=8)
    print(f'TTS 转换为 UTC: {tts_time_utc.strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]}')
    
    # 重新计算时间差
    time_diff_utc = (kws_time_utc - tts_time_utc).total_seconds()
    print(f'UTC 时间差: {time_diff_utc:.3f} 秒')
    print(f'是否在匹配阈值内: {abs(time_diff_utc) <= 2.0}')

if __name__ == "__main__":
    main()