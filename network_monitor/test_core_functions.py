#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Monitor 核心功能测试
测试不依赖 Chrome 连接的功能
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from data_filter import DataFilter, FilterRule
from data_exporter import DataExporter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_filter():
    """测试数据过滤器功能"""
    print("\n=== 测试数据过滤器 ===")
    
    # 创建过滤器
    filter_engine = DataFilter()
    
    # 添加过滤规则
    filter_engine.add_rule(FilterRule(
        name='api_only',
        rule_type='include',
        pattern=r'/api/',
        field='url'
    ))
    
    filter_engine.add_rule(FilterRule(
        name='exclude_images',
        rule_type='exclude',
        pattern=r'\.(png|jpg|jpeg|gif)$',
        field='url'
    ))
    
    # 测试数据
    test_data = [
        {
            'url': 'https://example.com/api/users',
            'method': 'GET',
            'status_code': 200,
            'timestamp': datetime.now().isoformat()
        },
        {
            'url': 'https://example.com/image.png',
            'method': 'GET',
            'status_code': 200,
            'timestamp': datetime.now().isoformat()
        },
        {
            'url': 'https://example.com/api/posts',
            'method': 'POST',
            'status_code': 201,
            'timestamp': datetime.now().isoformat()
        },
        {
            'url': 'https://example.com/home',
            'method': 'GET',
            'status_code': 200,
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    print(f"原始数据: {len(test_data)} 条")
    
    # 应用过滤器
    filtered_data = filter_engine.filter_transactions(test_data)
    
    print(f"过滤后数据: {len(filtered_data)} 条")
    print(f"过滤规则数量: {len(filter_engine.filter_rules)}")
    
    # 显示过滤后的数据
    for item in filtered_data:
        print(f"  - {item['method']} {item['url']} ({item['status_code']})")
    
    return filtered_data

def test_data_exporter():
    """测试数据导出器功能"""
    print("\n=== 测试数据导出器 ===")
    
    # 创建导出器
    exporter = DataExporter()
    
    # 测试数据 - 符合 DataExporter 期望的格式
    test_data = [
        {
            'transaction_id': 'test-1',
            'session_id': 'test-session',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': 150.0,
            'success': True,
            'request': {
                'method': 'GET',
                'url': 'https://example.com/api/users',
                'domain': 'example.com',
                'path': '/api/users',
                'endpoint': '/api/users',
                'is_api': True
            },
            'response': {
                'status_code': 200,
                'status_category': 'success',
                'content_type': 'application/json',
                'is_json': True
            },
            'tags': ['api', 'method:get', 'status:success']
        },
        {
            'transaction_id': 'test-2',
            'session_id': 'test-session',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': 200.0,
            'success': True,
            'request': {
                'method': 'POST',
                'url': 'https://example.com/api/posts',
                'domain': 'example.com',
                'path': '/api/posts',
                'endpoint': '/api/posts',
                'is_api': True
            },
            'response': {
                'status_code': 201,
                'status_category': 'success',
                'content_type': 'application/json',
                'is_json': True
            },
            'tags': ['api', 'method:post', 'status:success']
        }
    ]
    
    # 创建输出目录
    output_dir = Path('test_output')
    output_dir.mkdir(exist_ok=True)
    
    # 测试各种导出格式
    formats = ['json', 'csv', 'txt']
    
    for format_type in formats:
        try:
            filename = exporter.export_transactions(test_data, format_type, f'test_data.{format_type}')
            print(f"✓ {format_type.upper()} 导出成功: {filename}")
        except Exception as e:
            print(f"✗ {format_type.upper()} 导出失败: {e}")
    
    # 生成摘要报告
    try:
        summary_file = exporter.export_summary_report(test_data, 'test_summary.txt')
        print(f"✓ 摘要报告生成成功: {summary_file}")
    except Exception as e:
        print(f"✗ 摘要报告生成失败: {e}")

def test_filter_rules():
    """测试过滤规则的各种类型"""
    print("\n=== 测试过滤规则类型 ===")
    
    filter_engine = DataFilter()
    
    # 测试包含规则
    filter_engine.add_rule(FilterRule(
        name='include_api',
        rule_type='include',
        pattern=r'/api/',
        field='url'
    ))
    
    # 测试排除规则
    filter_engine.add_rule(FilterRule(
        name='exclude_static',
        rule_type='exclude',
        pattern=r'\.(css|js|png|jpg)$',
        field='url'
    ))
    
    # 测试状态码过滤
    filter_engine.add_rule(FilterRule(
        name='success_only',
        rule_type='include',
        pattern=r'^2\d\d$',
        field='status_code'
    ))
    
    test_data = [
        {'url': 'https://example.com/api/users', 'status_code': 200},
        {'url': 'https://example.com/style.css', 'status_code': 200},
        {'url': 'https://example.com/api/posts', 'status_code': 404},
        {'url': 'https://example.com/api/data', 'status_code': 201},
    ]
    
    print(f"测试数据: {len(test_data)} 条")
    for item in test_data:
        print(f"  - {item['url']} ({item['status_code']})")
    
    filtered = filter_engine.filter_transactions(test_data)
    
    print(f"\n过滤后数据: {len(filtered)} 条")
    for item in filtered:
        print(f"  - {item['url']} ({item['status_code']})")

def main():
    """运行所有测试"""
    print("Network Monitor 核心功能测试")
    print("=" * 50)
    
    try:
        # 测试数据过滤器
        filtered_data = test_data_filter()
        
        # 测试数据导出器
        test_data_exporter()
        
        # 测试过滤规则
        test_filter_rules()
        
        print("\n" + "=" * 50)
        print("✓ 所有核心功能测试完成！")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()