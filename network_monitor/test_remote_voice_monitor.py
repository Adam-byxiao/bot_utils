"""
测试远程语音代理监控器
用于测试新增的远程设备连接和数据解析功能
"""

import asyncio
import json
import logging
from datetime import datetime

from remote_voice_agent_monitor import RemoteVoiceAgentMonitor
from realtime_voice_agent_parser import RealtimeVoiceAgentParser, VoiceMessage
from voice_data_exporter import VoiceDataExporter


def test_voice_message_parser():
    """测试语音消息解析器"""
    print("=== 测试语音消息解析器 ===")
    
    # 模拟 realtimeVoiceAgent.session.history 数据
    mock_history_data = [
        {
            "timestamp": "2024-01-15T10:30:00.000Z",
            "type": "user_input",
            "role": "user",
            "content": "你好，请帮我查询今天的天气",
            "metadata": {"source": "voice", "duration": 2.5}
        },
        {
            "timestamp": "2024-01-15T10:30:02.000Z",
            "type": "assistant_response",
            "role": "assistant", 
            "content": "您好！我来帮您查询今天的天气情况。请问您想查询哪个城市的天气？",
            "metadata": {"confidence": 0.95, "response_time": 1.2}
        },
        {
            "timestamp": "2024-01-15T10:30:05.000Z",
            "type": "user_input",
            "role": "user",
            "content": "北京的天气",
            "metadata": {"source": "voice", "duration": 1.8}
        },
        {
            "timestamp": "2024-01-15T10:30:07.000Z",
            "type": "assistant_response",
            "role": "assistant",
            "content": "北京今天多云，气温15-25度，东南风3-4级，适合外出活动。",
            "metadata": {"confidence": 0.92, "response_time": 1.5}
        }
    ]
    
    try:
        # 创建解析器
        parser = RealtimeVoiceAgentParser()
        
        # 解析数据
        parse_success = parser.parse_history_data(mock_history_data)
        if not parse_success:
            print("✗ 解析失败")
            return [], [], None
        
        all_messages = parser.get_all_messages()
        print(f"✓ 成功解析 {len(all_messages)} 条消息")
        
        # 获取分类消息
        input_messages = parser.get_input_messages()
        output_messages = parser.get_output_messages()
        
        print(f"✓ 用户输入: {len(input_messages)} 条")
        print(f"✓ 助手输出: {len(output_messages)} 条")
        
        # 获取会话摘要
        session_summary = parser.get_session_summary()
        if session_summary:
            print(f"✓ 会话摘要: {session_summary.total_messages} 条消息")
            print(f"  开始时间: {session_summary.start_time}")
            print(f"  结束时间: {session_summary.end_time}")
        
        return input_messages, output_messages, session_summary
        
    except Exception as e:
        print(f"✗ 解析器测试失败: {e}")
        return [], [], None


def test_voice_data_exporter(input_messages, output_messages, session_summary):
    """测试语音数据导出器"""
    print("\n=== 测试语音数据导出器 ===")
    
    try:
        # 创建导出器
        exporter = VoiceDataExporter("test_voice_output")
        
        # 导出分类文件
        file_paths = exporter.export_input_output_files(
            input_messages, output_messages, session_summary
        )
        
        print("✓ 成功导出分类文件:")
        for file_type, file_path in file_paths.items():
            if file_path:
                print(f"  {file_type}: {file_path}")
        
        # 导出合并对话文件
        combined_file = exporter.export_combined_file(
            input_messages, output_messages, session_summary
        )
        print(f"✓ 合并对话文件: {combined_file}")
        
        # 获取导出统计
        stats = exporter.get_export_statistics()
        print(f"✓ 导出统计: {stats['total_files']} 个文件")
        
        return True
        
    except Exception as e:
        print(f"✗ 导出器测试失败: {e}")
        return False


async def test_chrome_connection():
    """测试 Chrome 连接（需要 Chrome 运行在 9222 端口）"""
    print("\n=== 测试 Chrome 连接 ===")
    
    try:
        # 创建监控器
        monitor = RemoteVoiceAgentMonitor(
            chrome_host="localhost",
            chrome_port=9222,
            output_dir="test_voice_output"
        )
        
        # 尝试连接
        connected = await monitor.connect_to_remote_device()
        
        if connected:
            print("✓ 成功连接到 Chrome DevTools")
            
            # 检查 realtimeVoiceAgent（可能不存在，这是正常的）
            agent_available = await monitor.check_realtime_voice_agent()
            if agent_available:
                print("✓ realtimeVoiceAgent 可用")
                
                # 尝试获取会话历史
                history_data = await monitor.get_session_history()
                if history_data:
                    print(f"✓ 获取到 {len(history_data)} 条历史记录")
                else:
                    print("! 未获取到历史记录（可能是空的）")
            else:
                print("! realtimeVoiceAgent 不可用（这在测试环境中是正常的）")
            
            # 断开连接
            await monitor.console_executor.disconnect()
            print("✓ 已断开连接")
            return True
            
        else:
            print("✗ 无法连接到 Chrome DevTools")
            print("  请确保 Chrome 以 --remote-debugging-port=9222 参数启动")
            return False
            
    except Exception as e:
        print(f"✗ Chrome 连接测试失败: {e}")
        return False


async def test_complete_workflow_with_mock_data():
    """使用模拟数据测试完整工作流程"""
    print("\n=== 测试完整工作流程（模拟数据）===")
    
    try:
        # 创建监控器
        monitor = RemoteVoiceAgentMonitor(
            chrome_host="localhost",
            chrome_port=9222,
            output_dir="test_voice_output"
        )
        
        # 模拟历史数据
        mock_history_data = [
            {
                "timestamp": "2024-01-15T14:30:00.000Z",
                "type": "user_input",
                "role": "user",
                "content": "请帮我设置一个提醒",
                "metadata": {"source": "voice"}
            },
            {
                "timestamp": "2024-01-15T14:30:02.000Z",
                "type": "assistant_response",
                "role": "assistant",
                "content": "好的，我来帮您设置提醒。请告诉我提醒的内容和时间。",
                "metadata": {"confidence": 0.98}
            },
            {
                "timestamp": "2024-01-15T14:30:10.000Z",
                "type": "user_input",
                "role": "user",
                "content": "明天上午9点提醒我开会",
                "metadata": {"source": "voice"}
            },
            {
                "timestamp": "2024-01-15T14:30:12.000Z",
                "type": "assistant_response",
                "role": "assistant",
                "content": "好的，我已经为您设置了明天上午9点的开会提醒。",
                "metadata": {"confidence": 0.95}
            }
        ]
        
        # 解析和分类数据
        input_messages, output_messages, session_summary = monitor.parse_and_classify_data(mock_history_data)
        print(f"✓ 解析得到 {len(input_messages)} 条输入，{len(output_messages)} 条输出")
        
        # 导出数据
        file_paths = monitor.export_classified_data(input_messages, output_messages, session_summary)
        print("✓ 数据导出完成:")
        for file_type, file_path in file_paths.items():
            if file_path:
                print(f"  {file_type}: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 完整工作流程测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试远程语音代理监控器功能")
    print("=" * 50)
    
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)  # 减少日志输出
    
    # 测试 1: 语音消息解析器
    input_messages, output_messages, session_summary = test_voice_message_parser()
    
    # 测试 2: 语音数据导出器
    if input_messages or output_messages:
        test_voice_data_exporter(input_messages, output_messages, session_summary)
    
    # 测试 3: Chrome 连接（可选，需要 Chrome 运行）
    await test_chrome_connection()
    
    # 测试 4: 完整工作流程（模拟数据）
    await test_complete_workflow_with_mock_data()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n使用说明:")
    print("1. 确保远程设备已通过 SSH 端口转发: ssh root@device_ip -L 9222:localhost:9222")
    print("2. 在 Chrome 中打开 chrome://inspect")
    print("3. 点击 Bot Controller 的 inspect 进入 DevTools")
    print("4. 运行 remote_voice_agent_monitor.py 获取和解析数据")


if __name__ == "__main__":
    asyncio.run(main())