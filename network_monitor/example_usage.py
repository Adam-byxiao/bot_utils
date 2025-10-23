#!/usr/bin/env python3
"""
远程语音代理监控器使用示例

这个脚本演示如何使用远程语音代理监控器来获取和解析语音代理数据。

使用前请确保：
1. 已建立 SSH 端口转发: ssh root@device_ip -L 9222:localhost:9222
2. Chrome 已启动调试模式: chrome --remote-debugging-port=9222
3. 已在 chrome://inspect 中打开 Bot Controller 的 DevTools
"""

import asyncio
import os
import sys
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from remote_voice_agent_monitor import RemoteVoiceAgentMonitor


async def main():
    """主函数：演示完整的监控流程"""
    
    print("=" * 60)
    print("远程语音代理监控器 - 使用示例")
    print("=" * 60)
    
    # 配置参数
    chrome_host = "localhost"
    chrome_port = 9222
    output_dir = "voice_output"
    
    print(f"配置信息:")
    print(f"  Chrome 主机: {chrome_host}")
    print(f"  Chrome 端口: {chrome_port}")
    print(f"  输出目录: {output_dir}")
    print()
    
    # 创建监控器实例
    monitor = RemoteVoiceAgentMonitor(
        chrome_host=chrome_host,
        chrome_port=chrome_port,
        output_dir=output_dir
    )
    
    try:
        print("开始监控流程...")
        print("-" * 40)
        
        # 步骤1: 连接到远程设备
        print("1. 连接到远程设备...")
        connected = await monitor.connect_to_remote_device()
        if not connected:
            print("❌ 连接失败！")
            print("\n请检查：")
            print("  - SSH 端口转发是否正常")
            print("  - Chrome 是否以调试模式启动")
            print("  - 端口 9222 是否可访问")
            return False
        print("✅ 连接成功！")
        
        # 步骤2: 检查语音代理可用性
        print("\n2. 检查语音代理可用性...")
        available = await monitor.check_realtime_voice_agent()
        if not available:
            print("❌ 语音代理不可用！")
            print("\n请检查：")
            print("  - 是否在正确的页面（Bot Controller）")
            print("  - realtimeVoiceAgent 是否已加载")
            return False
        print("✅ 语音代理可用！")
        
        # 步骤3: 获取会话历史
        print("\n3. 获取会话历史数据...")
        history_data = await monitor.get_session_history()
        if history_data is None:
            print("❌ 获取历史数据失败！")
            return False
        history_count = len(history_data) if isinstance(history_data, list) else 0
        print(f"✅ 成功获取 {history_count} 条历史记录！")
        
        # 步骤4: 解析和分类数据
        print("\n4. 解析和分类数据...")
        input_messages, output_messages, session_summary = monitor.parse_and_classify_data(history_data)
        total_messages = len(input_messages) + len(output_messages)
        if total_messages == 0:
            print("✅ 解析完成 - 无有效消息数据")
        else:
            print(f"✅ 成功解析 {total_messages} 条消息！")
        
        # 步骤5: 导出数据
        print("\n5. 导出数据到文件...")
        export_result = monitor.export_classified_data(input_messages, output_messages, session_summary)
        if not export_result:
            print("❌ 数据导出失败！")
            return False
        print("✅ 数据导出成功！")
        
        # 显示导出结果
        print("\n" + "=" * 40)
        print("导出结果:")
        print("=" * 40)
        for key, value in export_result.items():
            if key.endswith('_file'):
                print(f"  {key}: {value}")
        
        # 显示统计信息
        stats = monitor.exporter.get_export_statistics()
        print(f"\n导出统计: {stats['total_files']} 个文件")
        
        print("\n🎉 监控完成！所有数据已成功导出。")
        return True
        
    except Exception as e:
        print(f"❌ 监控过程中发生错误: {e}")
        return False
        
    finally:
        # 确保断开连接
        try:
            await monitor.console_executor.disconnect()
            print("\n🔌 已断开连接")
        except:
            pass


async def quick_monitoring():
    """快速监控：使用一键式方法"""
    
    print("=" * 60)
    print("快速监控模式")
    print("=" * 60)
    
    monitor = RemoteVoiceAgentMonitor(
        chrome_host="localhost",
        chrome_port=9222,
        output_dir="voice_output"
    )
    
    print("执行一键式监控...")
    result = await monitor.run_complete_monitoring_cycle()
    success = result.get("success", False)
    
    if success:
        print("🎉 监控成功完成！")
        
        # 显示导出的文件
        stats = monitor.exporter.get_export_statistics()
        print(f"\n导出了 {stats['total_files']} 个文件:")
        for file_info in stats['files']:
            print(f"  - {file_info['name']} ({file_info['size']} bytes)")
    else:
        print("❌ 监控失败")


def print_usage():
    """打印使用说明"""
    print("使用方法:")
    print("  python example_usage.py [mode]")
    print()
    print("模式:")
    print("  detailed  - 详细步骤模式（默认）")
    print("  quick     - 快速监控模式")
    print("  help      - 显示此帮助信息")
    print()
    print("使用前准备:")
    print("  1. 建立 SSH 端口转发:")
    print("     ssh root@device_ip -L 9222:localhost:9222")
    print()
    print("  2. 启动 Chrome 调试模式:")
    print("     chrome --remote-debugging-port=9222")
    print()
    print("  3. 在 chrome://inspect 中打开 Bot Controller 的 DevTools")


if __name__ == "__main__":
    # 解析命令行参数
    mode = "detailed"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode == "help":
        print_usage()
        sys.exit(0)
    elif mode == "quick":
        asyncio.run(quick_monitoring())
    elif mode == "detailed":
        asyncio.run(main())
    else:
        print(f"未知模式: {mode}")
        print_usage()
        sys.exit(1)