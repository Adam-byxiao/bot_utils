#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的KWS日志格式解析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from KWS_calculate import KWSLogParser

def test_new_log_format():
    """测试新的日志格式解析"""
    parser = KWSLogParser()
    
    # 测试新的日志格式
    test_lines = [
        # 标准KWS识别行
        "2026-02-06T06:10:40.758756Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hey_hello_vibe recognized phrase: hey_vibe, score: 0.950775, begin: 4.26744e+06, end: 4.27896e+06",
        
        # 新的结果详情行
        "2026-02-06T06:10:40.982660Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hey_vibe Results --- ",
        "Raw Logits:        [Label 0: 6.53906, Label 1: -6.87891] ",
        "Probabilities:     [Label 0: 0.999999, Label 1: 1.48816e-06] ",
        "------------------------- ",
        "==> Predicted Label ID: 0 ",
        "==> Confidence Score:   0.999999 ",
        "==> Preprocess Cost:    11ms ",
        "==> Rknn Run Cost:      211ms ",
        "==> Sum Cost:     223ms",
        
        # 另一个结果详情行 (Label ID为1)
        "2026-02-06T06:11:15.123456Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hello_vibe Results --- ",
        "Raw Logits:        [Label 0: -2.34567, Label 1: 8.91234] ",
        "Probabilities:     [Label 0: 0.000123, Label 1: 0.999877] ",
        "------------------------- ",
        "==> Predicted Label ID: 1 ",
        "==> Confidence Score:   0.999877 ",
        "==> Preprocess Cost:    15ms ",
        "==> Rknn Run Cost:      198ms ",
        "==> Sum Cost:     213ms"
    ]
    
    print("🧪 测试新的KWS日志格式解析")
    print("="*60)
    
    for i, line in enumerate(test_lines):
        print(f"\n📝 测试行 {i+1}:")
        print(f"   {line}")
        
        # 尝试解析KWS识别行
        kws_data = parser.parse_kws_line(line)
        if kws_data:
            print("   ✅ KWS识别行解析成功:")
            print(f"      时间戳: {kws_data['timestamp']}")
            print(f"      模型: {kws_data['model']}")
            print(f"      唤醒词: {kws_data['phrase']}")
            print(f"      分数: {kws_data['score']}")
            print(f"      开始时间: {kws_data['begin']}")
            print(f"      结束时间: {kws_data['end']}")
            continue
        
        # 尝试解析结果详情行
        results_data = parser.parse_results_line(line)
        if results_data:
            print("   ✅ 结果详情行解析成功:")
            print(f"      时间戳: {results_data['timestamp']}")
            print(f"      模型: {results_data['model']}")
            print(f"      预测标签ID: {results_data['predicted_label_id']}")
            print(f"      置信度分数: {results_data['confidence_score']}")
            print(f"      原始Logits: {results_data['raw_logits']}")
            print(f"      概率分布: {results_data['probabilities']}")
            print(f"      预处理耗时: {results_data['preprocess_cost']}ms")
            print(f"      RKNN运行耗时: {results_data['rknn_run_cost']}ms")
            print(f"      总耗时: {results_data['sum_cost']}ms")
            print(f"      是否触发: {results_data['triggered']}")
            continue
            
        print("   ❌ 无法解析此行")

if __name__ == "__main__":
    test_new_log_format()