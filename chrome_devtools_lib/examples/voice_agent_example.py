#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library - 语音代理监控示例
演示如何使用VoiceAgentMonitor扩展进行语音代理监控
"""

import asyncio
import logging
from chrome_devtools_lib.extensions import VoiceAgentMonitor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def basic_voice_agent_example():
    """基础语音代理监控示例"""
    print("=== 基础语音代理监控示例 ===")
    
    monitor = VoiceAgentMonitor()
    
    try:
        # 连接并检查语音代理
        if await monitor.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 检查语音代理是否可用
            is_available = await monitor.is_voice_agent_available()
            if is_available:
                print("✓ 语音代理可用")
                
                # 获取会话信息
                session_info = await monitor.get_session_info()
                if session_info:
                    print("📋 会话信息:")
                    print(f"  会话ID: {session_info.get('sessionId', 'Unknown')}")
                    print(f"  状态: {session_info.get('status', 'Unknown')}")
                    print(f"  创建时间: {session_info.get('createdAt', 'Unknown')}")
                
                # 获取历史记录
                history = await monitor.get_history()
                if history:
                    print(f"📚 历史记录: 共 {len(history)} 条消息")
                    
                    # 显示最近5条消息
                    recent_messages = history[-5:] if len(history) > 5 else history
                    for i, msg in enumerate(recent_messages, 1):
                        msg_type = msg.get('type', 'unknown')
                        content = msg.get('content', '')[:50] + '...' if len(msg.get('content', '')) > 50 else msg.get('content', '')
                        timestamp = msg.get('timestamp', 'Unknown')
                        print(f"  {i}. [{msg_type}] {content} ({timestamp})")
                
                # 获取对话统计
                stats = await monitor.get_conversation_stats()
                if stats:
                    print("📊 对话统计:")
                    print(f"  总消息数: {stats.get('totalMessages', 0)}")
                    print(f"  用户消息: {stats.get('userMessages', 0)}")
                    print(f"  助手消息: {stats.get('assistantMessages', 0)}")
                    print(f"  系统消息: {stats.get('systemMessages', 0)}")
                
            else:
                print("✗ 语音代理不可用")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
    
    finally:
        await monitor.disconnect()
        print("✓ 已断开连接")

async def message_monitoring_example():
    """消息监控示例"""
    print("\n=== 消息监控示例 ===")
    
    monitor = VoiceAgentMonitor()
    
    try:
        if await monitor.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            if await monitor.is_voice_agent_available():
                print("✓ 语音代理可用")
                
                # 获取初始消息数量
                initial_history = await monitor.get_history()
                initial_count = len(initial_history) if initial_history else 0
                print(f"📊 初始消息数量: {initial_count}")
                
                # 监控新消息
                print("🔍 开始监控新消息（30秒）...")
                print("💡 提示: 在Chrome中与语音代理进行对话以查看实时监控效果")
                
                for i in range(30):
                    await asyncio.sleep(1)
                    
                    # 检查是否有新消息
                    current_history = await monitor.get_history()
                    current_count = len(current_history) if current_history else 0
                    
                    if current_count > initial_count:
                        new_messages = current_history[initial_count:]
                        for msg in new_messages:
                            msg_type = msg.get('type', 'unknown')
                            content = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
                            print(f"🆕 新消息 [{msg_type}]: {content}")
                        
                        initial_count = current_count
                    
                    # 每5秒显示一次进度
                    if (i + 1) % 5 == 0:
                        print(f"⏱️  监控进度: {i + 1}/30 秒")
                
                print("✓ 监控完成")
            
            else:
                print("✗ 语音代理不可用")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"消息监控示例失败: {e}")
    
    finally:
        await monitor.disconnect()
        print("✓ 已断开连接")

async def message_filtering_example():
    """消息过滤示例"""
    print("\n=== 消息过滤示例 ===")
    
    monitor = VoiceAgentMonitor()
    
    try:
        if await monitor.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            if await monitor.is_voice_agent_available():
                print("✓ 语音代理可用")
                
                # 按类型获取消息
                message_types = ['user', 'assistant', 'system']
                
                for msg_type in message_types:
                    messages = await monitor.get_messages_by_type(msg_type)
                    if messages:
                        print(f"📝 {msg_type.upper()} 消息 ({len(messages)} 条):")
                        
                        # 显示最近3条消息
                        recent = messages[-3:] if len(messages) > 3 else messages
                        for i, msg in enumerate(recent, 1):
                            content = msg.get('content', '')[:80] + '...' if len(msg.get('content', '')) > 80 else msg.get('content', '')
                            timestamp = msg.get('timestamp', 'Unknown')
                            print(f"  {i}. {content} ({timestamp})")
                    else:
                        print(f"📝 {msg_type.upper()} 消息: 无")
                    print()
                
                # 获取最新消息
                latest = await monitor.get_latest_message()
                if latest:
                    print("🔥 最新消息:")
                    print(f"  类型: {latest.get('type', 'unknown')}")
                    print(f"  内容: {latest.get('content', '')[:100]}...")
                    print(f"  时间: {latest.get('timestamp', 'Unknown')}")
                else:
                    print("🔥 最新消息: 无")
            
            else:
                print("✗ 语音代理不可用")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"消息过滤示例失败: {e}")
    
    finally:
        await monitor.disconnect()
        print("✓ 已断开连接")

async def custom_script_example():
    """自定义脚本示例"""
    print("\n=== 自定义脚本示例 ===")
    
    monitor = VoiceAgentMonitor()
    
    try:
        if await monitor.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            if await monitor.is_voice_agent_available():
                print("✓ 语音代理可用")
                
                # 自定义脚本1: 获取语音代理配置
                config_script = """
                (function() {
                    if (window.realtimeVoiceAgent && window.realtimeVoiceAgent.config) {
                        return {
                            model: window.realtimeVoiceAgent.config.model || 'unknown',
                            language: window.realtimeVoiceAgent.config.language || 'unknown',
                            voice: window.realtimeVoiceAgent.config.voice || 'unknown',
                            autoStart: window.realtimeVoiceAgent.config.autoStart || false
                        };
                    }
                    return null;
                })()
                """
                
                result = await monitor.execute_custom_script(config_script)
                if result and result.get('success'):
                    config = result.get('result', {}).get('value')
                    if config:
                        print("⚙️  语音代理配置:")
                        for key, value in config.items():
                            print(f"  {key}: {value}")
                    else:
                        print("⚙️  无法获取语音代理配置")
                
                # 自定义脚本2: 获取当前状态
                status_script = """
                (function() {
                    if (window.realtimeVoiceAgent) {
                        return {
                            isConnected: window.realtimeVoiceAgent.isConnected || false,
                            isRecording: window.realtimeVoiceAgent.isRecording || false,
                            isSpeaking: window.realtimeVoiceAgent.isSpeaking || false,
                            currentMode: window.realtimeVoiceAgent.currentMode || 'unknown'
                        };
                    }
                    return null;
                })()
                """
                
                result = await monitor.execute_custom_script(status_script)
                if result and result.get('success'):
                    status = result.get('result', {}).get('value')
                    if status:
                        print("📡 语音代理状态:")
                        for key, value in status.items():
                            print(f"  {key}: {value}")
                    else:
                        print("📡 无法获取语音代理状态")
                
                # 自定义脚本3: 获取性能指标
                perf_script = """
                (function() {
                    if (window.realtimeVoiceAgent && window.realtimeVoiceAgent.performance) {
                        return {
                            totalRequests: window.realtimeVoiceAgent.performance.totalRequests || 0,
                            averageResponseTime: window.realtimeVoiceAgent.performance.averageResponseTime || 0,
                            errorCount: window.realtimeVoiceAgent.performance.errorCount || 0,
                            lastRequestTime: window.realtimeVoiceAgent.performance.lastRequestTime || null
                        };
                    }
                    return null;
                })()
                """
                
                result = await monitor.execute_custom_script(perf_script)
                if result and result.get('success'):
                    perf = result.get('result', {}).get('value')
                    if perf:
                        print("📈 性能指标:")
                        for key, value in perf.items():
                            print(f"  {key}: {value}")
                    else:
                        print("📈 无法获取性能指标")
            
            else:
                print("✗ 语音代理不可用")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"自定义脚本示例失败: {e}")
    
    finally:
        await monitor.disconnect()
        print("✓ 已断开连接")

async def main():
    """主函数，运行所有示例"""
    print("Chrome DevTools Library - 语音代理监控示例")
    print("=" * 60)
    print("💡 确保Chrome浏览器已启动并开启了DevTools调试端口")
    print("💡 确保页面中存在realtimeVoiceAgent对象")
    print("=" * 60)
    
    # 运行各个示例
    await basic_voice_agent_example()
    await message_monitoring_example()
    await message_filtering_example()
    await custom_script_example()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())