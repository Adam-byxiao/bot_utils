#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified API for Chrome DevTools Client
提供类似 PyChromeDevTools 的简化 API 调用方式
"""

from typing import Dict, Any, Optional, Tuple, List
from .client import ChromeDevToolsClient


class DomainProxy:
    """域代理类，提供简化的域方法调用"""
    
    def __init__(self, client: ChromeDevToolsClient, domain_name: str):
        self.client = client
        self.domain_name = domain_name
    
    def __getattr__(self, method_name: str):
        """动态生成域方法"""
        async def domain_method(**params):
            full_method = f"{self.domain_name}.{method_name}"
            result = await self.client.execute_command(full_method, params)
            
            if result.get('success'):
                return result.get('result', {}), []
            else:
                raise Exception(f"Command failed: {result.get('error')}")
        
        return domain_method


class SimplifiedChromeInterface:
    """
    简化的 Chrome DevTools 接口
    提供类似 PyChromeDevTools 的 API 调用方式
    """
    
    def __init__(self, host: str = 'localhost', port: int = 9222, suppress_origin: bool = False):
        """
        初始化简化接口
        
        Args:
            host: Chrome主机地址
            port: Chrome调试端口
            suppress_origin: 是否抑制Origin头部（Android环境）
        """
        self.client = ChromeDevToolsClient(
            debug_port=port,
            host=host,
            suppress_origin=suppress_origin
        )
        
        # 创建域代理
        self.Page = DomainProxy(self.client, 'Page')
        self.Runtime = DomainProxy(self.client, 'Runtime')
        self.Network = DomainProxy(self.client, 'Network')
        self.Performance = DomainProxy(self.client, 'Performance')
        self.Storage = DomainProxy(self.client, 'Storage')
        self.DOM = DomainProxy(self.client, 'DOM')
        self.CSS = DomainProxy(self.client, 'CSS')
        self.Debugger = DomainProxy(self.client, 'Debugger')
        self.Console = DomainProxy(self.client, 'Console')
        self.Security = DomainProxy(self.client, 'Security')
    
    async def connect(self, tab_url_pattern: str = None, tab_title_pattern: str = None) -> bool:
        """连接到 Chrome DevTools"""
        return await self.client.connect(tab_url_pattern, tab_title_pattern)
    
    async def connect_target_id(self, target_id: str) -> bool:
        """直接连接到指定的 targetID"""
        return await self.client.connect_target_id(target_id)
    
    async def wait_event(self, event_name: str, timeout: float = 60.0) -> Tuple[Optional[Dict], List[Dict]]:
        """
        等待特定事件
        
        Args:
            event_name: 事件名称
            timeout: 超时时间（秒）
            
        Returns:
            (匹配的事件, 所有接收到的事件)
        """
        return await self.client.wait_event(event_name, timeout)
    
    async def wait_message(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        等待单个消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            接收到的消息
        """
        return await self.client.wait_message(timeout)
    
    def pop_messages(self) -> List[Dict]:
        """获取所有已接收的消息（非阻塞）"""
        return self.client.pop_messages()
    
    async def enable_domain(self, domain: str) -> bool:
        """启用指定域"""
        return await self.client.enable_domain(domain)
    
    async def disable_domain(self, domain: str) -> bool:
        """禁用指定域"""
        return await self.client.disable_domain(domain)
    
    async def get_tabs(self) -> List[Dict]:
        """获取所有可用的标签页"""
        return await self.client.get_tabs()
    
    async def disconnect(self):
        """断开连接"""
        await self.client.disconnect()


# 为了兼容性，提供类似 PyChromeDevTools 的接口
class ChromeInterface(SimplifiedChromeInterface):
    """
    兼容 PyChromeDevTools 的接口类
    """
    pass


# 使用示例函数
async def example_usage():
    """使用示例"""
    # 创建接口实例
    chrome = ChromeInterface()
    
    # 连接到 Chrome
    await chrome.connect()
    
    # 启用域
    await chrome.Network.enable()
    await chrome.Page.enable()
    
    # 导航到页面
    result, messages = await chrome.Page.navigate(url="http://www.google.com/")
    
    # 等待页面加载完成
    event, all_events = await chrome.wait_event("Page.loadEventFired", timeout=60)
    
    # 获取 cookies
    cookies, messages = await chrome.Network.getCookies()
    
    # 断开连接
    await chrome.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())