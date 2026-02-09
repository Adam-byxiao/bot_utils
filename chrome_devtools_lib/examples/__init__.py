#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library - 示例模块

本模块包含了Chrome DevTools库的各种使用示例：
- basic_usage.py: 基础功能使用示例
- voice_agent_example.py: 语音代理监控示例
- advanced_usage.py: 高级功能使用示例
"""

__version__ = "1.0.0"
__author__ = "Chrome DevTools Library Team"

# 示例模块说明
EXAMPLES = {
    "basic_usage": {
        "description": "基础功能使用示例",
        "features": [
            "Runtime域基础操作",
            "Network域监控",
            "多域协同使用",
            "错误处理"
        ]
    },
    "voice_agent_example": {
        "description": "语音代理监控示例", 
        "features": [
            "语音代理可用性检查",
            "会话信息获取",
            "消息历史记录",
            "实时消息监控",
            "消息过滤和统计",
            "自定义脚本执行"
        ]
    },
    "advanced_usage": {
        "description": "高级功能使用示例",
        "features": [
            "性能监控",
            "存储管理", 
            "事件处理",
            "批量操作"
        ]
    }
}

def list_examples():
    """列出所有可用的示例"""
    print("Chrome DevTools Library - 可用示例:")
    print("=" * 50)
    
    for name, info in EXAMPLES.items():
        print(f"\n📁 {name}")
        print(f"   描述: {info['description']}")
        print("   功能:")
        for feature in info['features']:
            print(f"   • {feature}")
    
    print("\n" + "=" * 50)
    print("使用方法: python -m chrome_devtools_lib.examples.<example_name>")

if __name__ == "__main__":
    list_examples()