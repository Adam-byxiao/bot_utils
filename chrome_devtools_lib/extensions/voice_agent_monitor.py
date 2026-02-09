#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Agent Monitor Extension
基于Chrome DevTools库的语音代理监控扩展
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncio

from ..client import ChromeDevToolsClient
from ..domains.runtime import RuntimeDomain

logger = logging.getLogger(__name__)

class VoiceAgentMonitor:
    """语音代理监控器"""
    
    def __init__(self, debug_port: int = 9222, host: str = 'localhost'):
        """
        初始化语音代理监控器
        
        Args:
            debug_port: Chrome调试端口
            host: Chrome主机地址
        """
        self.client = ChromeDevToolsClient(debug_port, host)
        self.runtime = RuntimeDomain(self.client)
        self.is_monitoring = False
        self.last_history_length = 0
        
    async def connect(self, tab_url_pattern: str = "bot_controller") -> bool:
        """
        连接到包含语音代理的标签页
        
        Args:
            tab_url_pattern: 标签页URL模式，默认查找包含"bot_controller"的页面
            
        Returns:
            连接是否成功
        """
        success = await self.client.connect(tab_url_pattern=tab_url_pattern)
        if success:
            await self.runtime.enable()
        return success
    
    async def check_voice_agent_availability(self) -> bool:
        """
        检查realtimeVoiceAgent是否可用
        
        Returns:
            True如果可用，False如果不可用
        """
        expression = """
        (function() {
            try {
                return typeof realtimeVoiceAgent !== 'undefined' && 
                       realtimeVoiceAgent.session && 
                       realtimeVoiceAgent.session.history !== undefined;
            } catch (e) {
                return false;
            }
        })()
        """
        
        result = await self.runtime.evaluate(expression)
        
        if result["success"]:
            is_available = result["result"].get("value", False)
            logger.info(f"realtimeVoiceAgent 可用性: {is_available}")
            return is_available
        else:
            logger.error("检查 realtimeVoiceAgent 可用性失败")
            return False
    
    async def get_session_info(self) -> Dict:
        """
        获取语音代理会话基本信息
        
        Returns:
            会话信息字典
        """
        expressions = {
            "session_id": "realtimeVoiceAgent.session.id",
            "session_status": "realtimeVoiceAgent.session.status", 
            "history_length": "realtimeVoiceAgent.session.history.length",
            "is_connected": "realtimeVoiceAgent.session.isConnected",
            "model": "realtimeVoiceAgent.session.model"
        }
        
        session_info = {}
        for key, expression in expressions.items():
            try:
                result = await self.runtime.evaluate(expression)
                if result["success"]:
                    session_info[key] = result["result"].get("value")
                else:
                    session_info[key] = None
            except Exception as e:
                logger.error(f"获取会话信息 {key} 失败: {e}")
                session_info[key] = None
                
        return session_info
    
    async def get_voice_agent_history(self) -> Dict:
        """
        获取realtimeVoiceAgent.session.history的内容
        
        Returns:
            包含历史记录的字典
        """
        expression = """
        (function() {
            try {
                if (typeof realtimeVoiceAgent !== 'undefined' && 
                    realtimeVoiceAgent && 
                    realtimeVoiceAgent.session) {
                    return realtimeVoiceAgent.session.history || [];
                } else {
                    return [];
                }
            } catch (e) {
                return [];
            }
        })()
        """
        
        result = await self.runtime.evaluate(expression)
        
        if result["success"]:
            logger.info("成功获取 realtimeVoiceAgent.session.history")
            return result
        else:
            logger.error(f"获取历史记录失败: {result.get('error')}")
            return result
    
    async def get_latest_messages(self, count: int = 10) -> List[Dict]:
        """
        获取最新的消息
        
        Args:
            count: 获取的消息数量
            
        Returns:
            最新消息列表
        """
        expression = f"""
        (function() {{
            try {{
                if (typeof realtimeVoiceAgent !== 'undefined' && 
                    realtimeVoiceAgent && 
                    realtimeVoiceAgent.session &&
                    realtimeVoiceAgent.session.history) {{
                    const history = realtimeVoiceAgent.session.history;
                    return history.slice(-{count});
                }} else {{
                    return [];
                }}
            }} catch (e) {{
                return [];
            }}
        }})()
        """
        
        result = await self.runtime.evaluate(expression)
        
        if result["success"]:
            return result["result"].get("value", [])
        else:
            logger.error(f"获取最新消息失败: {result.get('error')}")
            return []
    
    async def get_messages_by_type(self, message_type: str) -> List[Dict]:
        """
        根据类型获取消息
        
        Args:
            message_type: 消息类型（如 'user', 'assistant', 'system'）
            
        Returns:
            指定类型的消息列表
        """
        expression = f"""
        (function() {{
            try {{
                if (typeof realtimeVoiceAgent !== 'undefined' && 
                    realtimeVoiceAgent && 
                    realtimeVoiceAgent.session &&
                    realtimeVoiceAgent.session.history) {{
                    const history = realtimeVoiceAgent.session.history;
                    return history.filter(msg => msg.type === '{message_type}');
                }} else {{
                    return [];
                }}
            }} catch (e) {{
                return [];
            }}
        }})()
        """
        
        result = await self.runtime.evaluate(expression)
        
        if result["success"]:
            return result["result"].get("value", [])
        else:
            logger.error(f"获取 {message_type} 类型消息失败: {result.get('error')}")
            return []
    
    async def get_conversation_statistics(self) -> Dict:
        """
        获取对话统计信息
        
        Returns:
            统计信息字典
        """
        expression = """
        (function() {
            try {
                if (typeof realtimeVoiceAgent !== 'undefined' && 
                    realtimeVoiceAgent && 
                    realtimeVoiceAgent.session &&
                    realtimeVoiceAgent.session.history) {
                    const history = realtimeVoiceAgent.session.history;
                    const stats = {
                        total_messages: history.length,
                        user_messages: 0,
                        assistant_messages: 0,
                        system_messages: 0,
                        other_messages: 0,
                        first_message_time: null,
                        last_message_time: null
                    };
                    
                    history.forEach(msg => {
                        switch(msg.type) {
                            case 'user':
                                stats.user_messages++;
                                break;
                            case 'assistant':
                                stats.assistant_messages++;
                                break;
                            case 'system':
                                stats.system_messages++;
                                break;
                            default:
                                stats.other_messages++;
                        }
                        
                        if (msg.timestamp) {
                            if (!stats.first_message_time || msg.timestamp < stats.first_message_time) {
                                stats.first_message_time = msg.timestamp;
                            }
                            if (!stats.last_message_time || msg.timestamp > stats.last_message_time) {
                                stats.last_message_time = msg.timestamp;
                            }
                        }
                    });
                    
                    return stats;
                } else {
                    return {
                        total_messages: 0,
                        user_messages: 0,
                        assistant_messages: 0,
                        system_messages: 0,
                        other_messages: 0,
                        first_message_time: null,
                        last_message_time: null
                    };
                }
            } catch (e) {
                return { error: e.message };
            }
        })()
        """
        
        result = await self.runtime.evaluate(expression)
        
        if result["success"]:
            return result["result"].get("value", {})
        else:
            logger.error(f"获取对话统计失败: {result.get('error')}")
            return {}
    
    async def monitor_new_messages(self, callback, check_interval: float = 2.0):
        """
        监控新消息
        
        Args:
            callback: 新消息回调函数，接收新消息列表作为参数
            check_interval: 检查间隔（秒）
        """
        self.is_monitoring = True
        logger.info("开始监控新消息")
        
        # 获取初始历史长度
        session_info = await self.get_session_info()
        self.last_history_length = session_info.get("history_length", 0)
        
        while self.is_monitoring:
            try:
                # 检查当前历史长度
                current_session_info = await self.get_session_info()
                current_length = current_session_info.get("history_length", 0)
                
                if current_length > self.last_history_length:
                    # 有新消息，获取新消息
                    new_message_count = current_length - self.last_history_length
                    new_messages = await self.get_latest_messages(new_message_count)
                    
                    if new_messages:
                        logger.info(f"检测到 {len(new_messages)} 条新消息")
                        await callback(new_messages)
                    
                    self.last_history_length = current_length
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"监控新消息时发生错误: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        logger.info("停止监控新消息")
    
    async def execute_custom_script(self, script: str) -> Dict:
        """
        执行自定义JavaScript脚本
        
        Args:
            script: 要执行的JavaScript代码
            
        Returns:
            执行结果
        """
        return await self.runtime.evaluate(script)
    
    async def disconnect(self):
        """断开连接"""
        self.stop_monitoring()
        await self.client.disconnect()

# 使用示例
if __name__ == "__main__":
    async def new_message_handler(messages):
        """新消息处理器示例"""
        for msg in messages:
            print(f"新消息: {msg.get('type', 'unknown')} - {msg.get('content', '')[:50]}...")
    
    async def test_voice_agent_monitor():
        monitor = VoiceAgentMonitor()
        
        # 连接到语音代理页面
        if await monitor.connect("bot_controller"):
            # 检查可用性
            is_available = await monitor.check_voice_agent_availability()
            print(f"语音代理可用: {is_available}")
            
            if is_available:
                # 获取会话信息
                session_info = await monitor.get_session_info()
                print(f"会话信息: {session_info}")
                
                # 获取统计信息
                stats = await monitor.get_conversation_statistics()
                print(f"对话统计: {stats}")
                
                # 开始监控（运行10秒后停止）
                monitor_task = asyncio.create_task(
                    monitor.monitor_new_messages(new_message_handler)
                )
                
                await asyncio.sleep(10)
                monitor.stop_monitoring()
                await monitor_task
            
            await monitor.disconnect()
        else:
            print("连接失败")
    
    asyncio.run(test_voice_agent_monitor())