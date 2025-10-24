#!/usr/bin/env python3
"""
测试脚本：验证美化后的显示效果
"""

import asyncio
from remote_voice_agent_monitor import RemoteVoiceAgentMonitor

async def test_display_format():
    """测试显示格式"""
    monitor = RemoteVoiceAgentMonitor()
    
    try:
        # 连接到设备
        print("正在连接到设备...")
        success = await monitor.connect_to_remote_device()
        if not success:
            print("连接失败！请确保SSH端口转发和Chrome调试模式已正确设置")
            return
        print("连接成功！")
        
        # 获取历史数据
        print("\n获取历史数据...")
        history_data = await monitor.get_session_history()
        
        if history_data:
            print(f"获取到 {len(history_data)} 条历史记录")
            
            # 解析数据
            input_messages, output_messages, session_summary = monitor.parse_and_classify_data(history_data)
            
            print(f"\n=== 美化后的对话显示效果预览 ===")
            print(f"输入消息: {len(input_messages)} 条")
            print(f"输出消息: {len(output_messages)} 条")
            
            # 显示前几条消息的美化效果
            all_messages = []
            for msg in input_messages:
                all_messages.append(('input', msg))
            for msg in output_messages:
                all_messages.append(('output', msg))
            
            # 按时间排序
            all_messages.sort(key=lambda x: x[1].timestamp)
            
            # 显示前3条消息
            for i, (msg_type, msg) in enumerate(all_messages[:3]):
                formatted_time = "12:34:56"  # 示例时间
                
                if msg_type == 'input':
                    # 用户消息
                    display_msg = f"""
┌─ 👤 用户 ({formatted_time}) ─────────────────────────────────────
│ {msg.content}
└─────────────────────────────────────────────────────────────────
"""
                else:
                    # 助手消息 - 处理长文本
                    content_lines = []
                    words = msg.content.split(' ')
                    current_line = ""
                    max_line_length = 60
                    
                    for word in words:
                        if len(current_line + word) <= max_line_length:
                            current_line += word + " "
                        else:
                            if current_line:
                                content_lines.append(current_line.strip())
                            current_line = word + " "
                    
                    if current_line:
                        content_lines.append(current_line.strip())
                    
                    # 格式化多行内容
                    formatted_content = ""
                    for line in content_lines:
                        formatted_content += f"│ {line}\n"
                    
                    display_msg = f"""
┌─ 🤖 助手 ({formatted_time}) ─────────────────────────────────────
{formatted_content}└─────────────────────────────────────────────────────────────────
"""
                
                print(display_msg)
                
        else:
            print("没有获取到历史数据")
            print("请在Bot Controller页面进行一些语音对话，然后重新运行此脚本")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_display_format())