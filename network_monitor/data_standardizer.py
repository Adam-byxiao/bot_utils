#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据标准化处理引擎
用于将网络数据转换为统一的标准格式
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class StandardizedRequest:
    """标准化请求数据结构"""
    id: str
    timestamp: str
    method: str
    url: str
    domain: str
    path: str
    endpoint: str
    query_parameters: Dict[str, Any]
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    content_type: Optional[str]
    size_bytes: int
    is_api: bool
    api_version: Optional[str]
    
@dataclass
class StandardizedResponse:
    """标准化响应数据结构"""
    id: str
    timestamp: str
    status_code: int
    status_category: str  # success, client_error, server_error, redirect
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    content_type: str
    size_bytes: int
    is_json: bool
    response_time_ms: float
    
@dataclass
class StandardizedTransaction:
    """标准化网络事务"""
    transaction_id: str
    session_id: str
    timestamp: str
    request: StandardizedRequest
    response: StandardizedResponse
    duration_ms: float
    success: bool
    error_message: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]

class DataStandardizer:
    """数据标准化处理器"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.api_patterns = {
            'rest_api': [r'/api/', r'/rest/', r'/v\d+/'],
            'graphql': [r'/graphql', r'/graph'],
            'json_rpc': [r'/rpc', r'/jsonrpc'],
            'websocket': [r'/ws/', r'/websocket']
        }
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'x-csrf-token', 'x-session-id', 'x-user-token'
        }
        
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def standardize_transaction(self, transaction_data: Dict) -> StandardizedTransaction:
        """标准化网络事务数据"""
        try:
            request_data = transaction_data['request']
            response_data = transaction_data.get('response')
            
            # 标准化请求
            std_request = self._standardize_request(request_data)
            
            # 标准化响应
            if response_data:
                std_response = self._standardize_response(response_data, std_request.id)
                success = std_response.status_code < 400
                error_message = None
            else:
                # 处理失败的请求
                std_response = self._create_error_response(std_request.id)
                success = False
                error_message = transaction_data.get('error', 'Request failed')
            
            # 计算持续时间
            duration_ms = transaction_data.get('duration_ms', 0)
            if 'duration' in transaction_data:
                duration_ms = transaction_data['duration'] * 1000
            
            # 生成标签
            tags = self._generate_tags(std_request, std_response)
            
            # 生成元数据
            metadata = self._generate_metadata(std_request, std_response, transaction_data)
            
            return StandardizedTransaction(
                transaction_id=std_request.id,
                session_id=self.session_id,
                timestamp=std_request.timestamp,
                request=std_request,
                response=std_response,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                tags=tags,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"标准化事务数据失败: {e}")
            raise
    
    def _standardize_request(self, request_data: Dict) -> StandardizedRequest:
        """标准化请求数据"""
        url = request_data['url']
        parsed_url = urlparse(url)
        
        # 提取API版本
        api_version = self._extract_api_version(parsed_url.path)
        
        # 标准化端点
        endpoint = self._normalize_endpoint(parsed_url.path)
        
        # 处理查询参数
        query_params = request_data.get('query_params', {})
        normalized_query = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                          for k, v in query_params.items()}
        
        # 处理请求头（移除敏感信息）
        headers = self._sanitize_headers(request_data.get('headers', {}))
        
        # 处理请求体
        body = request_data.get('body_data')
        if body and isinstance(body, dict) and '_raw_data' in body:
            body = None  # 不包含原始数据
        
        # 计算请求大小
        size_bytes = 0
        if body:
            size_bytes = len(json.dumps(body, ensure_ascii=False).encode('utf-8'))
        
        return StandardizedRequest(
            id=request_data['request_id'],
            timestamp=request_data['request_time'],
            method=request_data['method'].upper(),
            url=url,
            domain=parsed_url.netloc,
            path=parsed_url.path,
            endpoint=endpoint,
            query_parameters=normalized_query,
            headers=headers,
            body=body,
            content_type=request_data.get('content_type'),
            size_bytes=size_bytes,
            is_api=self._is_api_request(url),
            api_version=api_version
        )
    
    def _standardize_response(self, response_data: Dict, request_id: str) -> StandardizedResponse:
        """标准化响应数据"""
        status_code = response_data['status']
        
        # 分类状态码
        status_category = self._categorize_status_code(status_code)
        
        # 处理响应头
        headers = self._sanitize_headers(response_data.get('headers', {}))
        
        # 处理响应体
        body = response_data.get('response_data')
        if body and isinstance(body, dict) and '_raw_data' in body:
            body = None  # 不包含原始数据
        
        # 计算响应大小
        size_bytes = response_data.get('content_length', 0)
        if not size_bytes and body:
            size_bytes = len(json.dumps(body, ensure_ascii=False).encode('utf-8'))
        
        return StandardizedResponse(
            id=request_id,
            timestamp=response_data['response_time'],
            status_code=status_code,
            status_category=status_category,
            headers=headers,
            body=body,
            content_type=response_data.get('content_type', ''),
            size_bytes=size_bytes,
            is_json=response_data.get('is_json', False),
            response_time_ms=0  # 将在事务级别计算
        )
    
    def _create_error_response(self, request_id: str) -> StandardizedResponse:
        """创建错误响应"""
        return StandardizedResponse(
            id=request_id,
            timestamp=datetime.now().isoformat(),
            status_code=0,
            status_category='error',
            headers={},
            body=None,
            content_type='',
            size_bytes=0,
            is_json=False,
            response_time_ms=0
        )
    
    def _extract_api_version(self, path: str) -> Optional[str]:
        """提取API版本"""
        version_patterns = [r'/v(\d+)', r'/api/v(\d+)', r'/(\d+\.\d+)']
        
        for pattern in version_patterns:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _normalize_endpoint(self, path: str) -> str:
        """标准化端点路径"""
        # 移除查询参数
        endpoint = path.split('?')[0]
        
        # 替换数字ID为占位符
        endpoint = re.sub(r'/\d+(?=/|$)', '/{id}', endpoint)
        
        # 替换UUID为占位符
        uuid_pattern = r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=/|$)'
        endpoint = re.sub(uuid_pattern, '/{uuid}', endpoint, flags=re.IGNORECASE)
        
        return endpoint
    
    def _is_api_request(self, url: str) -> bool:
        """判断是否为API请求"""
        for api_type, patterns in self.api_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
        
        # 检查文件扩展名
        if url.endswith(('.json', '.xml', '.api')):
            return True
        
        return False
    
    def _categorize_status_code(self, status_code: int) -> str:
        """分类HTTP状态码"""
        if 200 <= status_code < 300:
            return 'success'
        elif 300 <= status_code < 400:
            return 'redirect'
        elif 400 <= status_code < 500:
            return 'client_error'
        elif 500 <= status_code < 600:
            return 'server_error'
        else:
            return 'unknown'
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """清理敏感请求头"""
        sanitized = {}
        
        for key, value in headers.items():
            key_lower = key.lower()
            
            if key_lower in self.sensitive_headers:
                sanitized[key] = '[REDACTED]'
            elif key_lower == 'cookie':
                sanitized[key] = '[REDACTED]'
            elif 'token' in key_lower or 'auth' in key_lower:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _generate_tags(self, request: StandardizedRequest, response: StandardizedResponse) -> List[str]:
        """生成标签"""
        tags = []
        
        # 请求方法标签
        tags.append(f"method:{request.method.lower()}")
        
        # API类型标签
        if request.is_api:
            tags.append("api")
            
            # 具体API类型
            for api_type, patterns in self.api_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, request.url, re.IGNORECASE):
                        tags.append(f"api_type:{api_type}")
                        break
        
        # 状态标签
        tags.append(f"status:{response.status_category}")
        tags.append(f"status_code:{response.status_code}")
        
        # 内容类型标签
        if response.content_type:
            main_type = response.content_type.split('/')[0]
            tags.append(f"content_type:{main_type}")
        
        # 域名标签
        tags.append(f"domain:{request.domain}")
        
        # API版本标签
        if request.api_version:
            tags.append(f"api_version:v{request.api_version}")
        
        return tags
    
    def _generate_metadata(self, request: StandardizedRequest, response: StandardizedResponse, 
                          raw_data: Dict) -> Dict[str, Any]:
        """生成元数据"""
        metadata = {
            'request_size_bytes': request.size_bytes,
            'response_size_bytes': response.size_bytes,
            'total_size_bytes': request.size_bytes + response.size_bytes,
            'has_query_params': bool(request.query_parameters),
            'has_request_body': request.body is not None,
            'has_response_body': response.body is not None,
            'is_secure': request.url.startswith('https://'),
            'endpoint_normalized': request.endpoint
        }
        
        # 添加性能指标
        if 'duration_ms' in raw_data:
            duration_ms = raw_data['duration_ms']
            metadata['performance_category'] = self._categorize_performance(duration_ms)
        
        # 添加错误信息
        if 'error' in raw_data:
            metadata['error_type'] = 'network_error'
            metadata['error_details'] = raw_data['error']
        
        return metadata
    
    def _categorize_performance(self, duration_ms: float) -> str:
        """分类性能表现"""
        if duration_ms < 100:
            return 'fast'
        elif duration_ms < 500:
            return 'normal'
        elif duration_ms < 2000:
            return 'slow'
        else:
            return 'very_slow'
    
    def to_dict(self, transaction: StandardizedTransaction) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(transaction)
    
    def to_json(self, transaction: StandardizedTransaction) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(transaction), ensure_ascii=False, indent=2)
    
    def batch_standardize(self, transactions: List[Dict]) -> List[StandardizedTransaction]:
        """批量标准化处理"""
        standardized = []
        
        for transaction_data in transactions:
            try:
                std_transaction = self.standardize_transaction(transaction_data)
                standardized.append(std_transaction)
            except Exception as e:
                logger.error(f"标准化事务失败: {e}")
                continue
        
        return standardized

# 示例使用
if __name__ == "__main__":
    standardizer = DataStandardizer()
    
    # 示例数据
    sample_transaction = {
        'request': {
            'request_id': 'test-123',
            'url': 'https://api.example.com/v1/users/123?include=profile',
            'method': 'GET',
            'headers': {
                'Authorization': 'Bearer token123',
                'Content-Type': 'application/json'
            },
            'request_time': '2024-01-01T12:00:00.000Z',
            'query_params': {'include': ['profile']}
        },
        'response': {
            'status': 200,
            'status_text': 'OK',
            'headers': {'content-type': 'application/json'},
            'response_time': '2024-01-01T12:00:00.250Z',
            'response_data': {'user': {'id': 123, 'name': 'John'}},
            'is_json': True,
            'content_length': 45
        },
        'duration_ms': 250
    }
    
    std_transaction = standardizer.standardize_transaction(sample_transaction)
    print("标准化事务:")
    print(standardizer.to_json(std_transaction))