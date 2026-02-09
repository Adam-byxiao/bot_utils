#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI多次KWS触发逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from KWS_calculate import KWSCalculator

def test_gui_multiple_triggers():
    """测试GUI多次KWS触发"""
    
    # 创建KWS计算器实例
    kws_calc = KWSCalculator("localhost", "test", "test")  # 使用测试参数
    
    # 模拟GUI的包装函数
    def create_gui_wrapper(kws_calculator):
        """创建GUI包装函数"""
        # 保存原始方法
        original_process_line = kws_calculator._process_log_line
        original_update_trigger = kws_calculator._update_trigger_status
        
        # 记录已处理的记录数量
        processed_kws_count = 0
        processed_triggered_count = 0
        processed_untriggered_count = 0
        
        def gui_process_line(line):
            nonlocal processed_kws_count, processed_triggered_count, processed_untriggered_count
            
            print(f"GUI处理日志行: {line.strip()}")
            
            # 调用原始处理方法
            original_process_line(line)
            
            # 检查是否有新的KWS识别记录
            current_kws_count = len(kws_calculator.records)
            if current_kws_count > processed_kws_count:
                print(f"检测到新的KWS识别记录: {current_kws_count - processed_kws_count} 条")
                processed_kws_count = current_kws_count
        
        def gui_update_trigger(phrase, triggered, timestamp, detailed_record=None):
            nonlocal processed_triggered_count, processed_untriggered_count
            
            print(f"GUI更新触发状态: phrase={phrase}, triggered={triggered}, timestamp={timestamp}")
            if detailed_record:
                print(f"  详细记录: label_id={detailed_record.get('predicted_label_id')}, confidence={detailed_record.get('confidence_score')}")
            
            # 调用原始方法
            original_update_trigger(phrase, triggered, timestamp, detailed_record)
            
            # 检查触发记录和未触发记录的变化
            current_triggered = len(kws_calculator.triggered_records)
            current_untriggered = len(kws_calculator.untriggered_records)
            
            # 处理新的触发记录
            if current_triggered > processed_triggered_count:
                print(f"检测到新的触发记录: {current_triggered - processed_triggered_count} 条")
                processed_triggered_count = current_triggered
            
            # 处理新的未触发记录
            if current_untriggered > processed_untriggered_count:
                print(f"检测到新的未触发记录: {current_untriggered - processed_untriggered_count} 条")
                processed_untriggered_count = current_untriggered
        
        # 替换处理方法
        kws_calculator._process_log_line = gui_process_line
        kws_calculator._update_trigger_status = gui_update_trigger
        
        return kws_calculator
    
    # 应用GUI包装
    kws_calc = create_gui_wrapper(kws_calc)
    
    # 模拟多次触发的日志数据
    test_logs = [
        # 第一次KWS识别
        "2026-02-06T06:10:40.758756Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hey_hello_vibe recognized phrase: hey_vibe, score: 0.950775, begin: 4.26744e+06, end: 4.27896e+06",
        
        # 第一次结果详情 (Label ID=1，应该触发)
        "2026-02-06T06:10:40.982660Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hey_vibe Results ---",
        "Raw Logits:        [Label 0: 6.53906, Label 1: -6.87891]",
        "Probabilities:     [Label 0: 0.999999, Label 1: 1.48816e-06]",
        "-------------------------",
        "==> Predicted Label ID: 1",
        "==> Confidence Score:   0.999999",
        "==> Preprocess Cost:    11ms",
        "==> Rknn Run Cost:      211ms",
        "==> Sum Cost:     223ms",
        
        # 第二次KWS识别
        "2026-02-06T06:11:15.123456Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hey_hello_vibe recognized phrase: hey_vibe, score: 0.982345, begin: 4.34567e+06, end: 4.35678e+06",
        
        # 第二次结果详情 (Label ID=1，应该再次触发)
        "2026-02-06T06:11:15.345678Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hey_vibe Results ---",
        "Raw Logits:        [Label 0: -2.34567, Label 1: 8.91234]",
        "Probabilities:     [Label 0: 0.000123, Label 1: 0.999877]",
        "-------------------------",
        "==> Predicted Label ID: 1",
        "==> Confidence Score:   0.999877",
        "==> Preprocess Cost:    15ms",
        "==> Rknn Run Cost:      198ms",
        "==> Sum Cost:     213ms",
        
        # 第三次KWS识别
        "2026-02-06T06:12:30.987654Z INFO vibe-ai-server: [kws_sensory.cc(257)] Model: hey_hello_vibe recognized phrase: hey_vibe, score: 0.873456, begin: 4.56789e+06, end: 4.57890e+06",
        
        # 第三次结果详情 (Label ID=0，不应该触发)
        "2026-02-06T06:12:31.234567Z INFO vibe-ai-server: [kws_sensory.cc(914)] --- Model:hey_vibe Results ---",
        "Raw Logits:        [Label 0: 7.12345, Label 1: -5.67890]",
        "Probabilities:     [Label 0: 0.999876, Label 1: 0.000124]",
        "-------------------------",
        "==> Predicted Label ID: 0",
        "==> Confidence Score:   0.999876",
        "==> Preprocess Cost:    12ms",
        "==> Rknn Run Cost:      205ms",
        "==> Sum Cost:     217ms"
    ]
    
    print("🧪 测试GUI多次KWS触发逻辑")
    print("="*60)
    print("预期结果: 2次触发 (Label ID=1), 1次未触发 (Label ID=0)")
    print("="*60)
    
    # 设置连接开始时间为第一个日志的时间之前
    kws_calc.connection_start_time = "2026-02-06T06:10:00.000000Z"
    
    # 处理所有日志行
    for i, log_line in enumerate(test_logs):
        print(f"\n📝 处理日志行 {i+1}:")
        print(f"   {log_line[:80]}..." if len(log_line) > 80 else f"   {log_line}")
        
        kws_calc._process_log_line(log_line)
    
    print(f"\n📊 最终结果统计:")
    print(f"   总记录数: {len(kws_calc.records)}")
    print(f"   触发记录数: {len(kws_calc.triggered_records)}")
    print(f"   未触发记录数: {len(kws_calc.untriggered_records)}")
    
    print(f"\n🔍 详细记录信息:")
    for i, record in enumerate(kws_calc.records):
        status = "✅ 触发" if record.triggered else "❌ 未触发"
        print(f"\n  记录 {i+1} - {status}:")
        print(f"    时间戳: {record.timestamp}")
        print(f"    唤醒词: {record.phrase}")
        print(f"    分数: {record.score}")
        if hasattr(record, 'predicted_label_id') and record.predicted_label_id is not None:
            print(f"    预测标签ID: {record.predicted_label_id}")
            print(f"    置信度分数: {record.confidence_score}")
        print(f"    是否触发: {record.triggered}")
    
    # 验证结果
    expected_triggers = 2
    expected_untriggers = 1
    
    if (len(kws_calc.triggered_records) == expected_triggers and 
        len(kws_calc.untriggered_records) == expected_untriggers):
        print(f"\n🎉 GUI测试通过! 成功检测到 {expected_triggers} 次触发和 {expected_untriggers} 次未触发")
    else:
        print(f"\n❌ GUI测试失败! 预期 {expected_triggers} 次触发和 {expected_untriggers} 次未触发")
        print(f"   实际结果: {len(kws_calc.triggered_records)} 次触发, {len(kws_calc.untriggered_records)} 次未触发")

if __name__ == "__main__":
    test_gui_multiple_triggers()