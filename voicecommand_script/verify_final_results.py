#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最终的 KWS 错误分析结果
"""

import pandas as pd

def main():
    # 读取最新的分析结果
    df = pd.read_csv('kws_error_analysis_20251017_143646.csv')
    
    print('最新 KWS 错误分析结果详细验证:')
    print('=' * 50)
    print(f'总记录数: {len(df)}')
    print()
    
    # 错误类型统计
    print('错误类型分布:')
    error_counts = df['error_type'].value_counts()
    for error_type, count in error_counts.items():
        percentage = (count / len(df)) * 100
        print(f'  {error_type}: {count} 条 ({percentage:.1f}%)')
    print()
    
    # 检查是否有 timestamp_mismatch
    timestamp_mismatch = df[df['error_type'] == 'timestamp_mismatch']
    print(f'✅ timestamp_mismatch 记录数: {len(timestamp_mismatch)}')
    
    if len(timestamp_mismatch) == 0:
        print('🎉 时间戳匹配问题已完全解决！')
    
    print()
    print('前 3 条记录示例:')
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        print(f'记录 {i+1}:')
        print(f'  KWS 时间戳: {row["kws_timestamp"]}')
        print(f'  KWS 短语: {row["kws_phrase"]}')
        print(f'  错误类型: {row["error_type"]}')
        print()

if __name__ == "__main__":
    main()