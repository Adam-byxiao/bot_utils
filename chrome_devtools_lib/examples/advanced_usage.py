#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library - 高级使用示例
演示库的高级功能，包括性能监控、存储管理、事件处理等
"""

import asyncio
import logging
import json
from chrome_devtools_lib import ChromeDevToolsClient
from chrome_devtools_lib.domains import RuntimeDomain, NetworkDomain, PerformanceDomain, StorageDomain

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def performance_monitoring_example():
    """性能监控示例"""
    print("=== 性能监控示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    performance = PerformanceDomain(client)
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用域
            await runtime.enable()
            await performance.enable()
            print("✓ Runtime和Performance域已启用")
            
            # 获取初始性能指标
            initial_metrics = await performance.get_metrics()
            if initial_metrics.get("success"):
                print("📊 初始性能指标:")
                for metric in initial_metrics["result"]["metrics"]:
                    print(f"  {metric['name']}: {metric['value']}")
            
            # 执行一些操作来产生性能数据
            print("🔄 执行性能测试操作...")
            
            # 刷新页面
            await runtime.evaluate("window.location.reload()")
            await asyncio.sleep(3)
            
            # 执行一些计算密集型操作
            compute_script = """
            (function() {
                const start = performance.now();
                let result = 0;
                for (let i = 0; i < 1000000; i++) {
                    result += Math.sqrt(i);
                }
                const end = performance.now();
                return {
                    result: result,
                    duration: end - start,
                    timestamp: new Date().toISOString()
                };
            })()
            """
            
            compute_result = await runtime.evaluate(compute_script)
            if compute_result.get("success"):
                data = compute_result["result"]["value"]
                print(f"✓ 计算操作完成，耗时: {data['duration']:.2f}ms")
            
            # 获取更新后的性能指标
            updated_metrics = await performance.get_metrics()
            if updated_metrics.get("success"):
                print("📊 更新后的性能指标:")
                for metric in updated_metrics["result"]["metrics"]:
                    print(f"  {metric['name']}: {metric['value']}")
            
            # 强制垃圾回收
            gc_result = await performance.collect_garbage()
            if gc_result.get("success"):
                print("✓ 垃圾回收已执行")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"性能监控示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def storage_management_example():
    """存储管理示例"""
    print("\n=== 存储管理示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    storage = StorageDomain(client)
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用域
            await runtime.enable()
            print("✓ Runtime域已启用")
            
            # 获取当前页面的origin
            origin_result = await runtime.evaluate("window.location.origin")
            if origin_result.get("success"):
                origin = origin_result["result"]["value"]
                print(f"📍 当前页面origin: {origin}")
                
                # 获取存储使用情况
                usage_result = await storage.get_usage_and_quota(origin)
                if usage_result.get("success"):
                    usage_data = usage_result["result"]
                    print("💾 存储使用情况:")
                    print(f"  已使用: {usage_data.get('usage', 0)} 字节")
                    print(f"  配额: {usage_data.get('quota', 0)} 字节")
                    print(f"  使用率: {(usage_data.get('usage', 0) / max(usage_data.get('quota', 1), 1) * 100):.2f}%")
            
            # 获取所有Cookie
            cookies_result = await storage.get_cookies()
            if cookies_result.get("success"):
                cookies = cookies_result["result"]["cookies"]
                print(f"🍪 当前Cookie数量: {len(cookies)}")
                
                # 显示前5个Cookie
                for i, cookie in enumerate(cookies[:5], 1):
                    print(f"  {i}. {cookie['name']}: {cookie['value'][:50]}...")
            
            # 设置测试Cookie
            test_cookies = [
                {
                    "name": "test_cookie_1",
                    "value": "test_value_1",
                    "domain": ".example.com",
                    "path": "/",
                    "secure": False,
                    "httpOnly": False
                },
                {
                    "name": "test_cookie_2", 
                    "value": "test_value_2",
                    "domain": ".example.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True
                }
            ]
            
            set_result = await storage.set_cookies(test_cookies)
            if set_result.get("success"):
                print("✓ 测试Cookie已设置")
            
            # 测试localStorage操作
            print("🗄️  测试localStorage操作...")
            
            # 设置localStorage数据
            localStorage_script = """
            (function() {
                try {
                    localStorage.setItem('test_key_1', 'test_value_1');
                    localStorage.setItem('test_key_2', JSON.stringify({data: 'complex_value', timestamp: Date.now()}));
                    return {
                        success: true,
                        count: localStorage.length
                    };
                } catch (e) {
                    return {
                        success: false,
                        error: e.message
                    };
                }
            })()
            """
            
            localStorage_result = await runtime.evaluate(localStorage_script)
            if localStorage_result.get("success"):
                data = localStorage_result["result"]["value"]
                if data["success"]:
                    print(f"✓ localStorage数据已设置，当前项目数: {data['count']}")
                else:
                    print(f"✗ localStorage操作失败: {data['error']}")
            
            # 清除测试数据
            print("🧹 清除测试数据...")
            
            # 清除localStorage
            clear_localStorage_script = """
            (function() {
                try {
                    localStorage.removeItem('test_key_1');
                    localStorage.removeItem('test_key_2');
                    return {success: true, remaining: localStorage.length};
                } catch (e) {
                    return {success: false, error: e.message};
                }
            })()
            """
            
            clear_result = await runtime.evaluate(clear_localStorage_script)
            if clear_result.get("success"):
                data = clear_result["result"]["value"]
                if data["success"]:
                    print(f"✓ localStorage测试数据已清除，剩余项目数: {data['remaining']}")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"存储管理示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def event_handling_example():
    """事件处理示例"""
    print("\n=== 事件处理示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    network = NetworkDomain(client)
    
    # 事件计数器
    events_count = {
        "console_api": 0,
        "exception": 0,
        "request": 0,
        "response": 0
    }
    
    # 事件处理器
    async def console_handler(params):
        events_count["console_api"] += 1
        console_type = params.get("type", "log")
        args = params.get("args", [])
        if args:
            value = args[0].get("value", "")
            print(f"🖥️  Console.{console_type}: {value}")
    
    async def exception_handler(params):
        events_count["exception"] += 1
        exception_details = params.get("exceptionDetails", {})
        text = exception_details.get("text", "Unknown exception")
        print(f"❌ Exception: {text}")
    
    async def request_handler(params):
        events_count["request"] += 1
        request = params.get("request", {})
        method = request.get("method", "GET")
        url = request.get("url", "Unknown")
        print(f"📤 Request: {method} {url[:80]}...")
    
    async def response_handler(params):
        events_count["response"] += 1
        response = params.get("response", {})
        status = response.get("status", "Unknown")
        url = response.get("url", "Unknown")
        print(f"📥 Response: {status} {url[:80]}...")
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用域
            await runtime.enable()
            await network.enable()
            print("✓ Runtime和Network域已启用")
            
            # 添加事件监听器
            runtime.add_console_handler(console_handler)
            runtime.add_exception_handler(exception_handler)
            network.add_request_handler(request_handler)
            network.add_response_handler(response_handler)
            print("✓ 事件监听器已添加")
            
            # 触发一些事件
            print("🎯 触发测试事件...")
            
            # 触发console事件
            await runtime.evaluate("console.log('这是一个测试日志消息')")
            await runtime.evaluate("console.warn('这是一个警告消息')")
            await runtime.evaluate("console.error('这是一个错误消息')")
            
            # 触发异常事件
            await runtime.evaluate("throw new Error('这是一个测试异常')")
            
            # 触发网络事件（如果页面有网络请求）
            await runtime.evaluate("""
            (function() {
                // 创建一个简单的fetch请求
                fetch('/api/test').catch(() => {});
                
                // 创建一个图片请求
                const img = new Image();
                img.src = '/test-image.png';
                
                // 创建一个XMLHttpRequest
                const xhr = new XMLHttpRequest();
                xhr.open('GET', '/test-endpoint');
                xhr.send();
            })()
            """)
            
            # 等待事件处理
            print("⏱️  等待事件处理（5秒）...")
            await asyncio.sleep(5)
            
            # 显示事件统计
            print("📊 事件统计:")
            for event_type, count in events_count.items():
                print(f"  {event_type}: {count} 个事件")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"事件处理示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def batch_operations_example():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            await runtime.enable()
            
            # 批量执行JavaScript
            scripts = [
                "document.title",
                "window.location.href",
                "navigator.userAgent",
                "screen.width + 'x' + screen.height",
                "new Date().toISOString()",
                "document.documentElement.scrollHeight",
                "window.innerWidth + 'x' + window.innerHeight",
                "document.readyState",
                "document.cookie.length",
                "localStorage.length"
            ]
            
            print("🔄 执行批量JavaScript操作...")
            results = []
            
            # 并发执行多个脚本
            tasks = [runtime.evaluate(script) for script in scripts]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, (script, result) in enumerate(zip(scripts, batch_results), 1):
                if isinstance(result, Exception):
                    print(f"  {i}. {script}: ❌ 异常 - {result}")
                elif result.get("success"):
                    value = result["result"]["value"]
                    print(f"  {i}. {script}: ✓ {value}")
                else:
                    error = result.get("error", "Unknown error")
                    print(f"  {i}. {script}: ❌ 错误 - {error}")
            
            # 批量DOM操作
            print("\n🔄 执行批量DOM操作...")
            
            dom_operations = [
                "document.querySelectorAll('*').length",
                "document.querySelectorAll('div').length", 
                "document.querySelectorAll('img').length",
                "document.querySelectorAll('a').length",
                "document.querySelectorAll('script').length",
                "document.querySelectorAll('link').length"
            ]
            
            dom_tasks = [runtime.evaluate(op) for op in dom_operations]
            dom_results = await asyncio.gather(*dom_tasks, return_exceptions=True)
            
            print("📊 DOM元素统计:")
            element_types = ["所有元素", "DIV元素", "IMG元素", "A元素", "SCRIPT元素", "LINK元素"]
            
            for element_type, result in zip(element_types, dom_results):
                if isinstance(result, Exception):
                    print(f"  {element_type}: ❌ 异常")
                elif result.get("success"):
                    count = result["result"]["value"]
                    print(f"  {element_type}: {count} 个")
                else:
                    print(f"  {element_type}: ❌ 错误")
            
            # 性能测试
            print("\n⚡ 执行性能测试...")
            
            perf_script = """
            (function() {
                const results = [];
                const iterations = 1000;
                
                // 测试1: 数组操作
                let start = performance.now();
                const arr = [];
                for (let i = 0; i < iterations; i++) {
                    arr.push(i);
                }
                results.push({
                    test: 'Array Push',
                    duration: performance.now() - start,
                    operations: iterations
                });
                
                // 测试2: DOM查询
                start = performance.now();
                for (let i = 0; i < 100; i++) {
                    document.querySelectorAll('*');
                }
                results.push({
                    test: 'DOM Query',
                    duration: performance.now() - start,
                    operations: 100
                });
                
                // 测试3: 数学计算
                start = performance.now();
                let sum = 0;
                for (let i = 0; i < iterations; i++) {
                    sum += Math.sqrt(i);
                }
                results.push({
                    test: 'Math Calculation',
                    duration: performance.now() - start,
                    operations: iterations
                });
                
                return results;
            })()
            """
            
            perf_result = await runtime.evaluate(perf_script)
            if perf_result.get("success"):
                perf_data = perf_result["result"]["value"]
                for test in perf_data:
                    ops_per_sec = test["operations"] / (test["duration"] / 1000)
                    print(f"  {test['test']}: {test['duration']:.2f}ms ({ops_per_sec:.0f} ops/sec)")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"批量操作示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def main():
    """主函数，运行所有高级示例"""
    print("Chrome DevTools Library - 高级使用示例")
    print("=" * 60)
    print("💡 确保Chrome浏览器已启动并开启了DevTools调试端口")
    print("💡 建议在有内容的网页上运行这些示例以获得更好的效果")
    print("=" * 60)
    
    # 运行各个示例
    await performance_monitoring_example()
    await storage_management_example()
    await event_handling_example()
    await batch_operations_example()
    
    print("\n" + "=" * 60)
    print("所有高级示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())