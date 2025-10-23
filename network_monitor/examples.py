#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络监控器使用示例
演示各种使用场景和功能
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

# 导入网络监控模块
from main import NetworkMonitor, get_default_config
from chrome_network_listener import ChromeNetworkListener
from data_filter import DataFilter, FilterRule
from data_exporter import DataExporter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def example_basic_monitoring():
    """
    示例1: 基本网络监控
    监控所有网络请求30秒
    """
    print("\n=== 示例1: 基本网络监控 ===")
    
    config = get_default_config()
    config['session_id'] = 'basic_example'
    config['export']['formats'] = ['json', 'txt']
    
    monitor = NetworkMonitor(config)
    
    try:
        print("开始基本监控，持续30秒...")
        await monitor.start_monitoring(duration=30)
        print("基本监控完成！")
    except Exception as e:
        print(f"监控失败: {e}")

async def example_api_only_monitoring():
    """
    示例2: 仅监控API请求
    只捕获包含'/api/'的请求
    """
    print("\n=== 示例2: API请求监控 ===")
    
    config = get_default_config()
    config['session_id'] = 'api_example'
    config['filters']['api_only'] = True
    config['filters']['exclude_static_resources'] = True
    config['export']['formats'] = ['json', 'csv']
    
    monitor = NetworkMonitor(config)
    
    try:
        print("开始API监控，持续45秒...")
        print("请在浏览器中访问包含API调用的页面")
        await monitor.start_monitoring(duration=45)
        print("API监控完成！")
    except Exception as e:
        print(f"监控失败: {e}")

async def example_domain_specific_monitoring():
    """
    示例3: 特定域名监控
    只监控指定域名的请求
    """
    print("\n=== 示例3: 特定域名监控 ===")
    
    config = get_default_config()
    config['session_id'] = 'domain_example'
    config['filters']['include_domains'] = [
        'api.github.com',
        'httpbin.org',
        'jsonplaceholder.typicode.com'
    ]
    config['export']['formats'] = ['excel']
    
    monitor = NetworkMonitor(config)
    
    try:
        print("开始域名监控，持续60秒...")
        print("请访问 GitHub、HTTPBin 或 JSONPlaceholder 等网站")
        await monitor.start_monitoring(duration=60)
        print("域名监控完成！")
    except Exception as e:
        print(f"监控失败: {e}")

async def example_error_monitoring():
    """
    示例4: 错误请求监控
    专门监控失败的请求
    """
    print("\n=== 示例4: 错误请求监控 ===")
    
    config = get_default_config()
    config['session_id'] = 'error_example'
    config['filters']['exclude_static_resources'] = True
    config['filters']['exclude_status_codes'] = []  # 不排除任何状态码
    config['export']['formats'] = ['json', 'txt']
    
    monitor = NetworkMonitor(config)
    
    try:
        print("开始错误监控，持续30秒...")
        print("请尝试访问一些不存在的页面或API端点")
        await monitor.start_monitoring(duration=30)
        print("错误监控完成！")
    except Exception as e:
        print(f"监控失败: {e}")

async def example_custom_listener():
    """
    示例5: 自定义监听器
    直接使用监听器进行自定义处理
    """
    print("\n=== 示例5: 自定义监听器 ===")
    
    listener = ChromeNetworkListener()
    request_count = 0
    response_count = 0
    
    async def on_request(request_data):
        nonlocal request_count
        request_count += 1
        url = request_data.get('request', {}).get('url', 'Unknown')
        method = request_data.get('request', {}).get('method', 'Unknown')
        print(f"[请求 #{request_count}] {method} {url}")
    
    async def on_response(response_data):
        nonlocal response_count
        response_count += 1
        status = response_data.get('response', {}).get('status', 'Unknown')
        print(f"[响应 #{response_count}] 状态码: {status}")
    
    listener.on_request_sent = on_request
    listener.on_response_received = on_response
    
    try:
        print("开始自定义监听，持续20秒...")
        await listener.connect()
        await listener.start_listening()
        
        # 等待20秒
        await asyncio.sleep(20)
        
        await listener.stop_listening()
        await listener.disconnect()
        
        print(f"自定义监听完成！共捕获 {request_count} 个请求，{response_count} 个响应")
        
    except Exception as e:
        print(f"自定义监听失败: {e}")

def example_data_filter():
    """
    示例6: 数据过滤器使用
    演示如何使用过滤器
    """
    print("\n=== 示例6: 数据过滤器 ===")
    
    # 创建过滤器
    filter_engine = DataFilter()
    
    # 添加各种过滤规则
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
    
    filter_engine.add_rule(FilterRule(
        name='success_only',
        rule_type='include',
        pattern=r'^2\d\d$',
        field='status_code'
    ))
    
    # 示例数据
    sample_transactions = [
        {
            'request': {'url': 'https://api.example.com/users'},
            'response': {'status_code': 200}
        },
        {
            'request': {'url': 'https://example.com/image.png'},
            'response': {'status_code': 200}
        },
        {
            'request': {'url': 'https://api.example.com/posts'},
            'response': {'status_code': 404}
        }
    ]
    
    print(f"原始数据: {len(sample_transactions)} 条")
    
    # 应用过滤器
    filtered_transactions = []
    for transaction in sample_transactions:
        if filter_engine.should_include(transaction):
            filtered_transactions.append(transaction)
    
    print(f"过滤后数据: {len(filtered_transactions)} 条")
    
    # 显示过滤统计
    stats = filter_engine.get_stats()
    print(f"过滤统计: {stats}")

def example_data_export():
    """
    示例7: 数据导出
    演示各种导出格式
    """
    print("\n=== 示例7: 数据导出 ===")
    
    # 创建导出器
    exporter = DataExporter('./examples_output')
    
    # 示例数据
    sample_data = [
        {
            'transaction_id': 'tx-001',
            'session_id': 'example-session',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': 150.5,
            'success': True,
            'request': {
                'method': 'GET',
                'url': 'https://api.example.com/users',
                'domain': 'api.example.com',
                'path': '/users',
                'is_api': True
            },
            'response': {
                'status_code': 200,
                'status_category': 'success',
                'content_type': 'application/json'
            },
            'tags': ['api', 'success']
        },
        {
            'transaction_id': 'tx-002',
            'session_id': 'example-session',
            'timestamp': datetime.now().isoformat(),
            'duration_ms': 89.2,
            'success': True,
            'request': {
                'method': 'POST',
                'url': 'https://api.example.com/posts',
                'domain': 'api.example.com',
                'path': '/posts',
                'is_api': True
            },
            'response': {
                'status_code': 201,
                'status_category': 'success',
                'content_type': 'application/json'
            },
            'tags': ['api', 'success', 'create']
        }
    ]
    
    print(f"准备导出 {len(sample_data)} 条示例数据...")
    
    # 导出为不同格式
    formats = exporter.get_supported_formats()
    print(f"支持的格式: {formats}")
    
    exported_files = []
    for format_type in formats:
        try:
            filepath = exporter.export_transactions(sample_data, format_type, 'example_data')
            exported_files.append(filepath)
            print(f"✓ {format_type.upper()} 导出完成: {filepath}")
        except Exception as e:
            print(f"✗ {format_type.upper()} 导出失败: {e}")
    
    # 导出摘要报告
    try:
        summary_file = exporter.export_summary_report(sample_data, 'example_summary')
        exported_files.append(summary_file)
        print(f"✓ 摘要报告导出完成: {summary_file}")
    except Exception as e:
        print(f"✗ 摘要报告导出失败: {e}")
    
    print(f"\n总共导出 {len(exported_files)} 个文件")

async def example_batch_monitoring():
    """
    示例8: 批量监控
    连续进行多个监控会话
    """
    print("\n=== 示例8: 批量监控 ===")
    
    sessions = [
        {'name': 'session_1', 'duration': 15, 'api_only': True},
        {'name': 'session_2', 'duration': 15, 'exclude_errors': True},
        {'name': 'session_3', 'duration': 15, 'all_requests': True}
    ]
    
    for i, session_config in enumerate(sessions, 1):
        print(f"\n开始第 {i} 个监控会话: {session_config['name']}")
        
        config = get_default_config()
        config['session_id'] = session_config['name']
        config['output_dir'] = f'./batch_output/{session_config["name"]}'
        
        # 根据会话配置调整过滤器
        if session_config.get('api_only'):
            config['filters']['api_only'] = True
        elif session_config.get('exclude_errors'):
            config['filters']['exclude_status_codes'] = [400, 401, 403, 404, 500, 502, 503]
        elif session_config.get('all_requests'):
            config['filters']['exclude_static_resources'] = False
        
        monitor = NetworkMonitor(config)
        
        try:
            await monitor.start_monitoring(duration=session_config['duration'])
            print(f"✓ 会话 {session_config['name']} 完成")
        except Exception as e:
            print(f"✗ 会话 {session_config['name']} 失败: {e}")
        
        # 会话间隔
        if i < len(sessions):
            print("等待5秒后开始下一个会话...")
            await asyncio.sleep(5)
    
    print("\n批量监控完成！")

def create_custom_config_examples():
    """
    示例9: 创建自定义配置文件
    生成不同场景的配置文件
    """
    print("\n=== 示例9: 自定义配置文件 ===")
    
    configs = {
        'api_monitoring.json': {
            'chrome_host': 'localhost',
            'chrome_port': 9222,
            'session_id': 'api_monitoring',
            'output_dir': './api_output',
            'filters': {
                'exclude_static_resources': True,
                'api_only': True,
                'exclude_status_codes': [404, 500],
                'include_domains': []
            },
            'export': {
                'formats': ['json', 'excel'],
                'include_summary': True
            }
        },
        'performance_monitoring.json': {
            'chrome_host': 'localhost',
            'chrome_port': 9222,
            'session_id': 'performance_monitoring',
            'output_dir': './performance_output',
            'filters': {
                'exclude_static_resources': False,
                'api_only': False,
                'exclude_status_codes': [],
                'include_domains': []
            },
            'export': {
                'formats': ['excel', 'csv'],
                'include_summary': True
            }
        },
        'error_monitoring.json': {
            'chrome_host': 'localhost',
            'chrome_port': 9222,
            'session_id': 'error_monitoring',
            'output_dir': './error_output',
            'filters': {
                'exclude_static_resources': True,
                'api_only': False,
                'exclude_status_codes': [200, 201, 202, 204],  # 只保留错误状态码
                'include_domains': []
            },
            'export': {
                'formats': ['json', 'txt'],
                'include_summary': True
            }
        }
    }
    
    # 创建配置文件目录
    config_dir = Path('./example_configs')
    config_dir.mkdir(exist_ok=True)
    
    for filename, config in configs.items():
        filepath = config_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✓ 创建配置文件: {filepath}")
    
    print(f"\n配置文件创建完成！可以使用以下命令运行:")
    for filename in configs.keys():
        print(f"  python main.py -c example_configs/{filename}")

async def run_all_examples():
    """
    运行所有示例
    """
    print("Chrome DevTools Network Monitor - 使用示例")
    print("=" * 50)
    
    # 检查Chrome连接
    try:
        listener = ChromeNetworkListener()
        await listener.connect()
        await listener.disconnect()
        print("✓ Chrome连接测试成功")
    except Exception as e:
        print(f"✗ Chrome连接失败: {e}")
        print("请确保Chrome已启动调试模式：")
        print("chrome.exe --remote-debugging-port=9222 --disable-web-security")
        return
    
    # 运行示例
    examples = [
        ("数据过滤器", example_data_filter),
        ("数据导出", example_data_export),
        ("自定义配置文件", create_custom_config_examples),
        ("基本网络监控", example_basic_monitoring),
        ("API请求监控", example_api_only_monitoring),
        ("自定义监听器", example_custom_listener),
    ]
    
    for name, example_func in examples:
        try:
            print(f"\n正在运行: {name}")
            if asyncio.iscoroutinefunction(example_func):
                await example_func()
            else:
                example_func()
            print(f"✓ {name} 完成")
        except Exception as e:
            print(f"✗ {name} 失败: {e}")
        
        # 示例间隔
        await asyncio.sleep(2)
    
    print("\n=== 所有示例运行完成 ===")
    print("查看生成的输出文件了解详细结果")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        
        examples_map = {
            'basic': example_basic_monitoring,
            'api': example_api_only_monitoring,
            'domain': example_domain_specific_monitoring,
            'error': example_error_monitoring,
            'custom': example_custom_listener,
            'filter': example_data_filter,
            'export': example_data_export,
            'batch': example_batch_monitoring,
            'config': create_custom_config_examples
        }
        
        if example_name in examples_map:
            example_func = examples_map[example_name]
            if asyncio.iscoroutinefunction(example_func):
                asyncio.run(example_func())
            else:
                example_func()
        else:
            print(f"未知示例: {example_name}")
            print(f"可用示例: {list(examples_map.keys())}")
    else:
        # 运行所有示例
        asyncio.run(run_all_examples())