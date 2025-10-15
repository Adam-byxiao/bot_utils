#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据捕获和解析模块
用于解析和处理从Chrome DevTools获取的网络数据
"""

import json
import re
import base64
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ParsedRequest:
    """解析后的请求数据"""
    url: str
    domain: str
    path: str
    method: str
    query_params: Dict[str, List[str]]
    headers: Dict[str, str]
    content_type: Optional[str]
    body_data: Optional[Dict[str, Any]]
    timestamp: float
    request_time: str

@dataclass
class ParsedResponse:
    """解析后的响应数据"""
    status_code: int
    status_text: str
    headers: Dict[str, str]
    content_type: str
    content_length: int
    response_data: Optional[Dict[str, Any]]
    timestamp: float
    response_time: str
    is_json: bool
    is_success: bool

@dataclass
class NetworkTransaction:
    """完整的网络事务"""
    transaction_id: str
    request: ParsedRequest
    response: ParsedResponse
    duration_ms: float
    error: Optional[str] = None

class DataParser:
    """数据解析器"""
    
    def __init__(self):
        self.json_content_types = [
            'application/json',
            'application/ld+json',
            'text/json'
        ]
        
        self.api_patterns = [
            r'/api/',
            r'/v\d+/',
            r'\.json$',
            r'/graphql',
            r'/rest/'
        ]
    
    def parse_request(self, raw_request: Dict) -> ParsedRequest:
        """解析原始请求数据"""
        try:
            url = raw_request['url']
            parsed_url = urlparse(url)
            
            # 解析查询参数
            query_params = parse_qs(parsed_url.query)
            
            # 解析请求头
            headers = raw_request.get('headers', {})
            content_type = headers.get('content-type', headers.get('Content-Type'))
            
            # 解析请求体
            body_data = None
            post_data = raw_request.get('post_data')
            if post_data:
                body_data = self._parse_request_body(post_data, content_type)
            
            return ParsedRequest(
                url=url,
                domain=parsed_url.netloc,
                path=parsed_url.path,
                method=raw_request['method'],
                query_params=query_params,
                headers=headers,
                content_type=content_type,
                body_data=body_data,
                timestamp=raw_request['timestamp'],
                request_time=raw_request['request_time']
            )
            
        except Exception as e:
            logger.error(f"解析请求数据失败: {e}")
            raise
    
    def parse_response(self, raw_response: Dict) -> ParsedResponse:
        """解析原始响应数据"""
        try:
            headers = raw_response.get('headers', {})
            content_type = headers.get('content-type', headers.get('Content-Type', ''))
            content_length = int(headers.get('content-length', headers.get('Content-Length', 0)) or 0)
            
            # 解析响应体
            response_data = None
            is_json = False
            
            response_body = raw_response.get('response_body')
            if response_body:
                response_data, is_json = self._parse_response_body(response_body, content_type)
            
            return ParsedResponse(
                status_code=raw_response['status'],
                status_text=raw_response['status_text'],
                headers=headers,
                content_type=content_type,
                content_length=content_length,
                response_data=response_data,
                timestamp=raw_response['timestamp'],
                response_time=raw_response['response_time'],
                is_json=is_json,
                is_success=200 <= raw_response['status'] < 300
            )
            
        except Exception as e:
            logger.error(f"解析响应数据失败: {e}")
            raise
    
    def _parse_request_body(self, post_data: str, content_type: Optional[str]) -> Optional[Dict[str, Any]]:
        """解析请求体数据"""
        if not post_data:
            return None
            
        try:
            # JSON数据
            if content_type and any(ct in content_type.lower() for ct in self.json_content_types):
                return json.loads(post_data)
            
            # 表单数据
            elif content_type and 'application/x-www-form-urlencoded' in content_type.lower():
                return dict(parse_qs(post_data))
            
            # 多部分表单数据
            elif content_type and 'multipart/form-data' in content_type.lower():
                return {'_raw_data': post_data, '_type': 'multipart'}
            
            # 其他类型，尝试解析为JSON
            else:
                try:
                    return json.loads(post_data)
                except json.JSONDecodeError:
                    return {'_raw_data': post_data, '_type': 'unknown'}
                    
        except Exception as e:
            logger.debug(f"解析请求体失败: {e}")
            return {'_raw_data': post_data, '_error': str(e)}
    
    def _parse_response_body(self, response_body: str, content_type: str) -> tuple[Optional[Dict[str, Any]], bool]:
        """解析响应体数据"""
        if not response_body:
            return None, False
            
        try:
            # JSON响应
            if any(ct in content_type.lower() for ct in self.json_content_types):
                try:
                    data = json.loads(response_body)
                    return data, True
                except json.JSONDecodeError:
                    return {'_raw_data': response_body, '_parse_error': 'Invalid JSON'}, False
            
            # HTML响应
            elif 'text/html' in content_type.lower():
                return {'_html_content': response_body[:1000], '_type': 'html'}, False
            
            # XML响应
            elif 'xml' in content_type.lower():
                return {'_xml_content': response_body[:1000], '_type': 'xml'}, False
            
            # 文本响应
            elif content_type.startswith('text/'):
                return {'_text_content': response_body[:1000], '_type': 'text'}, False
            
            # 二进制数据
            else:
                return {
                    '_binary_size': len(response_body),
                    '_content_type': content_type,
                    '_type': 'binary'
                }, False
                
        except Exception as e:
            logger.debug(f"解析响应体失败: {e}")
            return {'_raw_data': response_body[:500], '_error': str(e)}, False
    
    def create_transaction(self, raw_request_data: Dict) -> NetworkTransaction:
        """创建完整的网络事务"""
        try:
            request_data = raw_request_data['request']
            response_data = raw_request_data.get('response')
            
            parsed_request = self.parse_request(request_data)
            
            if response_data:
                parsed_response = self.parse_response(response_data)
                duration = raw_request_data.get('duration', 0) * 1000  # 转换为毫秒
                error = None
            else:
                # 处理失败的请求
                error = raw_request_data.get('error', 'Unknown error')
                parsed_response = ParsedResponse(
                    status_code=0,
                    status_text='Failed',
                    headers={},
                    content_type='',
                    content_length=0,
                    response_data=None,
                    timestamp=0,
                    response_time='',
                    is_json=False,
                    is_success=False
                )
                duration = 0
            
            return NetworkTransaction(
                transaction_id=request_data['request_id'],
                request=parsed_request,
                response=parsed_response,
                duration_ms=duration,
                error=error
            )
            
        except Exception as e:
            logger.error(f"创建网络事务失败: {e}")
            raise
    
    def is_api_request(self, url: str) -> bool:
        """判断是否为API请求"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in self.api_patterns)
    
    def extract_api_info(self, transaction: NetworkTransaction) -> Dict[str, Any]:
        """提取API相关信息"""
        request = transaction.request
        response = transaction.response
        
        api_info = {
            'endpoint': request.path,
            'method': request.method,
            'domain': request.domain,
            'is_api': self.is_api_request(request.url),
            'status_code': response.status_code,
            'is_success': response.is_success,
            'response_time_ms': transaction.duration_ms,
            'content_type': response.content_type,
            'has_json_response': response.is_json
        }
        
        # 提取查询参数
        if request.query_params:
            api_info['query_params'] = {k: v[0] if len(v) == 1 else v 
                                      for k, v in request.query_params.items()}
        
        # 提取请求体关键信息
        if request.body_data and isinstance(request.body_data, dict):
            if '_raw_data' not in request.body_data:
                api_info['request_data'] = request.body_data
        
        # 提取响应体关键信息
        if response.response_data and response.is_json:
            api_info['response_data'] = response.response_data
        
        return api_info
    
    def get_request_summary(self, transaction: NetworkTransaction) -> Dict[str, Any]:
        """获取请求摘要信息"""
        return {
            'id': transaction.transaction_id,
            'url': transaction.request.url,
            'method': transaction.request.method,
            'status': transaction.response.status_code,
            'duration_ms': transaction.duration_ms,
            'timestamp': transaction.request.timestamp,
            'is_api': self.is_api_request(transaction.request.url),
            'has_error': transaction.error is not None,
            'error': transaction.error
        }

# 示例使用
if __name__ == "__main__":
    parser = DataParser()
    
    # 示例数据
    sample_data = {
        'request': {
            'request_id': 'test-123',
            'url': 'https://api.example.com/v1/users?page=1',
            'method': 'GET',
            'headers': {'Content-Type': 'application/json'},
            'timestamp': 1234567890.123,
            'request_time': '2024-01-01T12:00:00'
        },
        'response': {
            'status': 200,
            'status_text': 'OK',
            'headers': {'content-type': 'application/json'},
            'timestamp': 1234567890.456,
            'response_time': '2024-01-01T12:00:00',
            'response_body': '{"users": [{"id": 1, "name": "John"}]}'
        },
        'duration': 0.333
    }
    
    transaction = parser.create_transaction(sample_data)
    api_info = parser.extract_api_info(transaction)
    summary = parser.get_request_summary(transaction)
    
    print("API信息:", json.dumps(api_info, indent=2, ensure_ascii=False))
    print("请求摘要:", json.dumps(summary, indent=2, ensure_ascii=False))