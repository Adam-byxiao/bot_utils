#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library - 基础使用示例
演示如何使用通用Chrome DevTools库的基本功能
"""

import asyncio
import logging
from chrome_devtools_lib import ChromeDevToolsClient
from chrome_devtools_lib.domains import RuntimeDomain, NetworkDomain

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def basic_runtime_example():
    """基础Runtime域使用示例"""
    print("=== 基础Runtime域使用示例 ===")
    
    # 创建客户端
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    
    try:
        # 连接到Chrome
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用Runtime域
            await runtime.enable()
            print("✓ Runtime域已启用")
            
            # 执行简单的JavaScript
            result = await runtime.evaluate("2 + 3")
            if result["success"]:
                print(f"✓ JavaScript执行结果: {result['result']['value']}")
            
            # 获取页面标题
            result = await runtime.evaluate("document.title")
            if result["success"]:
                print(f"✓ 页面标题: {result['result']['value']}")
            
            # 获取当前URL
            result = await runtime.evaluate("window.location.href")
            if result["success"]:
                print(f"✓ 当前URL: {result['result']['value']}")
            
            # 执行复杂的JavaScript
            complex_script = """
            (function() {
                const info = {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    cookieEnabled: navigator.cookieEnabled,
                    onlineStatus: navigator.onLine,
                    screenResolution: screen.width + 'x' + screen.height,
                    timestamp: new Date().toISOString()
                };
                return info;
            })()
            """
            
            result = await runtime.evaluate(complex_script)
            if result["success"]:
                print("✓ 浏览器信息:")
                browser_info = result['result']['value']
                for key, value in browser_info.items():
                    print(f"  {key}: {value}")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def network_monitoring_example():
    """网络监控示例"""
    print("\n=== 网络监控示例 ===")
    
    client = ChromeDevToolsClient()
    network = NetworkDomain(client)
    
    # 请求计数器
    request_count = 0
    response_count = 0
    
    async def request_handler(params):
        nonlocal request_count
        request_count += 1
        request = params.get('request', {})
        print(f"📤 请求 #{request_count}: {request.get('method', 'GET')} {request.get('url', 'Unknown')}")
    
    async def response_handler(params):
        nonlocal response_count
        response_count += 1
        response = params.get('response', {})
        print(f"📥 响应 #{response_count}: {response.get('status', 'Unknown')} {response.get('url', 'Unknown')}")
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用网络监控
            await network.enable()
            print("✓ Network域已启用")
            
            # 添加事件处理器
            network.add_request_handler(request_handler)
            network.add_response_handler(response_handler)
            print("✓ 网络事件处理器已添加")
            
            # 监控10秒
            print("🔍 开始监控网络活动（10秒）...")
            await asyncio.sleep(10)
            
            print(f"📊 监控结果: 共捕获 {request_count} 个请求和 {response_count} 个响应")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"网络监控示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def multi_domain_example():
    """多域协同使用示例"""
    print("\n=== 多域协同使用示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    network = NetworkDomain(client)
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            
            # 启用多个域
            await runtime.enable()
            await network.enable()
            print("✓ Runtime和Network域已启用")
            
            # 禁用缓存
            await network.set_cache_disabled(True)
            print("✓ 已禁用缓存")
            
            # 执行页面刷新
            await runtime.evaluate("window.location.reload()")
            print("✓ 页面刷新已触发")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 获取页面性能信息
            perf_script = """
            (function() {
                const perf = performance.getEntriesByType('navigation')[0];
                if (perf) {
                    return {
                        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                        loadComplete: perf.loadEventEnd - perf.loadEventStart,
                        totalTime: perf.loadEventEnd - perf.fetchStart
                    };
                }
                return null;
            })()
            """
            
            result = await runtime.evaluate(perf_script)
            if result["success"] and result['result']['value']:
                print("📊 页面性能指标:")
                perf_data = result['result']['value']
                for key, value in perf_data.items():
                    print(f"  {key}: {value:.2f}ms")
            
            # 恢复缓存
            await network.set_cache_disabled(False)
            print("✓ 已恢复缓存")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"多域示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    
    try:
        if await client.connect():
            print("✓ 成功连接到Chrome DevTools")
            await runtime.enable()
            
            # 执行会产生错误的JavaScript
            print("🧪 测试JavaScript语法错误...")
            result = await runtime.evaluate("invalid javascript syntax")
            if not result["success"]:
                print(f"✓ 正确捕获语法错误: {result.get('error', 'Unknown error')}")
            
            # 执行会抛出异常的JavaScript
            print("🧪 测试JavaScript运行时异常...")
            result = await runtime.evaluate("throw new Error('测试异常')")
            if not result["success"]:
                print(f"✓ 正确捕获运行时异常: {result.get('exception', {}).get('description', 'Unknown exception')}")
            
            # 执行访问不存在对象的JavaScript
            print("🧪 测试访问不存在的对象...")
            result = await runtime.evaluate("nonExistentObject.someProperty")
            if not result["success"]:
                print(f"✓ 正确捕获引用错误: {result.get('exception', {}).get('description', 'Unknown exception')}")
        
        else:
            print("✗ 连接Chrome DevTools失败")
            
    except Exception as e:
        logger.error(f"错误处理示例失败: {e}")
    
    finally:
        await client.disconnect()
        print("✓ 已断开连接")

async def main():
    """主函数，运行所有示例"""
    print("Chrome DevTools Library - 基础使用示例")
    print("=" * 50)
    
    # 运行各个示例
    await basic_runtime_example()
    await network_monitoring_example()
    await multi_domain_example()
    await error_handling_example()
    
    print("\n" + "=" * 50)
    print("所有示例执行完成！")

if __name__ == "__main__":
    asyncio.run(main())