#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据过滤和去重模块
用于筛选有效的网络数据并移除重复请求
"""

import re
import hashlib
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class FilterRule:
    """过滤规则"""
    name: str
    rule_type: str  # include, exclude
    field: str  # url, method, status_code, content_type, domain
    pattern: str  # 正则表达式或精确匹配
    is_regex: bool = True
    enabled: bool = True

@dataclass
class FilterStats:
    """过滤统计信息"""
    total_requests: int = 0
    filtered_requests: int = 0
    duplicate_requests: int = 0
    static_resources: int = 0
    api_requests: int = 0
    error_requests: int = 0

class DataFilter:
    """数据过滤器"""
    
    def __init__(self):
        self.filter_rules: List[FilterRule] = []
        self.seen_requests: Set[str] = set()
        self.stats = FilterStats()
        
        # 默认静态资源扩展名
        self.static_extensions = {
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf',
            '.zip', '.tar', '.gz', '.map'
        }
        
        # 默认过滤规则
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认过滤规则"""
        default_rules = [
            # 排除静态资源
            FilterRule(
                name="exclude_static_resources",
                rule_type="exclude",
                field="url",
                pattern=r"\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|mp4|mp3|pdf|zip|tar|gz|map)($|\?)",
                is_regex=True
            ),
            
            # 排除浏览器预检请求
            FilterRule(
                name="exclude_preflight",
                rule_type="exclude",
                field="method",
                pattern="OPTIONS",
                is_regex=False
            ),
            
            # 排除Chrome扩展请求
            FilterRule(
                name="exclude_chrome_extensions",
                rule_type="exclude",
                field="url",
                pattern=r"^chrome-extension://",
                is_regex=True
            ),
            
            # 排除本地文件
            FilterRule(
                name="exclude_local_files",
                rule_type="exclude",
                field="url",
                pattern=r"^file://",
                is_regex=True
            ),
            
            # 包含API请求
            FilterRule(
                name="include_api_requests",
                rule_type="include",
                field="url",
                pattern=r"/(api|rest|graphql|v\d+)/",
                is_regex=True
            ),
            
            # 包含JSON响应
            FilterRule(
                name="include_json_responses",
                rule_type="include",
                field="content_type",
                pattern=r"application/json",
                is_regex=True
            )
        ]
        
        self.filter_rules.extend(default_rules)
    
    def add_rule(self, rule: FilterRule):
        """添加过滤规则"""
        self.filter_rules.append(rule)
        logger.info(f"添加过滤规则: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除过滤规则"""
        for i, rule in enumerate(self.filter_rules):
            if rule.name == rule_name:
                del self.filter_rules[i]
                logger.info(f"移除过滤规则: {rule_name}")
                return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """启用过滤规则"""
        for rule in self.filter_rules:
            if rule.name == rule_name:
                rule.enabled = True
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """禁用过滤规则"""
        for rule in self.filter_rules:
            if rule.name == rule_name:
                rule.enabled = False
                return True
        return False
    
    def should_include(self, transaction: Dict) -> bool:
        """判断是否应该包含此事务"""
        self.stats.total_requests += 1
        
        # 检查是否为静态资源
        if self._is_static_resource(transaction):
            self.stats.static_resources += 1
            return False
        
        # 检查是否为API请求
        if self._is_api_request(transaction):
            self.stats.api_requests += 1
        
        # 检查是否为错误请求
        if self._is_error_request(transaction):
            self.stats.error_requests += 1
        
        # 应用过滤规则
        include_rules = [r for r in self.filter_rules if r.rule_type == "include" and r.enabled]
        exclude_rules = [r for r in self.filter_rules if r.rule_type == "exclude" and r.enabled]
        
        # 如果有包含规则，必须至少匹配一个
        if include_rules:
            include_match = any(self._match_rule(rule, transaction) for rule in include_rules)
            if not include_match:
                self.stats.filtered_requests += 1
                return False
        
        # 如果匹配任何排除规则，则排除
        if exclude_rules:
            exclude_match = any(self._match_rule(rule, transaction) for rule in exclude_rules)
            if exclude_match:
                self.stats.filtered_requests += 1
                return False
        
        return True
    
    def _match_rule(self, rule: FilterRule, transaction: Dict) -> bool:
        """检查事务是否匹配规则"""
        try:
            # 获取字段值
            field_value = self._get_field_value(rule.field, transaction)
            if field_value is None:
                return False
            
            # 执行匹配
            if rule.is_regex:
                return bool(re.search(rule.pattern, str(field_value), re.IGNORECASE))
            else:
                return str(field_value).lower() == rule.pattern.lower()
                
        except Exception as e:
            logger.debug(f"规则匹配失败: {rule.name} - {e}")
            return False
    
    def _get_field_value(self, field: str, transaction: Dict) -> Optional[str]:
        """获取字段值"""
        request = transaction.get('request', {})
        response = transaction.get('response', {})
        
        field_map = {
            'url': request.get('url'),
            'method': request.get('method'),
            'domain': urlparse(request.get('url', '')).netloc,
            'path': urlparse(request.get('url', '')).path,
            'status_code': str(response.get('status_code', response.get('status', ''))),
            'content_type': response.get('content_type', ''),
            'mime_type': response.get('mime_type', '')
        }
        
        return field_map.get(field)
    
    def _is_static_resource(self, transaction: Dict) -> bool:
        """判断是否为静态资源"""
        url = transaction.get('request', {}).get('url', '')
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # 检查文件扩展名
        for ext in self.static_extensions:
            if path.endswith(ext):
                return True
        
        # 检查常见静态资源路径
        static_paths = ['/static/', '/assets/', '/public/', '/dist/', '/build/']
        return any(static_path in path for static_path in static_paths)
    
    def _is_api_request(self, transaction: Dict) -> bool:
        """判断是否为API请求"""
        url = transaction.get('request', {}).get('url', '')
        content_type = transaction.get('response', {}).get('content_type', '')
        
        # 检查URL模式
        api_patterns = [r'/api/', r'/rest/', r'/v\d+/', r'/graphql', r'\.json$']
        for pattern in api_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # 检查响应类型
        return 'application/json' in content_type.lower()
    
    def _is_error_request(self, transaction: Dict) -> bool:
        """判断是否为错误请求"""
        status_code = transaction.get('response', {}).get('status_code', 
                                                         transaction.get('response', {}).get('status', 0))
        return status_code >= 400 or 'error' in transaction
    
    def is_duplicate(self, transaction: Dict) -> bool:
        """检查是否为重复请求"""
        # 生成请求指纹
        fingerprint = self._generate_fingerprint(transaction)
        
        if fingerprint in self.seen_requests:
            self.stats.duplicate_requests += 1
            return True
        
        self.seen_requests.add(fingerprint)
        return False
    
    def _generate_fingerprint(self, transaction: Dict) -> str:
        """生成请求指纹用于去重"""
        request = transaction.get('request', {})
        
        # 基本信息
        method = request.get('method', '')
        url = request.get('url', '')
        
        # 标准化URL（移除时间戳等动态参数）
        normalized_url = self._normalize_url_for_dedup(url)
        
        # 请求体（如果有）
        body = request.get('body_data', {})
        body_str = ''
        if body and isinstance(body, dict) and '_raw_data' not in body:
            body_str = str(sorted(body.items()))
        
        # 生成MD5哈希
        fingerprint_data = f"{method}:{normalized_url}:{body_str}"
        return hashlib.md5(fingerprint_data.encode('utf-8')).hexdigest()
    
    def _normalize_url_for_dedup(self, url: str) -> str:
        """标准化URL用于去重"""
        parsed = urlparse(url)
        
        # 移除常见的动态参数
        dynamic_params = ['timestamp', 'ts', '_t', 'cache', 'v', 'version', 'cb', 'callback']
        
        query_parts = []
        if parsed.query:
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key.lower() not in dynamic_params:
                        query_parts.append(param)
                else:
                    query_parts.append(param)
        
        # 重构URL
        normalized_query = '&'.join(sorted(query_parts))
        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized_query:
            normalized_url += f"?{normalized_query}"
        
        return normalized_url
    
    def filter_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """批量过滤事务"""
        filtered = []
        
        for transaction in transactions:
            # 检查是否应该包含
            if not self.should_include(transaction):
                continue
            
            # 检查是否重复
            if self.is_duplicate(transaction):
                continue
            
            filtered.append(transaction)
        
        logger.info(f"过滤完成: {len(transactions)} -> {len(filtered)}")
        return filtered
    
    def get_stats(self) -> FilterStats:
        """获取过滤统计信息"""
        return self.stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = FilterStats()
    
    def clear_seen_requests(self):
        """清空已见请求记录"""
        self.seen_requests.clear()
    
    def get_rules(self) -> List[FilterRule]:
        """获取所有过滤规则"""
        return self.filter_rules.copy()
    
    def export_rules(self) -> List[Dict]:
        """导出过滤规则为字典格式"""
        return [{
            'name': rule.name,
            'rule_type': rule.rule_type,
            'field': rule.field,
            'pattern': rule.pattern,
            'is_regex': rule.is_regex,
            'enabled': rule.enabled
        } for rule in self.filter_rules]
    
    def import_rules(self, rules_data: List[Dict]):
        """从字典格式导入过滤规则"""
        for rule_data in rules_data:
            rule = FilterRule(**rule_data)
            self.add_rule(rule)

class AdvancedFilter(DataFilter):
    """高级过滤器，支持自定义过滤函数"""
    
    def __init__(self):
        super().__init__()
        self.custom_filters: List[Callable[[Dict], bool]] = []
    
    def add_custom_filter(self, filter_func: Callable[[Dict], bool], name: str = None):
        """添加自定义过滤函数"""
        filter_func._filter_name = name or f"custom_filter_{len(self.custom_filters)}"
        self.custom_filters.append(filter_func)
        logger.info(f"添加自定义过滤器: {filter_func._filter_name}")
    
    def remove_custom_filter(self, name: str) -> bool:
        """移除自定义过滤函数"""
        for i, filter_func in enumerate(self.custom_filters):
            if getattr(filter_func, '_filter_name', '') == name:
                del self.custom_filters[i]
                logger.info(f"移除自定义过滤器: {name}")
                return True
        return False
    
    def should_include(self, transaction: Dict) -> bool:
        """判断是否应该包含此事务（包含自定义过滤器）"""
        # 先执行基础过滤
        if not super().should_include(transaction):
            return False
        
        # 执行自定义过滤器
        for filter_func in self.custom_filters:
            try:
                if not filter_func(transaction):
                    self.stats.filtered_requests += 1
                    return False
            except Exception as e:
                logger.error(f"自定义过滤器执行失败: {getattr(filter_func, '_filter_name', 'unknown')} - {e}")
        
        return True

# 示例使用
if __name__ == "__main__":
    # 创建过滤器
    data_filter = DataFilter()
    
    # 示例事务数据
    sample_transactions = [
        {
            'request': {
                'url': 'https://api.example.com/v1/users',
                'method': 'GET'
            },
            'response': {
                'status': 200,
                'content_type': 'application/json'
            }
        },
        {
            'request': {
                'url': 'https://example.com/static/style.css',
                'method': 'GET'
            },
            'response': {
                'status': 200,
                'content_type': 'text/css'
            }
        }
    ]
    
    # 过滤事务
    filtered = data_filter.filter_transactions(sample_transactions)
    
    print(f"原始事务数: {len(sample_transactions)}")
    print(f"过滤后事务数: {len(filtered)}")
    print(f"过滤统计: {data_filter.get_stats()}")