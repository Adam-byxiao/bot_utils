#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Protocol 网络监听器
用于监听和捕获Chrome浏览器的网络请求和响应
"""

import json
import time
import asyncio
import websockets
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NetworkRequest:
    """网络请求数据结构"""
    request_id: str
    url: str
    method: str
    headers: Dict
    timestamp: float
    request_time: str
    post_data: Optional[str] = None
    
@dataclass
class NetworkResponse:
    """网络响应数据结构"""
    request_id: str
    status: int
    status_text: str
    headers: Dict
    timestamp: float
    response_time: str
    mime_type: str
    response_body: Optional[str] = None
    response_size: int = 0

class ChromeNetworkListener:
    """Chrome DevTools Protocol 网络监听器"""
    
    def __init__(self, debug_port: int = 9222, host: str = 'localhost'):
        self.debug_port = debug_port
        self.host = host
        self.websocket = None
        self.is_connected = False
        self.requests: Dict[str, NetworkRequest] = {}
        self.responses: Dict[str, NetworkResponse] = {}
        self.completed_requests: List[Dict] = []
        self.request_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
        
    async def connect(self) -> bool:
        """连接到Chrome DevTools"""
        try:
            # 获取可用的标签页
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self.host}:{self.debug_port}/json') as resp:
                    tabs = await resp.json()
                    
            if not tabs:
                logger.error("没有找到可用的Chrome标签页")
                return False
                
            # 连接到第一个标签页的WebSocket
            tab = tabs[0]
            ws_url = tab['webSocketDebuggerUrl']
            
            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True
            
            # 启用网络域
            await self._send_command("Network.enable")
            await self._send_command("Runtime.enable")
            
            logger.info(f"已连接到Chrome DevTools: {tab['title']}")
            return True
            
        except Exception as e:
            logger.error(f"连接Chrome DevTools失败: {e}")
            return False
    
    async def _send_command(self, method: str, params: Dict = None) -> Dict:
        """发送CDP命令"""
        if not self.websocket:
            raise Exception("WebSocket未连接")
            
        command = {
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(command))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def start_monitoring(self):
        """开始监听网络事件"""
        if not self.is_connected:
            logger.error("请先连接到Chrome DevTools")
            return
            
        logger.info("开始监听网络事件...")
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_event(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
            self.is_connected = False
        except Exception as e:
            logger.error(f"监听网络事件时发生错误: {e}")
    
    async def _handle_event(self, event: Dict):
        """处理CDP事件"""
        method = event.get('method')
        params = event.get('params', {})
        
        if method == 'Network.requestWillBeSent':
            await self._handle_request_sent(params)
        elif method == 'Network.responseReceived':
            await self._handle_response_received(params)
        elif method == 'Network.loadingFinished':
            await self._handle_loading_finished(params)
        elif method == 'Network.loadingFailed':
            await self._handle_loading_failed(params)
    
    async def _handle_request_sent(self, params: Dict):
        """处理请求发送事件"""
        request_id = params['requestId']
        request_data = params['request']
        
        network_request = NetworkRequest(
            request_id=request_id,
            url=request_data['url'],
            method=request_data['method'],
            headers=request_data.get('headers', {}),
            timestamp=params['timestamp'],
            request_time=datetime.fromtimestamp(params['timestamp']).isoformat(),
            post_data=request_data.get('postData')
        )
        
        self.requests[request_id] = network_request
        
        if self.request_callback:
            await self.request_callback(network_request)
            
        logger.debug(f"请求发送: {request_data['method']} {request_data['url']}")
    
    async def _handle_response_received(self, params: Dict):
        """处理响应接收事件"""
        request_id = params['requestId']
        response_data = params['response']
        
        network_response = NetworkResponse(
            request_id=request_id,
            status=response_data['status'],
            status_text=response_data['statusText'],
            headers=response_data.get('headers', {}),
            timestamp=params['timestamp'],
            response_time=datetime.fromtimestamp(params['timestamp']).isoformat(),
            mime_type=response_data.get('mimeType', ''),
            response_size=response_data.get('encodedDataLength', 0)
        )
        
        self.responses[request_id] = network_response
        
        if self.response_callback:
            await self.response_callback(network_response)
            
        logger.debug(f"响应接收: {response_data['status']} {response_data.get('url', '')}")
    
    async def _handle_loading_finished(self, params: Dict):
        """处理加载完成事件"""
        request_id = params['requestId']
        
        if request_id in self.requests and request_id in self.responses:
            request = self.requests[request_id]
            response = self.responses[request_id]
            
            # 尝试获取响应体
            try:
                body_result = await self._send_command(
                    "Network.getResponseBody",
                    {"requestId": request_id}
                )
                if 'result' in body_result:
                    response.response_body = body_result['result'].get('body')
            except Exception as e:
                logger.debug(f"获取响应体失败: {e}")
            
            # 合并请求和响应数据
            completed_request = {
                'request': asdict(request),
                'response': asdict(response),
                'duration': response.timestamp - request.timestamp
            }
            
            self.completed_requests.append(completed_request)
            
            # 清理已完成的请求
            del self.requests[request_id]
            del self.responses[request_id]
            
            logger.debug(f"请求完成: {request.method} {request.url} - {response.status}")
    
    async def _handle_loading_failed(self, params: Dict):
        """处理加载失败事件"""
        request_id = params['requestId']
        error_text = params.get('errorText', 'Unknown error')
        
        if request_id in self.requests:
            request = self.requests[request_id]
            
            failed_request = {
                'request': asdict(request),
                'error': error_text,
                'timestamp': params['timestamp']
            }
            
            self.completed_requests.append(failed_request)
            
            # 清理失败的请求
            del self.requests[request_id]
            if request_id in self.responses:
                del self.responses[request_id]
                
            logger.debug(f"请求失败: {request.method} {request.url} - {error_text}")
    
    def set_request_callback(self, callback: Callable):
        """设置请求回调函数"""
        self.request_callback = callback
    
    def set_response_callback(self, callback: Callable):
        """设置响应回调函数"""
        self.response_callback = callback
    
    def get_completed_requests(self) -> List[Dict]:
        """获取已完成的请求列表"""
        return self.completed_requests.copy()
    
    def clear_completed_requests(self):
        """清空已完成的请求列表"""
        self.completed_requests.clear()
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("已断开Chrome DevTools连接")

# 示例使用
if __name__ == "__main__":
    async def main():
        listener = ChromeNetworkListener()
        
        if await listener.connect():
            # 设置回调函数
            async def on_request(request: NetworkRequest):
                print(f"请求: {request.method} {request.url}")
            
            async def on_response(response: NetworkResponse):
                print(f"响应: {response.status} {response.mime_type}")
            
            listener.set_request_callback(on_request)
            listener.set_response_callback(on_response)
            
            # 开始监听
            await listener.start_monitoring()
    
    asyncio.run(main())