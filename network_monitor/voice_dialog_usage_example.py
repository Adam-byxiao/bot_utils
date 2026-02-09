#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音对话解析器使用示例
展示如何在实际项目中使用 VoiceDialogParser
"""

import json
import asyncio
from datetime import datetime
from voice_dialog_parser import VoiceDialogParser

# 示例数据 - 模拟从 realtimeManager.getHistory() 获取的数据
example_history_data = [
    {
        "itemId": "item_CzH3hZ8xJjoMlREkpwGzl",
        "previousItemId": None,
        "type": "message",
        "role": "user",
        "status": "completed",
        "content": [
            {
                "type": "input_audio",
                "audio": None,
                "transcript": "春节是几号?春节是几号?"
            }
        ]
    },
    {
        "itemId": "item_CzH3lCzEYvKMCTZp8T96j",
        "type": "function_call",
        "status": "completed",
        "arguments": "{  \n  \"query\": \"2026 春节是几月几号\"\n}",
        "name": "search_intelligent",
        "output": "{\"content\": `https://www.baibaidu.com/festivaldate/2026-2-17-101.html?utm_source=openai` )根据国务院办公厅发布的放假安排，春节假期从2月15日（农历腊月二十八，星期日）开始，至2月23日（农历正月初七，星期一）结束，共9天。 ( `https://www.bjfsh.gov.cn/zhxw/fsdt/202511/t20251105_40108387.shtml?utm_source=openai` )其中，2月14日（星期六）和2月28日（星期六）需要上班。 \"}]}"
    },
    {
        "itemId": "item_CzH3pylPPSgoScCSyUO7V",
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [
            {
                "type": "output_audio",
                "transcript": "In 2026, the Chinese New Year, or Spring Festival, falls on February 17th. That's the date for the Lunar New Year celebration.",
                "audio": None
            }
        ]
    }
]

def basic_usage():
    """基础使用方法"""
    print("=" * 60)
    print("基础使用方法")
    print("=" * 60)
    
    # 1. 创建解析器实例
    parser = VoiceDialogParser()
    
    # 2. 解析数据
    if parser.parse_history_data(example_history_data):
        print("✅ 解析成功！")
        
        # 3. 获取格式化输出
        print("\n📝 格式化输出:")
        print(parser.get_formatted_output())
        
        # 4. 获取对话对象
        print("\n💬 对话详情:")
        dialogs = parser.get_dialogs()
        for i, dialog in enumerate(dialogs, 1):
            print(f"对话 {i}:")
            print(f"  用户: {dialog.user_input}")
            print(f"  助手: {dialog.assistant_output}")
            print()
        
        # 5. 导出为JSON
        json_output = parser.export_to_json("example_output.json")
        print("✅ JSON数据已保存到 example_output.json")
        
    else:
        print("❌ 解析失败！")

def advanced_usage():
    """高级使用方法"""
    print("\n" + "=" * 60)
    print("高级使用方法")
    print("=" * 60)
    
    # 模拟从文件读取数据
    try:
        # 保存示例数据到文件
        with open('example_data.json', 'w', encoding='utf-8') as f:
            json.dump(example_history_data, f, indent=2, ensure_ascii=False)
        
        # 从文件读取数据
        with open('example_data.json', 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # 解析数据
        parser = VoiceDialogParser()
        if parser.parse_history_data(loaded_data):
            print("✅ 从文件加载并解析成功！")
            
            # 批量处理多个对话
            dialogs = parser.get_dialogs()
            
            # 生成分析报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"voice_analysis_report_{timestamp}.txt"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("语音对话分析报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {datetime.now().isoformat()}\n")
                f.write(f"对话数量: {len(dialogs)}\n\n")
                
                for i, dialog in enumerate(dialogs, 1):
                    f.write(f"对话 {i}:\n")
                    f.write(f"用户输入: {dialog.user_input}\n")
                    f.write(f"助手回复: {dialog.assistant_output}\n")
                    f.write("-" * 40 + "\n\n")
            
            print(f"✅ 分析报告已保存到: {report_filename}")
            
        else:
            print("❌ 解析失败！")
            
    except Exception as e:
        print(f"❌ 文件操作出错: {e}")

async def integration_example():
    """集成到监控系统的示例"""
    print("\n" + "=" * 60)
    print("集成到监控系统的示例")
    print("=" * 60)
    
    # 模拟监控过程中捕获数据
    print("🔍 模拟监控过程...")
    await asyncio.sleep(1)
    
    # 创建解析器
    parser = VoiceDialogParser()
    
    # 解析数据
    if parser.parse_history_data(example_history_data):
        print("✅ 实时解析成功！")
        
        # 实时显示对话内容
        dialogs = parser.get_dialogs()
        if dialogs:
            print("\n🎯 最新对话内容:")
            latest_dialog = dialogs[-1]  # 获取最新的对话
            print(f"用户: {latest_dialog.user_input}")
            print(f"助手: {latest_dialog.assistant_output}")
        
        # 保存到带时间戳的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parser.export_to_json(f"realtime_dialog_{timestamp}.json")
        
        print(f"✅ 实时对话数据已保存")
        
    else:
        print("❌ 实时解析失败！")

def main():
    """主函数"""
    print("语音对话解析器使用示例")
    print("=" * 60)
    
    # 运行各种使用示例
    basic_usage()
    advanced_usage()
    
    # 运行异步示例
    asyncio.run(integration_example())
    
    print("\n" + "=" * 60)
    print("使用示例完成！")
    print("=" * 60)
    print("\n📋 总结:")
    print("1. 创建 VoiceDialogParser 实例")
    print("2. 调用 parse_history_data() 方法解析数据")
    print("3. 使用 get_formatted_output() 获取格式化文本")
    print("4. 使用 get_dialogs() 获取对话对象列表")
    print("5. 使用 export_to_json() 导出为JSON文件")
    print("6. 集成到监控系统中进行实时解析")

if __name__ == "__main__":
    main()