#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library - 简化 API 使用示例
演示 ChromeInterface 简化 API 的各种使用场景
"""

import asyncio
import logging
from chrome_devtools_lib.simplified_api import ChromeInterface

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def basic_simplified_example():
    """基础简化 API 使用示例"""
    print("=== 基础简化 API 使用示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 连接到 Chrome
        success = await chrome.connect()
        if not success:
            print("❌ 连接失败，请确保 Chrome 已启动并开启调试端口")
            return
        
        print("✓ 成功连接到 Chrome DevTools")
        
        # 启用必要的域
        await chrome.Runtime.enable()
        await chrome.Page.enable()
        print("✓ Runtime 和 Page 域已启用")
        
        # 执行 JavaScript
        result, messages = await chrome.Runtime.evaluate(expression="2 + 3")
        if result and 'result' in result:
            print(f"✓ JavaScript 执行结果: {result['result']['value']}")
        
        # 获取页面信息
        title_result, _ = await chrome.Runtime.evaluate(expression="document.title")
        url_result, _ = await chrome.Runtime.evaluate(expression="window.location.href")
        
        if title_result and 'result' in title_result:
            print(f"✓ 页面标题: {title_result['result']['value']}")
        if url_result and 'result' in url_result:
            print(f"✓ 当前 URL: {url_result['result']['value']}")
        
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
    finally:
        await chrome.disconnect()
        print("✓ 已断开连接")

async def navigation_example():
    """页面导航示例"""
    print("\n=== 页面导航示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Page.enable()
        await chrome.Runtime.enable()
        
        # 导航到指定页面
        print("🔄 导航到 example.com...")
        nav_result, _ = await chrome.Page.navigate(url="https://example.com")
        
        if nav_result:
            print("✓ 导航命令已发送")
            
            # 等待页面加载完成
            print("⏳ 等待页面加载完成...")
            event, all_messages = await chrome.wait_event("Page.loadEventFired", timeout=10)
            
            if event:
                print("✓ 页面加载完成!")
                print(f"📊 等待期间收到 {len(all_messages)} 条消息")
                
                # 获取加载后的页面信息
                title_result, _ = await chrome.Runtime.evaluate(expression="document.title")
                if title_result and 'result' in title_result:
                    print(f"✓ 新页面标题: {title_result['result']['value']}")
            else:
                print("⚠️ 页面加载超时")
        
    except Exception as e:
        print(f"❌ 导航过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def network_monitoring_example():
    """网络监控示例"""
    print("\n=== 网络监控示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        print("🌐 开始监控网络请求...")
        
        # 导航到页面以产生网络请求
        await chrome.Page.navigate(url="https://httpbin.org/json")
        
        # 监控网络请求（限时监控）
        request_count = 0
        start_time = asyncio.get_event_loop().time()
        timeout = 10  # 10秒超时
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            message = await chrome.wait_message(timeout=2)
            
            if message:
                method = message.get('method', '')
                
                if method == 'Network.requestWillBeSent':
                    request = message['params']['request']
                    print(f"📤 请求: {request['method']} {request['url']}")
                    request_count += 1
                
                elif method == 'Network.responseReceived':
                    response = message['params']['response']
                    print(f"📥 响应: {response['status']} {response['url']}")
                
                elif method == 'Page.loadEventFired':
                    print("✓ 页面加载完成")
                    break
            else:
                # 超时，检查是否还有未读消息
                unread = chrome.pop_messages()
                if not unread:
                    break
        
        print(f"📊 监控结束，共捕获 {request_count} 个请求")
        
        # 获取 cookies
        cookies_result, _ = await chrome.Network.getCookies()
        if cookies_result and 'cookies' in cookies_result:
            print(f"🍪 当前页面有 {len(cookies_result['cookies'])} 个 cookie")
        
    except Exception as e:
        print(f"❌ 网络监控过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def direct_target_connection_example():
    """直接目标连接示例"""
    print("\n=== 直接目标连接示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 首先获取所有标签页
        tabs = await chrome.get_tabs()
        
        if not tabs:
            print("❌ 没有找到可用的标签页")
            return
        
        print(f"📋 找到 {len(tabs)} 个标签页:")
        for i, tab in enumerate(tabs):
            print(f"  {i+1}. {tab.get('title', 'Unknown')} - {tab.get('url', 'Unknown')}")
        
        # 连接到第一个标签页
        target_id = tabs[0]['id']
        print(f"\n🎯 直接连接到标签页: {target_id}")
        
        success = await chrome.connect_target_id(target_id)
        if success:
            print("✓ 直接连接成功")
            
            # 启用域并执行操作
            await chrome.Runtime.enable()
            
            # 获取页面信息
            title_result, _ = await chrome.Runtime.evaluate(expression="document.title")
            url_result, _ = await chrome.Runtime.evaluate(expression="window.location.href")
            
            if title_result and 'result' in title_result:
                print(f"✓ 连接的页面标题: {title_result['result']['value']}")
            if url_result and 'result' in url_result:
                print(f"✓ 连接的页面 URL: {url_result['result']['value']}")
        else:
            print("❌ 直接连接失败")
        
    except Exception as e:
        print(f"❌ 直接连接过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def android_environment_example():
    """Android 环境示例"""
    print("\n=== Android 环境示例 ===")
    
    # Android 环境需要抑制 Origin 头部
    chrome = ChromeInterface(suppress_origin=True)
    
    try:
        print("📱 使用 Android 兼容模式连接...")
        success = await chrome.connect()
        
        if success:
            print("✓ Android 环境连接成功")
            
            await chrome.Runtime.enable()
            
            # 执行一些基本操作
            result, _ = await chrome.Runtime.evaluate(expression="navigator.userAgent")
            if result and 'result' in result:
                user_agent = result['result']['value']
                print(f"🔍 User Agent: {user_agent[:100]}...")
                
                # 检查是否为移动设备
                is_mobile_result, _ = await chrome.Runtime.evaluate(
                    expression="navigator.userAgent.includes('Mobile')"
                )
                if is_mobile_result and 'result' in is_mobile_result:
                    is_mobile = is_mobile_result['result']['value']
                    print(f"📱 是否为移动设备: {is_mobile}")
        else:
            print("❌ Android 环境连接失败")
    
    except Exception as e:
        print(f"❌ Android 环境测试中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def event_waiting_example():
    """事件等待示例"""
    print("\n=== 事件等待示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Page.enable()
        await chrome.Runtime.enable()
        
        print("⏳ 演示事件等待功能...")
        
        # 导航到页面
        await chrome.Page.navigate(url="https://httpbin.org/delay/2")
        
        # 等待特定事件
        print("🔄 等待页面开始加载...")
        dom_event, messages = await chrome.wait_event("Page.domContentEventFired", timeout=15)
        
        if dom_event:
            print("✓ DOM 内容加载完成!")
            print(f"📊 等待期间收到 {len(messages)} 条消息")
            
            # 分析收到的消息类型
            message_types = {}
            for msg in messages:
                method = msg.get('method', 'unknown')
                message_types[method] = message_types.get(method, 0) + 1
            
            print("📈 消息类型统计:")
            for method, count in sorted(message_types.items()):
                print(f"  {method}: {count}")
        else:
            print("⚠️ 等待事件超时")
        
        # 等待任意消息
        print("\n⏳ 等待任意消息...")
        any_message = await chrome.wait_message(timeout=5)
        if any_message:
            print(f"📨 收到消息: {any_message.get('method', 'unknown')}")
        else:
            print("⚠️ 等待消息超时")
        
        # 获取所有未读消息
        unread_messages = chrome.pop_messages()
        print(f"📬 未读消息数量: {len(unread_messages)}")
        
    except Exception as e:
        print(f"❌ 事件等待过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def storage_operations_example():
    """存储操作示例"""
    print("\n=== 存储操作示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Storage.enable()
        await chrome.Page.enable()
        await chrome.Runtime.enable()
        
        # 导航到一个有存储数据的页面
        await chrome.Page.navigate(url="https://httpbin.org")
        await chrome.wait_event("Page.loadEventFired", timeout=10)
        
        # 设置一些本地存储数据
        print("💾 设置本地存储数据...")
        await chrome.Runtime.evaluate(
            expression="localStorage.setItem('test_key', 'test_value')"
        )
        await chrome.Runtime.evaluate(
            expression="sessionStorage.setItem('session_key', 'session_value')"
        )
        
        # 获取存储使用情况
        print("📊 获取存储使用情况...")
        usage_result, _ = await chrome.Storage.getUsageAndQuota(origin="https://httpbin.org")
        
        if usage_result and 'usage' in usage_result:
            usage = usage_result['usage']
            quota = usage_result['quota']
            print(f"💽 存储使用情况: {usage} / {quota} 字节")
        
        # 读取本地存储数据
        local_result, _ = await chrome.Runtime.evaluate(
            expression="localStorage.getItem('test_key')"
        )
        session_result, _ = await chrome.Runtime.evaluate(
            expression="sessionStorage.getItem('session_key')"
        )
        
        if local_result and 'result' in local_result:
            print(f"🔑 本地存储数据: {local_result['result']['value']}")
        if session_result and 'result' in session_result:
            print(f"🔑 会话存储数据: {session_result['result']['value']}")
        
        # 清除存储数据
        print("🧹 清除存储数据...")
        clear_result, _ = await chrome.Storage.clearDataForOrigin(
            origin="https://httpbin.org",
            storageTypes="local_storage,session_storage"
        )
        
        if clear_result:
            print("✓ 存储数据已清除")
        
    except Exception as e:
        print(f"❌ 存储操作过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 演示连接错误处理
        print("🔌 测试连接错误处理...")
        
        # 尝试连接到不存在的端口
        chrome_bad = ChromeInterface(port=9999)
        success = await chrome_bad.connect()
        
        if not success:
            print("✓ 正确处理了连接失败")
        
        # 正常连接
        success = await chrome.connect()
        if not success:
            print("❌ 无法连接到 Chrome，请检查是否启动")
            return
        
        await chrome.Runtime.enable()
        
        # 演示 JavaScript 执行错误
        print("🐛 测试 JavaScript 执行错误...")
        error_result, _ = await chrome.Runtime.evaluate(
            expression="nonexistent_variable"
        )
        
        if error_result and 'exceptionDetails' in error_result:
            exception = error_result['exceptionDetails']
            print(f"✓ 正确捕获 JavaScript 错误: {exception.get('text', 'Unknown error')}")
        
        # 演示超时处理
        print("⏰ 测试超时处理...")
        event, messages = await chrome.wait_event("NonExistentEvent", timeout=2)
        
        if event is None:
            print("✓ 正确处理了事件等待超时")
        
        # 演示消息处理
        message = await chrome.wait_message(timeout=1)
        if message is None:
            print("✓ 正确处理了消息等待超时")
        
    except Exception as e:
        print(f"⚠️ 捕获到异常: {e}")
        print("✓ 异常处理机制正常工作")
    finally:
        await chrome.disconnect()

async def performance_comparison_example():
    """性能对比示例"""
    print("\n=== 性能对比示例 ===")
    
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Runtime.enable()
        
        # 测试批量操作性能
        print("⚡ 测试批量 JavaScript 执行性能...")
        
        import time
        
        # 批量执行多个简单操作
        start_time = time.time()
        
        operations = [
            "Math.random()",
            "Date.now()",
            "navigator.userAgent.length",
            "document.readyState",
            "window.innerWidth"
        ]
        
        results = []
        for i, operation in enumerate(operations):
            result, _ = await chrome.Runtime.evaluate(expression=operation)
            if result and 'result' in result:
                results.append(result['result']['value'])
            
            if i == 0:
                print(f"  操作 {i+1}: {operation} = {results[-1] if results else 'Error'}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 批量执行 {len(operations)} 个操作耗时: {duration:.3f} 秒")
        print(f"📈 平均每个操作: {duration/len(operations):.3f} 秒")
        
        # 测试消息处理性能
        print("\n📨 测试消息处理性能...")
        
        # 导航到页面以产生消息
        await chrome.Page.enable()
        await chrome.Page.navigate(url="https://httpbin.org/json")
        
        start_time = time.time()
        message_count = 0
        
        # 收集5秒内的所有消息
        while (time.time() - start_time) < 5:
            message = await chrome.wait_message(timeout=1)
            if message:
                message_count += 1
            else:
                break
        
        # 获取剩余的未读消息
        remaining = chrome.pop_messages()
        total_messages = message_count + len(remaining)
        
        duration = time.time() - start_time
        print(f"📊 {duration:.1f} 秒内处理了 {total_messages} 条消息")
        print(f"📈 消息处理速率: {total_messages/duration:.1f} 消息/秒")
        
    except Exception as e:
        print(f"❌ 性能测试过程中出现错误: {e}")
    finally:
        await chrome.disconnect()

async def main():
    """主函数 - 运行所有示例"""
    print("🚀 Chrome DevTools Library - 简化 API 示例集合")
    print("=" * 60)
    
    examples = [
        ("基础使用", basic_simplified_example),
        ("页面导航", navigation_example),
        ("网络监控", network_monitoring_example),
        ("直接目标连接", direct_target_connection_example),
        ("Android 环境", android_environment_example),
        ("事件等待", event_waiting_example),
        ("存储操作", storage_operations_example),
        ("错误处理", error_handling_example),
        ("性能对比", performance_comparison_example),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
            print(f"\n✅ {name}示例执行完成")
        except Exception as e:
            print(f"\n❌ {name}示例执行失败: {e}")
        
        # 在示例之间添加分隔
        print("-" * 60)
    
    print("\n🎉 所有简化 API 示例执行完成!")
    print("\n💡 提示:")
    print("  - 确保 Chrome 已启动并开启调试端口 (--remote-debugging-port=9222)")
    print("  - 某些示例需要网络连接")
    print("  - Android 示例需要连接到 Android 设备的 Chrome")

if __name__ == "__main__":
    asyncio.run(main())