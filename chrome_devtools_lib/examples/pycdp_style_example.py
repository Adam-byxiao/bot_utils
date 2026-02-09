#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyChromeDevTools 风格的 API 使用示例
展示借鉴 PyChromeDevTools 的新功能
"""

import asyncio
import time
import logging
from pathlib import Path
import sys

# 添加库路径
sys.path.append(str(Path(__file__).parent.parent))

from simplified_api import ChromeInterface
from client import ChromeDevToolsClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_page_loading_time():
    """示例1: 页面加载时间测量（类似 PyChromeDevTools 示例）"""
    print("\n=== 示例1: 页面加载时间测量 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 连接到 Chrome
        await chrome.connect()
        
        # 启用必要的域
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        # 记录开始时间
        start_time = time.time()
        
        # 导航到页面
        await chrome.Page.navigate(url="http://www.google.com/")
        
        # 等待页面加载完成
        event, all_events = await chrome.wait_event("Page.loadEventFired", timeout=60)
        
        # 计算加载时间
        end_time = time.time()
        loading_time = end_time - start_time
        
        print(f"页面加载时间: {loading_time:.2f} 秒")
        
        if event:
            print("页面加载完成事件已接收")
        else:
            print("页面加载超时")
            
    except Exception as e:
        logger.error(f"示例1执行失败: {e}")
    finally:
        await chrome.disconnect()


async def example_2_cookies_extraction():
    """示例2: 提取所有 cookies（类似 PyChromeDevTools 示例）"""
    print("\n=== 示例2: 提取所有 cookies ===")
    
    chrome = ChromeInterface()
    
    try:
        # 连接到 Chrome
        await chrome.connect()
        
        # 启用必要的域
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        # 导航到页面
        await chrome.Page.navigate(url="http://www.nytimes.com/")
        
        # 等待页面停止加载
        event, all_events = await chrome.wait_event("Page.frameStoppedLoading", timeout=60)
        
        # 等待额外的对象加载
        await asyncio.sleep(5)
        
        # 获取 cookies
        cookies_result, messages = await chrome.Network.getCookies()
        
        print(f"找到 {len(cookies_result.get('cookies', []))} 个 cookies:")
        
        for cookie in cookies_result.get('cookies', []):
            print("Cookie:")
            print(f"\t域名: {cookie.get('domain', 'N/A')}")
            print(f"\t键: {cookie.get('name', 'N/A')}")
            print(f"\t值: {cookie.get('value', 'N/A')}")
            print()
            
    except Exception as e:
        logger.error(f"示例2执行失败: {e}")
    finally:
        await chrome.disconnect()


async def example_3_network_monitoring():
    """示例3: 网络请求监控（类似 PyChromeDevTools 示例）"""
    print("\n=== 示例3: 网络请求监控 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 连接到 Chrome
        await chrome.connect()
        
        # 启用必要的域
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        # 导航到页面
        await chrome.Page.navigate(url="http://www.facebook.com")
        
        # 等待页面停止加载
        event, all_events = await chrome.wait_event("Page.frameStoppedLoading", timeout=60)
        
        print("网络请求 URLs:")
        
        # 处理所有接收到的消息
        for message in all_events:
            if message.get("method") == "Network.responseReceived":
                try:
                    url = message["params"]["response"]["url"]
                    print(f"  {url}")
                except KeyError:
                    pass
                    
    except Exception as e:
        logger.error(f"示例3执行失败: {e}")
    finally:
        await chrome.disconnect()


async def example_4_direct_target_connection():
    """示例4: 直接 targetID 连接（新功能）"""
    print("\n=== 示例4: 直接 targetID 连接 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 获取所有标签页
        tabs = await chrome.get_tabs()
        
        if tabs:
            target_id = tabs[0]['id']
            print(f"直接连接到目标: {target_id}")
            
            # 直接连接到指定的 targetID
            success = await chrome.connect_target_id(target_id)
            
            if success:
                print("直接连接成功!")
                
                # 启用 Runtime 域
                await chrome.Runtime.enable()
                
                # 执行 JavaScript
                result, messages = await chrome.Runtime.evaluate(expression="document.title")
                print(f"页面标题: {result.get('result', {}).get('value', 'N/A')}")
            else:
                print("直接连接失败")
        else:
            print("未找到可用的标签页")
            
    except Exception as e:
        logger.error(f"示例4执行失败: {e}")
    finally:
        await chrome.disconnect()


async def example_5_android_support():
    """示例5: Android 环境支持（新功能）"""
    print("\n=== 示例5: Android 环境支持 ===")
    
    # 创建支持 Android 环境的接口
    chrome = ChromeInterface(suppress_origin=True)
    
    try:
        print("使用 Android 兼容模式连接...")
        
        # 连接到 Chrome（Android 模式）
        success = await chrome.connect()
        
        if success:
            print("Android 模式连接成功!")
            
            # 启用 Page 域
            await chrome.Page.enable()
            
            # 获取页面信息
            result, messages = await chrome.Page.getNavigationHistory()
            print(f"导航历史条目数: {len(result.get('entries', []))}")
        else:
            print("Android 模式连接失败（可能不在 Android 环境中）")
            
    except Exception as e:
        logger.error(f"示例5执行失败: {e}")
    finally:
        await chrome.disconnect()


async def example_6_enhanced_event_waiting():
    """示例6: 增强的事件等待机制（新功能）"""
    print("\n=== 示例6: 增强的事件等待机制 ===")
    
    chrome = ChromeInterface()
    
    try:
        # 连接到 Chrome
        await chrome.connect()
        
        # 启用必要的域
        await chrome.Runtime.enable()
        await chrome.Page.enable()
        
        # 导航到页面
        await chrome.Page.navigate(url="http://www.example.com/")
        
        print("演示不同的事件等待方式:")
        
        # 1. 等待特定事件
        print("1. 等待页面加载事件...")
        event, all_events = await chrome.wait_event("Page.loadEventFired", timeout=10)
        if event:
            print(f"   接收到事件: {event.get('method')}")
        
        # 2. 等待单个消息
        print("2. 等待单个消息...")
        message = await chrome.wait_message(timeout=2)
        if message:
            print(f"   接收到消息: {message.get('method', 'Unknown')}")
        
        # 3. 获取所有消息（非阻塞）
        print("3. 获取所有未读消息...")
        messages = chrome.pop_messages()
        print(f"   获取到 {len(messages)} 条消息")
        
    except Exception as e:
        logger.error(f"示例6执行失败: {e}")
    finally:
        await chrome.disconnect()


async def main():
    """主函数，运行所有示例"""
    print("Chrome DevTools 库 - PyChromeDevTools 风格 API 示例")
    print("=" * 60)
    
    examples = [
        example_1_page_loading_time,
        example_2_cookies_extraction,
        example_3_network_monitoring,
        example_4_direct_target_connection,
        example_5_android_support,
        example_6_enhanced_event_waiting
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
        except Exception as e:
            logger.error(f"示例 {i} 执行失败: {e}")
        
        # 在示例之间添加延迟
        if i < len(examples):
            await asyncio.sleep(2)
    
    print("\n所有示例执行完成!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())