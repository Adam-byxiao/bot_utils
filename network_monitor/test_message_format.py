#!/usr/bin/env python3
"""
测试脚本：查看实际的消息内容格式
"""

import asyncio
import json
from remote_voice_agent_monitor import RemoteVoiceAgentMonitor

async def test_message_format():
    """测试消息格式"""
    monitor = RemoteVoiceAgentMonitor()
    
    try:
        # 连接到设备
        print("正在连接到设备...")
        success = await monitor.connect_to_remote_device()
        if not success:
            print("连接失败！")
            return
        print("连接成功！")
        
        # 获取历史数据
        print("\n获取历史数据...")
        history_data = await monitor.get_session_history()
        
        if history_data:
            print(f"获取到 {len(history_data)} 条历史记录")
            
            # 显示前几条原始数据
            print("\n=== 原始数据格式 ===")
            for i, item in enumerate(history_data[:3]):  # 只显示前3条
                print(f"\n第 {i+1} 条消息:")
                print(json.dumps(item, ensure_ascii=False, indent=2))
                
            # 解析数据
            print("\n=== 解析后的数据 ===")
            input_messages, output_messages, session_summary = monitor.parse_and_classify_data(history_data)
            
            print(f"输入消息: {len(input_messages)} 条")
            for i, msg in enumerate(input_messages[:2]):  # 只显示前2条
                print(f"\n输入消息 {i+1}:")
                print(f"  内容: {msg.content}")
                print(f"  原始数据: {json.dumps(msg.raw_data, ensure_ascii=False, indent=2)}")
                
            print(f"\n输出消息: {len(output_messages)} 条")
            for i, msg in enumerate(output_messages[:2]):  # 只显示前2条
                print(f"\n输出消息 {i+1}:")
                print(f"  内容: {msg.content}")
                print(f"  原始数据: {json.dumps(msg.raw_data, ensure_ascii=False, indent=2)}")
        else:
            print("没有获取到历史数据")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_message_format())