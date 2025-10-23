#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Console 执行器
用于在 Chrome DevTools Console 中执行 JavaScript 代码并获取结果
"""

import json
import time
import asyncio
import websockets
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChromeConsoleExecutor:
    """Chrome DevTools Console 执行器"""
    
    def __init__(self, debug_port: int = 9222, host: str = 'localhost'):
        self.debug_port = debug_port
        self.host = host
        self.websocket = None
        self.is_connected = False
        self.command_id = 1
        
    async def connect(self, tab_url_pattern: str = None) -> bool:
        """
        连接到 Chrome DevTools
        
        Args:
            tab_url_pattern: 标签页 URL 模式，用于匹配特定标签页
        """
        try:
            # 获取可用的标签页
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self.host}:{self.debug_port}/json') as resp:
                    tabs = await resp.json()
                    
            if not tabs:
                logger.error("没有找到可用的Chrome标签页")
                return False
            
            # 查找匹配的标签页
            target_tab = None
            if tab_url_pattern:
                for tab in tabs:
                    if tab_url_pattern in tab.get('url', ''):
                        target_tab = tab
                        break
                        
            if not target_tab:
                target_tab = tabs[0]  # 使用第一个标签页
                
            # 连接到目标标签页的WebSocket
            ws_url = target_tab['webSocketDebuggerUrl']
            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True
            
            # 启用 Runtime 域
            await self._send_command("Runtime.enable")
            
            logger.info(f"已连接到Chrome DevTools: {target_tab.get('title', 'Unknown')}")
            logger.info(f"标签页URL: {target_tab.get('url', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"连接Chrome DevTools失败: {e}")
            return False
    
    async def _send_command(self, method: str, params: Dict = None) -> Dict:
        """发送CDP命令并等待响应"""
        if not self.websocket:
            raise Exception("WebSocket未连接")
            
        command = {
            "id": self.command_id,
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(command))
        self.command_id += 1
        
        # 等待响应
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            # 如果是我们发送的命令的响应
            if data.get('id') == command['id']:
                return data
            # 忽略其他事件
    
    async def execute_javascript(self, expression: str, return_by_value: bool = True) -> Dict:
        """
        在 Console 中执行 JavaScript 代码
        
        Args:
            expression: 要执行的 JavaScript 表达式
            return_by_value: 是否返回值而不是对象引用
            
        Returns:
            执行结果字典
        """
        try:
            params = {
                "expression": expression,
                "returnByValue": return_by_value,
                "generatePreview": True,
                "userGesture": True,
                "awaitPromise": True
            }
            
            response = await self._send_command("Runtime.evaluate", params)
            
            if 'error' in response:
                logger.error(f"CDP命令执行失败: {response['error']}")
                return {"success": False, "error": response['error']}
            
            result = response.get('result', {})
            
            if result.get('exceptionDetails'):
                logger.error(f"JavaScript执行异常: {result['exceptionDetails']}")
                return {
                    "success": False, 
                    "error": "JavaScript执行异常",
                    "exception": result['exceptionDetails']
                }
            
            return {
                "success": True,
                "result": result.get('result', {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行JavaScript失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_realtime_voice_agent_history(self) -> Dict:
        """
        获取 realtimeVoiceAgent.session.history 的内容
        
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
        result = await self.execute_javascript(expression)
        
        if result["success"]:
            logger.info("成功获取 realtimeVoiceAgent.session.history")
            return result
        else:
            logger.error(f"获取历史记录失败: {result.get('error')}")
            return result
    
    async def check_realtime_voice_agent_availability(self) -> bool:
        """
        检查 realtimeVoiceAgent 是否可用
        
        Returns:
            True 如果可用，False 如果不可用
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
        result = await self.execute_javascript(expression)
        
        if result["success"]:
            is_available = result["result"].get("value", False)
            logger.info(f"realtimeVoiceAgent 可用性: {is_available}")
            return is_available
        else:
            logger.error("检查 realtimeVoiceAgent 可用性失败")
            return False
    
    async def get_session_info(self) -> Dict:
        """
        获取会话基本信息
        
        Returns:
            会话信息字典
        """
        expressions = {
            "session_id": "realtimeVoiceAgent.session.id",
            "session_status": "realtimeVoiceAgent.session.status", 
            "history_length": "realtimeVoiceAgent.session.history.length"
        }
        
        session_info = {}
        for key, expression in expressions.items():
            result = await self.execute_javascript(expression)
            if result["success"]:
                session_info[key] = result["result"].get("value")
            else:
                session_info[key] = None
                
        return session_info
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("已断开Chrome DevTools连接")

# 测试代码
if __name__ == "__main__":
    async def test_console_executor():
        executor = ChromeConsoleExecutor()
        
        # 连接到包含 bot_controller 的标签页
        if await executor.connect("bot_controller"):
            # 检查 realtimeVoiceAgent 可用性
            is_available = await executor.check_realtime_voice_agent_availability()
            print(f"realtimeVoiceAgent 可用: {is_available}")
            
            if is_available:
                # 获取会话信息
                session_info = await executor.get_session_info()
                print(f"会话信息: {session_info}")
                
                # 获取历史记录
                history_result = await executor.get_realtime_voice_agent_history()
                if history_result["success"]:
                    print("历史记录获取成功")
                    print(json.dumps(history_result, indent=2, ensure_ascii=False))
                else:
                    print(f"历史记录获取失败: {history_result}")
            
            await executor.disconnect()
        else:
            print("连接失败")
    
    asyncio.run(test_console_executor())