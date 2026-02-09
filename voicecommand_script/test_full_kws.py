#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的KWS监控流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from KWS_calculate import KWSCalculator

def test_kws_monitoring():
    """测试KWS监控流程"""
    
    # 创建KWS计算器实例
    kws_calc = KWSCalculator("localhost", "test", "test")  # 使用测试参数
    
    # 模拟日志数据
    test_logs = [
        # KWS识别行
        "2026-02-06T06:10:40.758756Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hey_hello_vibe recognized phrase: hey_vibe, score: 0.950775, begin: 4.26744e+06, end: 4.27896e+06",
        
        # 结果详情行（多行）
        "2026-02-06T06:10:40.982660Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hey_vibe Results ---",
        "Raw Logits:        [Label 0: 6.53906, Label 1: -6.87891]",
        "Probabilities:     [Label 0: 0.999999, Label 1: 1.48816e-06]",
        "-------------------------",
        "==> Predicted Label ID: 0",
        "==> Confidence Score:   0.999999",
        "==> Preprocess Cost:    11ms",
        "==> Rknn Run Cost:      211ms",
        "==> Sum Cost:     223ms",
        
        # 另一个KWS识别行
        "2026-02-06T06:11:15.123456Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hello_vibe recognized phrase: hello_vibe, score: 0.982345, begin: 4.34567e+06, end: 4.35678e+06",
        
        # 另一个结果详情行 (Label ID为1)
        "2026-02-06T06:11:15.345678Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hello_vibe Results ---",
        "Raw Logits:        [Label 0: -2.34567, Label 1: 8.91234]",
        "Probabilities:     [Label 0: 0.000123, Label 1: 0.999877]",
        "-------------------------",
        "==> Predicted Label ID: 1",
        "==> Confidence Score:   0.999877",
        "==> Preprocess Cost:    15ms",
        "==> Rknn Run Cost:      198ms",
        "==> Sum Cost:     213ms"
    ]
    
    print("🧪 测试完整的KWS监控流程")
    print("="*60)
    
    # 设置连接开始时间为第一个日志的时间之前
    kws_calc.connection_start_time = "2026-02-06T06:10:00.000000Z"
    
    # 处理所有日志行
    for i, log_line in enumerate(test_logs):
        print(f"\n📝 处理日志行 {i+1}:")
        print(f"   {log_line[:80]}..." if len(log_line) > 80 else f"   {log_line}")
        
        kws_calc._process_log_line(log_line)
    
    print(f"\n📊 处理结果统计:")
    print(f"   总记录数: {len(kws_calc.records)}")
    print(f"   触发记录数: {len(kws_calc.triggered_records)}")
    print(f"   未触发记录数: {len(kws_calc.untriggered_records)}")
    
    print(f"\n🔍 详细记录信息:")
    for i, record in enumerate(kws_calc.records):
        print(f"\n  记录 {i+1}:")
        print(f"    时间戳: {record.timestamp}")
        print(f"    唤醒词: {record.phrase}")
        print(f"    分数: {record.score}")
        print(f"    是否触发: {record.triggered}")
        if hasattr(record, 'predicted_label_id') and record.predicted_label_id is not None:
            print(f"    预测标签ID: {record.predicted_label_id}")
            print(f"    置信度分数: {record.confidence_score}")
            print(f"    预处理耗时: {record.preprocess_cost}ms")
            print(f"    RKNN运行耗时: {record.rknn_run_cost}ms")
            print(f"    总耗时: {record.sum_cost}ms")
    
    # 测试导出功能
    print(f"\n💾 测试导出功能:")
    try:
        kws_calc.export_results()
        print("✅ 导出功能正常")
    except Exception as e:
        print(f"❌ 导出功能出错: {e}")

if __name__ == "__main__":
    test_kws_monitoring()