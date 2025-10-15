#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS计算工具使用示例
演示如何使用KWS_calculate.py进行语音唤醒词监控
"""

import time
import threading
import json
from KWS_calculate import KWSCalculator

def example_basic_monitoring():
    """基本监控示例"""
    print("=== 基本监控示例 ===")
    
    # 配置连接参数
    host = "192.168.1.100"  # 替换为实际设备IP
    username = "root"       # 替换为实际用户名
    password = "password"   # 替换为实际密码
    
    # 创建KWS计算器
    kws_calc = KWSCalculator(host, username, password)
    
    try:
        # 连接设备
        if not kws_calc.connect():
            print("连接失败")
            return
        
        print("连接成功，开始监控30秒...")
        
        # 在单独线程中开始监控
        monitor_thread = threading.Thread(target=kws_calc.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 监控30秒
        time.sleep(30)
        
        # 停止监控
        kws_calc.stop_monitoring()
        monitor_thread.join(timeout=5)
        
        # 导出结果
        kws_calc.export_results()
        kws_calc.print_summary()
        
    finally:
        kws_calc.disconnect()

def example_with_config():
    """使用配置文件的示例"""
    print("=== 配置文件示例 ===")
    
    # 读取配置文件
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("配置文件不存在，使用默认配置")
        config = {
            "ssh_connection": {
                "host": "192.168.1.100",
                "username": "root",
                "password": "password",
                "port": 22
            }
        }
    
    # 从配置创建KWS计算器
    ssh_config = config["ssh_connection"]
    kws_calc = KWSCalculator(
        ssh_config["host"],
        ssh_config["username"],
        ssh_config["password"],
        ssh_config["port"]
    )
    
    try:
        if kws_calc.connect():
            print("使用配置文件连接成功")
            # 这里可以添加监控逻辑
        else:
            print("连接失败")
    finally:
        kws_calc.disconnect()

def example_custom_analysis():
    """自定义分析示例"""
    print("=== 自定义分析示例 ===")
    
    # 模拟一些测试数据
    from KWS_calculate import KWSRecord
    from datetime import datetime
    
    # 创建测试记录
    test_records = [
        KWSRecord(
            timestamp="2025-10-14T07:36:02.463710Z",
            phrase="hello_vibe",
            score=0.947266,
            begin_time=560400,
            end_time=571200,
            triggered=False,
            raw_log="test log 1"
        ),
        KWSRecord(
            timestamp="2025-10-14T07:36:05.886235Z",
            phrase="hello_vibe",
            score=0.992218,
            begin_time=616800,
            end_time=628320,
            triggered=True,
            raw_log="test log 2"
        )
    ]
    
    # 分析数据
    total_records = len(test_records)
    triggered_records = [r for r in test_records if r.triggered]
    untriggered_records = [r for r in test_records if not r.triggered]
    
    print(f"总记录数: {total_records}")
    print(f"触发记录数: {len(triggered_records)}")
    print(f"未触发记录数: {len(untriggered_records)}")
    
    if total_records > 0:
        trigger_rate = len(triggered_records) / total_records * 100
        print(f"触发率: {trigger_rate:.2f}%")
        
        # 分数分析
        all_scores = [r.score for r in test_records]
        avg_score = sum(all_scores) / len(all_scores)
        print(f"平均分数: {avg_score:.4f}")
        
        if triggered_records:
            triggered_scores = [r.score for r in triggered_records]
            avg_triggered_score = sum(triggered_scores) / len(triggered_scores)
            print(f"触发记录平均分数: {avg_triggered_score:.4f}")

def example_real_time_analysis():
    """实时分析示例"""
    print("=== 实时分析示例 ===")
    
    class RealTimeAnalyzer:
        def __init__(self):
            self.score_threshold = 0.9
            self.low_score_count = 0
            self.high_score_count = 0
        
        def analyze_record(self, record):
            """分析单条记录"""
            if record.score < self.score_threshold:
                self.low_score_count += 1
                print(f"低分数记录: {record.phrase}, score: {record.score}")
            else:
                self.high_score_count += 1
                print(f"高分数记录: {record.phrase}, score: {record.score}")
        
        def get_stats(self):
            """获取统计信息"""
            total = self.low_score_count + self.high_score_count
            if total > 0:
                high_score_rate = self.high_score_count / total * 100
                return {
                    'total': total,
                    'high_score_count': self.high_score_count,
                    'low_score_count': self.low_score_count,
                    'high_score_rate': high_score_rate
                }
            return {'total': 0}
    
    analyzer = RealTimeAnalyzer()
    
    # 模拟实时数据处理
    from KWS_calculate import KWSRecord
    test_data = [
        ("hello_vibe", 0.85),
        ("hello_vibe", 0.95),
        ("hello_vibe", 0.88),
        ("hello_vibe", 0.92)
    ]
    
    for phrase, score in test_data:
        record = KWSRecord(
            timestamp="2025-10-14T07:36:02.463710Z",
            phrase=phrase,
            score=score,
            begin_time=560400,
            end_time=571200,
            triggered=score > 0.9,
            raw_log=f"test log for {phrase}"
        )
        analyzer.analyze_record(record)
    
    stats = analyzer.get_stats()
    print(f"分析结果: {stats}")

def main():
    """主函数 - 运行所有示例"""
    print("KWS计算工具使用示例")
    print("=" * 50)
    
    examples = [
        ("基本监控示例", example_basic_monitoring),
        ("配置文件示例", example_with_config),
        ("自定义分析示例", example_custom_analysis),
        ("实时分析示例", example_real_time_analysis)
    ]
    
    for name, func in examples:
        print(f"\n运行 {name}...")
        try:
            func()
        except Exception as e:
            print(f"示例 {name} 运行出错: {e}")
        print("-" * 30)
    
    print("\n所有示例运行完成！")

if __name__ == "__main__":
    main()