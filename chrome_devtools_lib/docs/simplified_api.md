# ChromeInterface 简化 API 文档

## 概述

`ChromeInterface` 是 `chrome_devtools_lib` 提供的简化 API 接口，旨在提供类似 `PyChromeDevTools` 的使用体验。该接口封装了 `ChromeDevToolsClient` 的复杂性，提供更直观、更易用的方法来与 Chrome DevTools 交互。

## 设计理念

### 1. 简化操作
- 提供直观的域方法调用
- 自动处理连接和域启用
- 统一的返回值格式

### 2. 兼容性
- 支持 PyChromeDevTools 迁移
- 保持相似的 API 风格
- 异步版本的方法调用

### 3. 增强功能
- 直接 targetID 连接
- Android 环境支持
- 增强的事件等待机制
- 消息队列管理

## 类定义

```python
from chrome_devtools_lib.simplified_api import ChromeInterface

class ChromeInterface:
    """简化的 Chrome DevTools 接口"""
```

## 构造函数

### `ChromeInterface(host="localhost", port=9222, suppress_origin=False)`

创建简化接口实例。

**参数：**
- `host` (str): Chrome 主机地址，默认 'localhost'
- `port` (int): Chrome 调试端口，默认 9222
- `suppress_origin` (bool): 是否抑制 Origin 头部（Android 环境支持），默认 False

**示例：**
```python
# 标准连接
chrome = ChromeInterface()

# 自定义端口
chrome = ChromeInterface(port=9223)

# Android 环境
chrome = ChromeInterface(suppress_origin=True)

# 远程连接
chrome = ChromeInterface(host="192.168.1.100", port=9222)
```

## 核心方法

### 连接管理

#### `async connect() -> bool`

连接到 Chrome DevTools。

**返回值：**
- `bool`: 连接是否成功

**示例：**
```python
chrome = ChromeInterface()
success = await chrome.connect()
if success:
    print("连接成功")
```

#### `async connect_target_id(target_id: str) -> bool`

直接连接到指定的目标 ID。

**参数：**
- `target_id` (str): 目标标签页的 ID

**返回值：**
- `bool`: 连接是否成功

**示例：**
```python
# 获取标签页列表
tabs = await chrome.get_tabs()
if tabs:
    # 直接连接到第一个标签页
    success = await chrome.connect_target_id(tabs[0]['id'])
```

#### `async disconnect()`

断开连接。

**示例：**
```python
await chrome.disconnect()
```

#### `async get_tabs() -> List[Dict]`

获取所有标签页信息。

**返回值：**
- `List[Dict]`: 标签页信息列表

**示例：**
```python
tabs = await chrome.get_tabs()
for tab in tabs:
    print(f"标签页: {tab['title']} - {tab['url']}")
```

### 消息和事件处理

#### `async wait_event(event_name: str, timeout: float = 30.0) -> Tuple[Optional[Dict], List[Dict]]`

等待特定事件。

**参数：**
- `event_name` (str): 事件名称（如 'Page.loadEventFired'）
- `timeout` (float): 超时时间（秒）

**返回值：**
- `Tuple[Optional[Dict], List[Dict]]`: (目标事件, 所有消息列表)

**示例：**
```python
# 等待页面加载完成
event, all_messages = await chrome.wait_event("Page.loadEventFired", timeout=10)
if event:
    print("页面加载完成!")
    print(f"等待期间收到 {len(all_messages)} 条消息")
```

#### `async wait_message(timeout: float = 30.0) -> Optional[Dict]`

等待任意消息。

**参数：**
- `timeout` (float): 超时时间（秒）

**返回值：**
- `Optional[Dict]`: 接收到的消息

**示例：**
```python
message = await chrome.wait_message(timeout=5)
if message:
    print(f"收到消息: {message.get('method', 'unknown')}")
```

#### `pop_messages() -> List[Dict]`

获取所有未读消息。

**返回值：**
- `List[Dict]`: 未读消息列表

**示例：**
```python
messages = chrome.pop_messages()
print(f"未读消息数量: {len(messages)}")
```

## 域访问

### 动态域代理

`ChromeInterface` 通过 `DomainProxy` 类实现动态域方法调用：

```python
# 域启用
await chrome.Network.enable()
await chrome.Page.enable()
await chrome.Runtime.enable()

# 域方法调用
result, messages = await chrome.Page.navigate(url="http://example.com")
cookies_result, messages = await chrome.Network.getCookies()
eval_result, messages = await chrome.Runtime.evaluate(expression="document.title")
```

### 常用域和方法

#### Page 域

```python
# 导航到页面
result, messages = await chrome.Page.navigate(url="http://example.com")

# 重新加载页面
result, messages = await chrome.Page.reload()

# 获取页面源码
result, messages = await chrome.Page.getResourceContent(
    frameId="frame_id",
    url="http://example.com"
)
```

#### Network 域

```python
# 启用网络监控
await chrome.Network.enable()

# 获取 Cookies
cookies_result, messages = await chrome.Network.getCookies()

# 设置用户代理
result, messages = await chrome.Network.setUserAgentOverride(
    userAgent="Custom User Agent"
)

# 清除缓存
result, messages = await chrome.Network.clearBrowserCache()
```

#### Runtime 域

```python
# 执行 JavaScript
result, messages = await chrome.Runtime.evaluate(
    expression="document.title"
)

# 调用函数
result, messages = await chrome.Runtime.callFunctionOn(
    functionDeclaration="function() { return this.tagName; }",
    objectId="object_id"
)
```

#### Storage 域

```python
# 清除存储数据
result, messages = await chrome.Storage.clearDataForOrigin(
    origin="http://example.com",
    storageTypes="all"
)

# 获取存储使用情况
result, messages = await chrome.Storage.getUsageAndQuota(
    origin="http://example.com"
)
```

## 使用模式

### 1. 基础使用模式

```python
import asyncio
from chrome_devtools_lib.simplified_api import ChromeInterface

async def basic_usage():
    chrome = ChromeInterface()
    
    try:
        # 连接
        await chrome.connect()
        
        # 启用域
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        # 导航到页面
        result, messages = await chrome.Page.navigate(url="http://example.com")
        
        # 等待页面加载
        event, all_messages = await chrome.wait_event("Page.loadEventFired")
        
        # 执行 JavaScript
        eval_result, messages = await chrome.Runtime.evaluate(
            expression="document.title"
        )
        
        print(f"页面标题: {eval_result['result']['value']}")
        
    finally:
        await chrome.disconnect()

asyncio.run(basic_usage())
```

### 2. Android 环境使用

```python
async def android_usage():
    # Android 环境需要抑制 Origin 头部
    chrome = ChromeInterface(suppress_origin=True)
    
    try:
        await chrome.connect()
        # ... 其他操作
    finally:
        await chrome.disconnect()
```

### 3. 直接连接模式

```python
async def direct_connection():
    chrome = ChromeInterface()
    
    try:
        # 获取标签页列表
        tabs = await chrome.get_tabs()
        
        if tabs:
            # 直接连接到特定标签页
            success = await chrome.connect_target_id(tabs[0]['id'])
            if success:
                # ... 执行操作
                pass
    finally:
        await chrome.disconnect()
```

### 4. 事件监控模式

```python
async def event_monitoring():
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Network.enable()
        
        # 监控网络请求
        while True:
            message = await chrome.wait_message(timeout=5)
            if message and message.get('method') == 'Network.requestWillBeSent':
                request = message['params']['request']
                print(f"请求: {request['method']} {request['url']}")
                
    except KeyboardInterrupt:
        print("停止监控")
    finally:
        await chrome.disconnect()
```

## 错误处理

### 1. 连接错误

```python
async def handle_connection_errors():
    chrome = ChromeInterface()
    
    try:
        success = await chrome.connect()
        if not success:
            print("连接失败，请检查 Chrome 是否启动并开启调试端口")
            return
            
        # ... 执行操作
        
    except Exception as e:
        print(f"连接异常: {e}")
    finally:
        await chrome.disconnect()
```

### 2. 命令执行错误

```python
async def handle_command_errors():
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        
        # 执行可能失败的命令
        result, messages = await chrome.Runtime.evaluate(
            expression="nonexistent_variable"
        )
        
        # 检查执行结果
        if 'exceptionDetails' in result:
            print(f"JavaScript 执行错误: {result['exceptionDetails']}")
        else:
            print(f"执行成功: {result['result']['value']}")
            
    finally:
        await chrome.disconnect()
```

## 性能优化

### 1. 连接复用

```python
class ChromeManager:
    def __init__(self):
        self.chrome = ChromeInterface()
        self.connected = False
    
    async def ensure_connected(self):
        if not self.connected:
            self.connected = await self.chrome.connect()
        return self.connected
    
    async def execute_script(self, script):
        if await self.ensure_connected():
            return await self.chrome.Runtime.evaluate(expression=script)
        return None, []
    
    async def close(self):
        if self.connected:
            await self.chrome.disconnect()
            self.connected = False
```

### 2. 批量操作

```python
async def batch_operations():
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        await chrome.Runtime.enable()
        
        # 批量执行多个脚本
        scripts = [
            "document.title",
            "document.URL",
            "document.readyState"
        ]
        
        results = []
        for script in scripts:
            result, messages = await chrome.Runtime.evaluate(expression=script)
            results.append(result['result']['value'])
        
        print(f"批量执行结果: {results}")
        
    finally:
        await chrome.disconnect()
```

## 最佳实践

### 1. 使用上下文管理器

```python
class ChromeContext:
    def __init__(self, **kwargs):
        self.chrome = ChromeInterface(**kwargs)
    
    async def __aenter__(self):
        await self.chrome.connect()
        return self.chrome
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.chrome.disconnect()

# 使用示例
async def with_context():
    async with ChromeContext() as chrome:
        await chrome.Page.enable()
        result, messages = await chrome.Page.navigate(url="http://example.com")
```

### 2. 错误重试机制

```python
import asyncio
from typing import Optional

async def retry_operation(operation, max_retries=3, delay=1.0):
    """重试操作的通用函数"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"操作失败，{delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
    return None

# 使用示例
async def reliable_navigation():
    chrome = ChromeInterface()
    
    try:
        await chrome.connect()
        
        # 带重试的页面导航
        result = await retry_operation(
            lambda: chrome.Page.navigate(url="http://example.com")
        )
        
    finally:
        await chrome.disconnect()
```

### 3. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logged_operations():
    chrome = ChromeInterface()
    
    try:
        logger.info("开始连接 Chrome")
        success = await chrome.connect()
        
        if success:
            logger.info("连接成功")
            
            logger.info("导航到页面")
            result, messages = await chrome.Page.navigate(url="http://example.com")
            
            logger.info(f"导航结果: {result}")
            
        else:
            logger.error("连接失败")
            
    except Exception as e:
        logger.error(f"操作异常: {e}")
    finally:
        logger.info("断开连接")
        await chrome.disconnect()
```

## 与 PyChromeDevTools 的对比

| 特性 | PyChromeDevTools | ChromeInterface | 说明 |
|------|------------------|-----------------|------|
| 连接方式 | `chrome.connect()` | `await chrome.connect()` | 异步版本 |
| 域方法调用 | `chrome.Domain.method()` | `await chrome.Domain.method()` | 异步版本 |
| 返回值 | 单一结果 | `(result, messages)` | 增强版本 |
| 事件等待 | `wait_event()` | `await wait_event()` | 异步 + 增强 |
| Android 支持 | 自动处理 | 显式配置 | 更灵活 |
| 消息处理 | 基础支持 | 增强队列管理 | 更强大 |

## 总结

`ChromeInterface` 简化 API 提供了一个强大而易用的接口来与 Chrome DevTools 交互。它结合了 `PyChromeDevTools` 的简洁性和现代异步编程的优势，同时添加了许多增强功能，使其成为 Chrome 自动化和监控任务的理想选择。