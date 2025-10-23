#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查原始备份文件的时间戳格式
"""

import json

def main():
    # 读取原始备份数据
    with open('kws_analysis/realtime_parse_info_20251017_102600_backup.json', 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    print('原始备份文件时间戳分析:')
    print('=' * 50)

    # 检查时间戳格式
    beijing_time_records = []
    utc_time_records = []

    for i, record in enumerate(backup_data):
        timestamp = record['timestamp']
        hour = int(timestamp.split(' ')[1].split(':')[0])
        
        if hour >= 18:  # 可能是北京时间
            beijing_time_records.append((i, timestamp))
        else:  # 可能是 UTC 时间
            utc_time_records.append((i, timestamp))

    print(f'总记录数: {len(backup_data)}')
    print(f'疑似北京时间记录数: {len(beijing_time_records)}')
    print(f'疑似 UTC 时间记录数: {len(utc_time_records)}')

    print()
    print('前 5 个记录的时间戳:')
    for i in range(5):
        print(f'  记录 {i}: {backup_data[i]["timestamp"]}')

    print()
    print('中间 5 个记录的时间戳 (7010-7014):')
    for i in range(7010, 7015):
        print(f'  记录 {i}: {backup_data[i]["timestamp"]}')

if __name__ == "__main__":
    main()