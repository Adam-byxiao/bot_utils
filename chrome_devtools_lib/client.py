#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Client
通用的Chrome DevTools客户端基础类
"""

import json
import time
import asyncio
import websockets
import aiohttp
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChromeDevToolsClient:
    """Chrome DevTools 通用客户端"""
    
    def __init__(self, debug_port: int = 9222, host: str = 'localhost', suppress_origin: bool = False):
        """
        初始化Chrome DevTools客户端
        
        Args:
            debug_port: Chrome调试端口，默认9222
            host: Chrome主机地址，默认localhost
            suppress_origin: 是否抑制Origin头部，Android环境需要设置为True
        """
        self.debug_port = debug_port
        self.host = host
        self.suppress_origin = suppress_origin
        self.websocket = None
        self.is_connected = False
        self.command_id = 1
        self.event_handlers = {}
        self.enabled_domains = set()
        self.message_queue = []  # 消息队列
        self.pending_commands = {}  # 待处理的命令
        
    async def connect(self, tab_url_pattern: str = None, tab_title_pattern: str = None) -> bool:
        """
        连接到Chrome DevTools
        
        Args:
            tab_url_pattern: 标签页URL模式，用于匹配特定标签页
            tab_title_pattern: 标签页标题模式，用于匹配特定标签页
            
        Returns:
            连接是否成功
        """
        try:
            # 获取可用的标签页
            tabs = await self.get_tabs()
            if not tabs:
                logger.error("未找到可用的标签页")
                return False
            
            # 查找目标标签页
            target_tab = self._find_target_tab(tabs, tab_url_pattern, tab_title_pattern)
            if not target_tab:
                logger.error("未找到匹配的标签页")
                return False
            
            return await self.connect_target_id(target_tab['id'])
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    async def connect_target_id(self, target_id: str) -> bool:
        """
        直接连接到指定的 targetID
        
        Args:
            target_id: 目标标签页的ID
            
        Returns:
            连接是否成功
        """
        try:
            # 构建WebSocket URL
            ws_url = f"ws://{self.host}:{self.debug_port}/devtools/page/{target_id}"
            
            # 设置连接参数
            extra_headers = {}
            if self.suppress_origin:
                # Android环境下抑制Origin头部
                extra_headers = {}
            else:
                extra_headers = {"Origin": f"http://{self.host}:{self.debug_port}"}
            
            # 连接WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers=extra_headers,
                ping_interval=None,
                ping_timeout=None
            )
            
            self.is_connected = True
            logger.info(f"成功连接到目标: {target_id}")
            
            # 启动事件监听器
            asyncio.create_task(self._event_listener())
            
            return True
            
        except Exception as e:
            logger.error(f"连接目标 {target_id} 失败: {e}")
            return False
    
    def _find_target_tab(self, tabs: List[Dict], url_pattern: str = None, title_pattern: str = None) -> Optional[Dict]:
        """查找目标标签页"""
        for tab in tabs:
            if url_pattern and url_pattern in tab.get('url', ''):
                return tab
            if title_pattern and title_pattern in tab.get('title', ''):
                return tab
        return None
    
    async def _send_command(self, method: str, params: Dict = None) -> Dict:
        """
        发送CDP命令并等待响应
        
        Args:
            method: CDP方法名
            params: 命令参数
            
        Returns:
            命令响应
        """
        if not self.websocket:
            raise Exception("WebSocket未连接")
            
        command = {
            "id": self.command_id,
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(command))
        current_id = self.command_id
        self.command_id += 1
        
        # 等待响应
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            # 如果是我们发送的命令的响应
            if data.get('id') == current_id:
                return data
            # 忽略其他事件（事件监听器会处理）
    
    async def _event_listener(self):
        """事件监听器，处理Chrome DevTools事件"""
        try:
            while self.is_connected and self.websocket:
                response = await self.websocket.recv()
                data = json.loads(response)
                
                # 将所有消息添加到队列中
                self.message_queue.append(data)
                
                # 处理事件（没有id字段的消息）
                if 'method' in data and 'id' not in data:
                    method = data['method']
                    params = data.get('params', {})
                    
                    # 调用注册的事件处理器
                    if method in self.event_handlers:
                        for handler in self.event_handlers[method]:
                            try:
                                await handler(params)
                            except Exception as e:
                                logger.error(f"事件处理器执行失败 {method}: {e}")
                                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"事件监听器异常: {e}")
    
    async def wait_event(self, event_name: str, timeout: float = 1.0) -> tuple[Optional[Dict], List[Dict]]:
        """
        等待特定事件
        
        Args:
            event_name: 要等待的事件名称
            timeout: 超时时间（秒）
            
        Returns:
            (匹配的事件, 所有接收到的事件)
        """
        start_time = time.time()
        all_events = []
        
        while time.time() - start_time < timeout:
            # 检查消息队列中是否有匹配的事件
            for i, message in enumerate(self.message_queue):
                if message.get('method') == event_name:
                    # 找到匹配的事件
                    matching_event = self.message_queue.pop(i)
                    all_events = self.message_queue.copy()
                    self.message_queue.clear()
                    return matching_event, all_events
            
            # 短暂等待新消息
            await asyncio.sleep(0.01)
        
        # 超时，返回所有收到的消息
        all_events = self.message_queue.copy()
        self.message_queue.clear()
        return None, all_events
    
    async def wait_message(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        等待单个消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            接收到的消息，超时返回None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.message_queue:
                return self.message_queue.pop(0)
            await asyncio.sleep(0.01)
        
        return None
    
    def pop_messages(self) -> List[Dict]:
        """
        获取所有已接收的消息（非阻塞）
        
        Returns:
            所有未读消息的列表
        """
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """
        添加事件处理器
        
        Args:
            event_name: 事件名称（如 'Runtime.consoleAPICalled'）
            handler: 事件处理函数
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """移除事件处理器"""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    async def enable_domain(self, domain: str) -> bool:
        """
        启用指定的DevTools域
        
        Args:
            domain: 域名（如 'Runtime', 'Network', 'Performance'）
            
        Returns:
            是否启用成功
        """
        try:
            response = await self._send_command(f"{domain}.enable")
            
            if 'error' in response:
                logger.error(f"启用域 {domain} 失败: {response['error']}")
                return False
                
            self.enabled_domains.add(domain)
            logger.info(f"已启用域: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"启用域 {domain} 异常: {e}")
            return False
    
    async def disable_domain(self, domain: str) -> bool:
        """禁用指定的DevTools域"""
        try:
            response = await self._send_command(f"{domain}.disable")
            
            if 'error' in response:
                logger.error(f"禁用域 {domain} 失败: {response['error']}")
                return False
                
            self.enabled_domains.discard(domain)
            logger.info(f"已禁用域: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"禁用域 {domain} 异常: {e}")
            return False
    
    async def execute_command(self, method: str, params: Dict = None) -> Dict:
        """
        执行通用CDP命令
        
        Args:
            method: CDP方法名
            params: 命令参数
            
        Returns:
            执行结果
        """
        try:
            response = await self._send_command(method, params)
            
            if 'error' in response:
                logger.error(f"CDP命令执行失败 {method}: {response['error']}")
                return {"success": False, "error": response['error']}
            
            return {
                "success": True,
                "result": response.get('result', {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行CDP命令失败 {method}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_tabs(self) -> List[Dict]:
        """获取所有可用的标签页"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self.host}:{self.debug_port}/json') as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取标签页列表失败: {e}")
            return []
    
    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
            logger.info("已断开Chrome DevTools连接")
    
    def __del__(self):
        """析构函数，确保连接被关闭"""
        if self.is_connected and self.websocket:
            asyncio.create_task(self.disconnect())