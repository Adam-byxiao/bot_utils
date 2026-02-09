#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Domain
Chrome DevTools Network域的实现，用于网络监控和分析
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class NetworkDomain:
    """Network域实现"""
    
    def __init__(self, client):
        """
        初始化Network域
        
        Args:
            client: ChromeDevToolsClient实例
        """
        self.client = client
        self.domain_name = "Network"
        self.request_handlers = []
        self.response_handlers = []
    
    async def enable(self, max_total_buffer_size: Optional[int] = None,
                    max_resource_buffer_size: Optional[int] = None,
                    max_post_data_size: Optional[int] = None) -> bool:
        """
        启用Network域
        
        Args:
            max_total_buffer_size: 最大总缓冲区大小
            max_resource_buffer_size: 最大资源缓冲区大小
            max_post_data_size: 最大POST数据大小
        """
        params = {}
        if max_total_buffer_size is not None:
            params["maxTotalBufferSize"] = max_total_buffer_size
        if max_resource_buffer_size is not None:
            params["maxResourceBufferSize"] = max_resource_buffer_size
        if max_post_data_size is not None:
            params["maxPostDataSize"] = max_post_data_size
        
        result = await self.client.execute_command("Network.enable", params)
        
        if result["success"]:
            # 注册事件处理器
            self.client.add_event_handler("Network.requestWillBeSent", self._handle_request)
            self.client.add_event_handler("Network.responseReceived", self._handle_response)
            self.client.add_event_handler("Network.loadingFinished", self._handle_loading_finished)
            self.client.add_event_handler("Network.loadingFailed", self._handle_loading_failed)
            
        return result["success"]
    
    async def disable(self) -> bool:
        """禁用Network域"""
        return await self.client.disable_domain(self.domain_name)
    
    async def _handle_request(self, params: Dict):
        """处理请求事件"""
        for handler in self.request_handlers:
            try:
                await handler(params)
            except Exception as e:
                logger.error(f"请求处理器执行失败: {e}")
    
    async def _handle_response(self, params: Dict):
        """处理响应事件"""
        for handler in self.response_handlers:
            try:
                await handler(params)
            except Exception as e:
                logger.error(f"响应处理器执行失败: {e}")
    
    async def _handle_loading_finished(self, params: Dict):
        """处理加载完成事件"""
        logger.debug(f"加载完成: {params.get('requestId')}")
    
    async def _handle_loading_failed(self, params: Dict):
        """处理加载失败事件"""
        logger.warning(f"加载失败: {params.get('requestId')} - {params.get('errorText')}")
    
    def add_request_handler(self, handler):
        """添加请求处理器"""
        self.request_handlers.append(handler)
    
    def add_response_handler(self, handler):
        """添加响应处理器"""
        self.response_handlers.append(handler)
    
    async def set_cache_disabled(self, cache_disabled: bool) -> Dict:
        """
        设置是否禁用缓存
        
        Args:
            cache_disabled: 是否禁用缓存
        """
        params = {"cacheDisabled": cache_disabled}
        return await self.client.execute_command("Network.setCacheDisabled", params)
    
    async def set_user_agent_override(self, user_agent: str,
                                    accept_language: Optional[str] = None,
                                    platform: Optional[str] = None) -> Dict:
        """
        设置用户代理覆盖
        
        Args:
            user_agent: 用户代理字符串
            accept_language: 接受语言
            platform: 平台
        """
        params = {"userAgent": user_agent}
        if accept_language is not None:
            params["acceptLanguage"] = accept_language
        if platform is not None:
            params["platform"] = platform
        
        return await self.client.execute_command("Network.setUserAgentOverride", params)
    
    async def get_response_body(self, request_id: str) -> Dict:
        """
        获取响应体
        
        Args:
            request_id: 请求ID
        """
        params = {"requestId": request_id}
        return await self.client.execute_command("Network.getResponseBody", params)
    
    async def get_request_post_data(self, request_id: str) -> Dict:
        """
        获取请求POST数据
        
        Args:
            request_id: 请求ID
        """
        params = {"requestId": request_id}
        return await self.client.execute_command("Network.getRequestPostData", params)
    
    async def clear_browser_cache(self) -> Dict:
        """清除浏览器缓存"""
        return await self.client.execute_command("Network.clearBrowserCache")
    
    async def clear_browser_cookies(self) -> Dict:
        """清除浏览器Cookie"""
        return await self.client.execute_command("Network.clearBrowserCookies")
    
    async def get_cookies(self, urls: Optional[List[str]] = None) -> Dict:
        """
        获取Cookie
        
        Args:
            urls: URL列表，如果为None则获取所有Cookie
        """
        params = {}
        if urls is not None:
            params["urls"] = urls
        
        return await self.client.execute_command("Network.getCookies", params)
    
    async def set_cookie(self, name: str, value: str,
                        url: Optional[str] = None,
                        domain: Optional[str] = None,
                        path: Optional[str] = None,
                        secure: Optional[bool] = None,
                        http_only: Optional[bool] = None,
                        same_site: Optional[str] = None,
                        expires: Optional[float] = None,
                        priority: Optional[str] = None) -> Dict:
        """
        设置Cookie
        
        Args:
            name: Cookie名称
            value: Cookie值
            url: URL
            domain: 域名
            path: 路径
            secure: 是否安全
            http_only: 是否仅HTTP
            same_site: SameSite策略
            expires: 过期时间
            priority: 优先级
        """
        params = {"name": name, "value": value}
        
        if url is not None:
            params["url"] = url
        if domain is not None:
            params["domain"] = domain
        if path is not None:
            params["path"] = path
        if secure is not None:
            params["secure"] = secure
        if http_only is not None:
            params["httpOnly"] = http_only
        if same_site is not None:
            params["sameSite"] = same_site
        if expires is not None:
            params["expires"] = expires
        if priority is not None:
            params["priority"] = priority
        
        return await self.client.execute_command("Network.setCookie", params)