#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Client - 详细注释版本
通用的Chrome DevTools客户端基础类

本文件是 client.py 的详细注释版本，用于学习和理解实现细节。
"""

import json
import time
import asyncio
import websockets
import aiohttp
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

# 创建模块级别的日志记录器
logger = logging.getLogger(__name__)

class ChromeDevToolsClient:
    """
    Chrome DevTools 通用客户端
    
    这个类实现了与 Chrome DevTools Protocol (CDP) 的完整交互能力。
    主要功能包括：
    1. WebSocket 连接管理
    2. CDP 命令执行
    3. 事件监听和处理
    4. DevTools 域管理
    5. 多标签页支持
    
    设计原则：
    - 异步优先：所有网络操作都是异步的
    - 事件驱动：支持实时事件监听
    - 模块化：通过域管理实现功能分离
    - 容错性：完善的异常处理
    """
    
    def __init__(self, debug_port: int = 9222, host: str = 'localhost'):
        """
        初始化Chrome DevTools客户端
        
        Args:
            debug_port: Chrome调试端口，默认9222
                       启动Chrome时需要添加 --remote-debugging-port=9222 参数
            host: Chrome主机地址，默认localhost
                  可以是远程主机IP地址
        
        实例变量说明：
        - debug_port: 调试端口号
        - host: 主机地址
        - websocket: WebSocket连接对象，用于与Chrome通信
        - is_connected: 连接状态标志
        - command_id: 命令ID计数器，确保每个命令有唯一ID
        - event_handlers: 事件处理器字典，存储事件名到处理器列表的映射
        - enabled_domains: 已启用的域集合，跟踪当前启用的DevTools域
        """
        self.debug_port = debug_port
        self.host = host
        self.websocket = None  # WebSocket连接对象
        self.is_connected = False  # 连接状态标志
        self.command_id = 1  # 命令ID计数器，从1开始
        self.event_handlers = {}  # 事件处理器字典 {event_name: [handler1, handler2, ...]}
        self.enabled_domains = set()  # 已启用的域集合 {'Runtime', 'Network', ...}
        
    async def connect(self, tab_url_pattern: str = None, tab_title_pattern: str = None) -> bool:
        """
        连接到Chrome DevTools
        
        连接流程：
        1. 通过HTTP API获取所有可用标签页
        2. 根据URL或标题模式查找目标标签页
        3. 建立WebSocket连接
        4. 启动事件监听任务
        
        Args:
            tab_url_pattern: 标签页URL模式，用于匹配特定标签页
                           例如: "localhost:3000" 匹配包含此字符串的URL
            tab_title_pattern: 标签页标题模式，用于匹配特定标签页
                             例如: "React App" 匹配包含此字符串的标题
            
        Returns:
            bool: 连接是否成功
            
        实现细节：
        - 使用Chrome的HTTP API (/json端点) 获取标签页列表
        - 优先匹配URL模式，其次匹配标题模式
        - 如果没有匹配的标签页，使用第一个可用标签页
        - WebSocket URL从标签页信息中的webSocketDebuggerUrl字段获取
        """
        try:
            # 步骤1: 获取可用的标签页
            # Chrome DevTools 提供HTTP API来获取所有打开的标签页信息
            async with aiohttp.ClientSession() as session:
                # 请求Chrome的标签页列表API
                async with session.get(f'http://{self.host}:{self.debug_port}/json') as resp:
                    tabs = await resp.json()
                    
            # 检查是否有可用的标签页
            if not tabs:
                logger.error("没有找到可用的Chrome标签页")
                return False
            
            # 步骤2: 查找匹配的标签页
            target_tab = self._find_target_tab(tabs, tab_url_pattern, tab_title_pattern)
                        
            # 如果没有找到匹配的标签页，使用第一个标签页
            if not target_tab:
                target_tab = tabs[0]  # 默认使用第一个标签页
                
            # 步骤3: 连接到目标标签页的WebSocket
            # 每个标签页都有一个唯一的WebSocket调试URL
            ws_url = target_tab['webSocketDebuggerUrl']
            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True
            
            # 记录连接成功信息
            logger.info(f"已连接到Chrome DevTools: {target_tab.get('title', 'Unknown')}")
            logger.info(f"标签页URL: {target_tab.get('url', 'Unknown')}")
            
            # 步骤4: 启动事件监听任务
            # 创建后台任务来持续监听Chrome发送的事件
            asyncio.create_task(self._event_listener())
            
            return True
            
        except Exception as e:
            logger.error(f"连接Chrome DevTools失败: {e}")
            return False
    
    def _find_target_tab(self, tabs: List[Dict], url_pattern: str = None, title_pattern: str = None) -> Optional[Dict]:
        """
        查找目标标签页
        
        匹配算法：
        1. 优先匹配URL模式（如果提供）
        2. 其次匹配标题模式（如果提供）
        3. 使用简单的字符串包含匹配
        
        Args:
            tabs: 标签页信息列表，每个元素包含url、title、webSocketDebuggerUrl等字段
            url_pattern: URL匹配模式
            title_pattern: 标题匹配模式
            
        Returns:
            匹配的标签页信息字典，未找到则返回None
            
        标签页信息结构示例：
        {
            "description": "",
            "devtoolsFrontendUrl": "/devtools/inspector.html?ws=localhost:9222/devtools/page/...",
            "id": "page_id",
            "title": "页面标题",
            "type": "page",
            "url": "https://example.com",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/..."
        }
        """
        for tab in tabs:
            # 优先匹配URL模式
            if url_pattern and url_pattern in tab.get('url', ''):
                return tab
            # 其次匹配标题模式
            if title_pattern and title_pattern in tab.get('title', ''):
                return tab
        return None
    
    async def _send_command(self, method: str, params: Dict = None) -> Dict:
        """
        发送CDP命令并等待响应
        
        Chrome DevTools Protocol (CDP) 使用JSON-RPC 2.0格式：
        请求格式：
        {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": "document.title"}
        }
        
        响应格式：
        {
            "id": 1,
            "result": {"type": "string", "value": "页面标题"}
        }
        
        或错误响应：
        {
            "id": 1,
            "error": {"code": -32000, "message": "错误信息"}
        }
        
        Args:
            method: CDP方法名，格式为 "Domain.method"
                   例如: "Runtime.evaluate", "Network.enable"
            params: 命令参数字典，可选
            
        Returns:
            命令响应字典，包含result或error字段
            
        实现要点：
        1. 每个命令都有唯一的ID，用于匹配请求和响应
        2. 使用WebSocket发送JSON格式的命令
        3. 循环接收消息直到找到匹配ID的响应
        4. 忽略事件消息（由事件监听器处理）
        """
        if not self.websocket:
            raise Exception("WebSocket未连接")
            
        # 构造CDP命令
        command = {
            "id": self.command_id,  # 唯一命令ID
            "method": method,       # CDP方法名
            "params": params or {}  # 参数，默认为空字典
        }
        
        # 发送命令到Chrome
        await self.websocket.send(json.dumps(command))
        
        # 保存当前命令ID，用于响应匹配
        current_id = self.command_id
        self.command_id += 1  # 递增命令ID计数器
        
        # 等待响应
        while True:
            # 接收WebSocket消息
            response = await self.websocket.recv()
            data = json.loads(response)
            
            # 检查是否是我们发送的命令的响应
            if data.get('id') == current_id:
                return data
            # 如果不是，继续等待（其他消息由事件监听器处理）
    
    async def _event_listener(self):
        """
        事件监听器，处理Chrome DevTools事件
        
        Chrome会主动发送各种事件，如：
        - Runtime.consoleAPICalled: 控制台输出
        - Network.requestWillBeSent: 网络请求
        - Page.loadEventFired: 页面加载完成
        
        事件消息格式：
        {
            "method": "Runtime.consoleAPICalled",
            "params": {
                "type": "log",
                "args": [{"type": "string", "value": "Hello World"}]
            }
        }
        
        注意：事件消息没有"id"字段，这是区分事件和命令响应的关键
        
        实现要点：
        1. 持续监听WebSocket消息
        2. 识别事件消息（无id字段）
        3. 调用注册的事件处理器
        4. 异常隔离，单个处理器异常不影响其他处理器
        5. 连接断开时优雅退出
        """
        try:
            # 持续监听，直到连接断开
            while self.is_connected and self.websocket:
                # 接收WebSocket消息
                response = await self.websocket.recv()
                data = json.loads(response)
                
                # 处理事件（没有id字段的消息）
                if 'method' in data and 'id' not in data:
                    method = data['method']  # 事件名称
                    params = data.get('params', {})  # 事件参数
                    
                    # 调用注册的事件处理器
                    if method in self.event_handlers:
                        # 遍历该事件的所有处理器
                        for handler in self.event_handlers[method]:
                            try:
                                # 异步调用处理器
                                await handler(params)
                            except Exception as e:
                                # 单个处理器异常不影响其他处理器
                                logger.error(f"事件处理器执行失败 {method}: {e}")
                                
        except websockets.exceptions.ConnectionClosed:
            # WebSocket连接正常关闭
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            # 其他异常
            logger.error(f"事件监听器异常: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """
        添加事件处理器
        
        支持为同一个事件注册多个处理器，处理器按注册顺序执行。
        
        Args:
            event_name: 事件名称，格式为 "Domain.eventName"
                       例如: "Runtime.consoleAPICalled", "Network.requestWillBeSent"
            handler: 事件处理函数，必须是异步函数
                    函数签名: async def handler(params: Dict) -> None
                    
        示例:
            async def console_handler(params):
                print(f"控制台消息: {params}")
            
            client.add_event_handler("Runtime.consoleAPICalled", console_handler)
        """
        # 如果事件名称不存在，创建新的处理器列表
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        # 添加处理器到列表
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """
        移除事件处理器
        
        Args:
            event_name: 事件名称
            handler: 要移除的处理器函数
        """
        if event_name in self.event_handlers:
            try:
                # 从处理器列表中移除指定处理器
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                # 处理器不存在，忽略错误
                pass
    
    async def enable_domain(self, domain: str) -> bool:
        """
        启用指定的DevTools域
        
        Chrome DevTools按功能分为多个域：
        - Runtime: JavaScript执行和调试
        - Network: 网络监控
        - Performance: 性能分析
        - Storage: 存储管理
        - Page: 页面控制
        - DOM: DOM操作
        
        启用域后才能使用该域的功能和接收相关事件。
        
        Args:
            domain: 域名，例如 'Runtime', 'Network', 'Performance'
            
        Returns:
            bool: 是否启用成功
            
        实现细节：
        - 发送 "{Domain}.enable" 命令
        - 检查响应中的错误信息
        - 更新已启用域集合
        """
        try:
            # 发送域启用命令
            response = await self._send_command(f"{domain}.enable")
            
            # 检查是否有错误
            if 'error' in response:
                logger.error(f"启用域 {domain} 失败: {response['error']}")
                return False
                
            # 添加到已启用域集合
            self.enabled_domains.add(domain)
            logger.info(f"已启用域: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"启用域 {domain} 异常: {e}")
            return False
    
    async def disable_domain(self, domain: str) -> bool:
        """
        禁用指定的DevTools域
        
        禁用域可以减少不必要的事件和提高性能。
        
        Args:
            domain: 要禁用的域名
            
        Returns:
            bool: 是否禁用成功
        """
        try:
            # 发送域禁用命令
            response = await self._send_command(f"{domain}.disable")
            
            # 检查是否有错误
            if 'error' in response:
                logger.error(f"禁用域 {domain} 失败: {response['error']}")
                return False
                
            # 从已启用域集合中移除
            self.enabled_domains.discard(domain)
            logger.info(f"已禁用域: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"禁用域 {domain} 异常: {e}")
            return False
    
    async def execute_command(self, method: str, params: Dict = None) -> Dict:
        """
        执行通用CDP命令
        
        这是对 _send_command 的高级封装，提供：
        1. 统一的返回格式
        2. 错误处理和转换
        3. 时间戳记录
        4. 异常捕获
        
        Args:
            method: CDP方法名，格式为 "Domain.method"
            params: 命令参数字典，可选
            
        Returns:
            Dict: 统一格式的执行结果
            成功时：
            {
                "success": True,
                "result": {...},  # CDP响应的result字段
                "timestamp": "2023-12-01T10:30:00"
            }
            失败时：
            {
                "success": False,
                "error": "错误信息"
            }
            
        使用示例：
            # 执行JavaScript代码
            result = await client.execute_command(
                "Runtime.evaluate",
                {"expression": "document.title"}
            )
            
            if result["success"]:
                title = result["result"]["result"]["value"]
                print(f"页面标题: {title}")
            else:
                print(f"执行失败: {result['error']}")
        """
        try:
            # 发送CDP命令
            response = await self._send_command(method, params)
            
            # 检查CDP级别的错误
            if 'error' in response:
                logger.error(f"CDP命令执行失败 {method}: {response['error']}")
                return {"success": False, "error": response['error']}
            
            # 返回成功结果
            return {
                "success": True,
                "result": response.get('result', {}),  # CDP响应的result字段
                "timestamp": datetime.now().isoformat()  # 添加时间戳
            }
            
        except Exception as e:
            # 捕获异常并转换为统一格式
            logger.error(f"执行CDP命令失败 {method}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_tabs(self) -> List[Dict]:
        """
        获取所有可用的标签页
        
        通过Chrome的HTTP API获取当前所有打开的标签页信息。
        
        Returns:
            List[Dict]: 标签页信息列表
            每个标签页包含以下字段：
            - id: 标签页ID
            - title: 页面标题
            - url: 页面URL
            - type: 类型（通常是"page"）
            - webSocketDebuggerUrl: WebSocket调试URL
            
        使用示例：
            tabs = await client.get_tabs()
            for tab in tabs:
                print(f"标题: {tab['title']}")
                print(f"URL: {tab['url']}")
        """
        try:
            # 使用HTTP客户端请求标签页列表
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self.host}:{self.debug_port}/json') as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取标签页列表失败: {e}")
            return []
    
    async def disconnect(self):
        """
        断开连接
        
        清理步骤：
        1. 设置连接状态为False（停止事件监听循环）
        2. 关闭WebSocket连接
        3. 记录断开连接日志
        
        注意：事件监听任务会在下次循环时自动退出
        """
        self.is_connected = False  # 停止事件监听循环
        if self.websocket:
            await self.websocket.close()  # 关闭WebSocket连接
            logger.info("已断开Chrome DevTools连接")
    
    def __del__(self):
        """
        析构函数，确保连接被关闭
        
        在对象被垃圾回收时自动调用，确保WebSocket连接被正确关闭。
        
        注意：在异步环境中，析构函数中的异步操作可能不会正确执行，
        建议显式调用disconnect()方法。
        """
        if self.is_connected and self.websocket:
            # 创建清理任务（可能不会执行）
            asyncio.create_task(self.disconnect())

# 使用示例和最佳实践
"""
基础使用示例：

import asyncio
from chrome_devtools_lib import ChromeDevToolsClient

async def basic_example():
    # 1. 创建客户端实例
    client = ChromeDevToolsClient()
    
    try:
        # 2. 连接到Chrome
        if not await client.connect():
            print("连接失败")
            return
        
        # 3. 启用需要的域
        await client.enable_domain("Runtime")
        
        # 4. 执行命令
        result = await client.execute_command(
            "Runtime.evaluate",
            {"expression": "document.title"}
        )
        
        if result["success"]:
            print(f"页面标题: {result['result']['result']['value']}")
        
    finally:
        # 5. 确保断开连接
        await client.disconnect()

# 事件监听示例：

async def event_example():
    client = ChromeDevToolsClient()
    
    # 定义事件处理器
    async def console_handler(params):
        args = params.get('args', [])
        if args:
            message = args[0].get('value', '')
            print(f"控制台消息: {message}")
    
    try:
        await client.connect()
        await client.enable_domain("Runtime")
        
        # 注册事件处理器
        client.add_event_handler("Runtime.consoleAPICalled", console_handler)
        
        # 执行会产生控制台输出的代码
        await client.execute_command(
            "Runtime.evaluate",
            {"expression": "console.log('Hello from Chrome!')"}
        )
        
        # 等待事件
        await asyncio.sleep(1)
        
    finally:
        await client.disconnect()

# 运行示例
if __name__ == "__main__":
    asyncio.run(basic_example())
"""