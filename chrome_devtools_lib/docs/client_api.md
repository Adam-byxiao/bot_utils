# ChromeDevToolsClient API 文档

## 概述

`ChromeDevToolsClient` 是 Chrome DevTools 通用库的核心客户端类，提供了与 Chrome 浏览器 DevTools 协议的完整交互能力。该类基于 WebSocket 连接实现，支持异步操作、事件监听和多域管理。

## 类定义

```python
class ChromeDevToolsClient:
    """Chrome DevTools 通用客户端"""
```

## 构造函数

### `__init__(debug_port: int = 9222, host: str = 'localhost')`

初始化 Chrome DevTools 客户端实例。

**参数：**
- `debug_port` (int): Chrome 调试端口，默认 9222
- `host` (str): Chrome 主机地址，默认 'localhost'

**示例：**
```python
# 使用默认配置
client = ChromeDevToolsClient()

# 自定义端口和主机
client = ChromeDevToolsClient(debug_port=9223, host='192.168.1.100')
```

## 核心方法

### 连接管理

#### `async connect(tab_url_pattern: str = None, tab_title_pattern: str = None) -> bool`

连接到 Chrome DevTools。

**参数：**
- `tab_url_pattern` (str, 可选): 标签页 URL 模式，用于匹配特定标签页
- `tab_title_pattern` (str, 可选): 标签页标题模式，用于匹配特定标签页

**返回值：**
- `bool`: 连接是否成功

**功能说明：**
1. 通过 HTTP API 获取所有可用标签页
2. 根据 URL 或标题模式查找目标标签页
3. 建立 WebSocket 连接
4. 启动事件监听任务

**示例：**
```python
# 连接到任意标签页
success = await client.connect()

# 连接到特定 URL 的标签页
success = await client.connect(tab_url_pattern="localhost:3000")

# 连接到特定标题的标签页
success = await client.connect(tab_title_pattern="React App")
```

#### `async disconnect()`

断开与 Chrome DevTools 的连接。

**功能说明：**
- 设置连接状态为 False
- 关闭 WebSocket 连接
- 记录断开连接日志

**示例：**
```python
await client.disconnect()
```

#### `async connect_target_id(target_id: str) -> bool`

直接连接到指定的目标ID（标签页）。

**参数：**
- `target_id` (str): 目标标签页的ID

**返回值：**
- `bool`: 连接是否成功

**功能说明：**
- 直接使用目标ID建立WebSocket连接
- 支持Android环境（根据suppress_origin参数）
- 跳过标签页发现过程，提高连接效率

**示例：**
```python
# 获取标签页列表
tabs = await client.get_tabs()
if tabs:
    # 直接连接到第一个标签页
    success = await client.connect_target_id(tabs[0]['id'])
```

### 消息和事件处理

#### `async wait_event(event_name: str, timeout: float = 30.0) -> Tuple[Optional[Dict], List[Dict]]`

等待特定的Chrome DevTools事件。

**参数：**
- `event_name` (str): 要等待的事件名称（如 'Page.loadEventFired'）
- `timeout` (float): 超时时间（秒），默认30秒

**返回值：**
- `Tuple[Optional[Dict], List[Dict]]`: 
  - 第一个元素：匹配的事件（如果找到）
  - 第二个元素：等待期间接收到的所有消息列表

**示例：**
```python
# 等待页面加载完成事件
event, all_messages = await client.wait_event("Page.loadEventFired", timeout=10)
if event:
    print("页面加载完成!")
    print(f"等待期间收到 {len(all_messages)} 条消息")
```

#### `async wait_message(timeout: float = 30.0) -> Optional[Dict]`

等待任意Chrome DevTools消息。

**参数：**
- `timeout` (float): 超时时间（秒），默认30秒

**返回值：**
- `Optional[Dict]`: 接收到的消息，超时时返回None

**示例：**
```python
# 等待任意消息
message = await client.wait_message(timeout=5)
if message:
    print(f"收到消息: {message.get('method', 'unknown')}")
```

#### `pop_messages() -> List[Dict]`

获取所有未读的Chrome DevTools消息。

**返回值：**
- `List[Dict]`: 所有未读消息的列表

**功能说明：**
- 返回消息队列中的所有消息
- 调用后清空消息队列
- 非阻塞操作

**示例：**
```python
# 获取所有未读消息
messages = client.pop_messages()
print(f"未读消息数量: {len(messages)}")
for msg in messages:
    print(f"消息类型: {msg.get('method', 'unknown')}")
```

### 命令执行

#### `async execute_command(method: str, params: Dict = None) -> Dict`

执行通用 Chrome DevTools Protocol (CDP) 命令。

**参数：**
- `method` (str): CDP 方法名（如 'Runtime.evaluate'）
- `params` (Dict, 可选): 命令参数

**返回值：**
- `Dict`: 包含执行结果的字典
  - `success` (bool): 执行是否成功
  - `result` (Dict): 命令执行结果（成功时）
  - `error` (str): 错误信息（失败时）
  - `timestamp` (str): 执行时间戳

**示例：**
```python
# 执行 JavaScript 代码
result = await client.execute_command(
    "Runtime.evaluate",
    {"expression": "document.title"}
)

if result["success"]:
    title = result["result"]["result"]["value"]
    print(f"页面标题: {title}")
else:
    print(f"执行失败: {result['error']}")
```

#### `async _send_command(method: str, params: Dict = None) -> Dict`

内部方法：发送 CDP 命令并等待响应。

**参数：**
- `method` (str): CDP 方法名
- `params` (Dict, 可选): 命令参数

**返回值：**
- `Dict`: 原始 CDP 响应

**注意：** 这是内部方法，建议使用 `execute_command` 替代。

### 域管理

#### `async enable_domain(domain: str) -> bool`

启用指定的 DevTools 域。

**参数：**
- `domain` (str): 域名（如 'Runtime', 'Network', 'Performance'）

**返回值：**
- `bool`: 是否启用成功

**功能说明：**
- 发送域启用命令
- 更新已启用域集合
- 记录启用状态

**示例：**
```python
# 启用 Runtime 域
await client.enable_domain("Runtime")

# 启用 Network 域
await client.enable_domain("Network")

# 启用 Performance 域
await client.enable_domain("Performance")
```

#### `async disable_domain(domain: str) -> bool`

禁用指定的 DevTools 域。

**参数：**
- `domain` (str): 域名

**返回值：**
- `bool`: 是否禁用成功

**示例：**
```python
await client.disable_domain("Network")
```

### 事件处理

#### `add_event_handler(event_name: str, handler: Callable)`

添加事件处理器。

**参数：**
- `event_name` (str): 事件名称（如 'Runtime.consoleAPICalled'）
- `handler` (Callable): 事件处理函数（异步函数）

**示例：**
```python
async def console_handler(params):
    print(f"控制台消息: {params}")

client.add_event_handler("Runtime.consoleAPICalled", console_handler)
```

#### `remove_event_handler(event_name: str, handler: Callable)`

移除事件处理器。

**参数：**
- `event_name` (str): 事件名称
- `handler` (Callable): 要移除的处理函数

**示例：**
```python
client.remove_event_handler("Runtime.consoleAPICalled", console_handler)
```

#### `async _event_listener()`

内部方法：事件监听器，处理 Chrome DevTools 事件。

**功能说明：**
- 持续监听 WebSocket 消息
- 识别事件消息（无 id 字段）
- 调用注册的事件处理器
- 处理连接异常

### 工具方法

#### `async get_tabs() -> List[Dict]`

获取所有可用的标签页。

**返回值：**
- `List[Dict]`: 标签页信息列表

**示例：**
```python
tabs = await client.get_tabs()
for tab in tabs:
    print(f"标题: {tab['title']}, URL: {tab['url']}")
```

#### `_find_target_tab(tabs: List[Dict], url_pattern: str = None, title_pattern: str = None) -> Optional[Dict]`

内部方法：查找目标标签页。

**参数：**
- `tabs` (List[Dict]): 标签页列表
- `url_pattern` (str, 可选): URL 模式
- `title_pattern` (str, 可选): 标题模式

**返回值：**
- `Optional[Dict]`: 匹配的标签页信息，未找到则返回 None

## 属性

### 实例属性

- `debug_port` (int): Chrome 调试端口
- `host` (str): Chrome 主机地址
- `websocket`: WebSocket 连接对象
- `is_connected` (bool): 连接状态
- `command_id` (int): 命令 ID 计数器
- `event_handlers` (Dict): 事件处理器字典
- `enabled_domains` (Set): 已启用的域集合

## 使用模式

### 基础使用模式

```python
import asyncio
from chrome_devtools_lib import ChromeDevToolsClient

async def main():
    client = ChromeDevToolsClient()
    
    # 连接
    if await client.connect():
        # 启用域
        await client.enable_domain("Runtime")
        
        # 执行命令
        result = await client.execute_command(
            "Runtime.evaluate",
            {"expression": "window.location.href"}
        )
        
        print(result)
        
        # 断开连接
        await client.disconnect()

asyncio.run(main())
```

### 事件监听模式

```python
async def setup_event_monitoring():
    client = ChromeDevToolsClient()
    
    # 定义事件处理器
    async def network_request_handler(params):
        print(f"网络请求: {params['request']['url']}")
    
    async def console_handler(params):
        print(f"控制台: {params['args'][0]['value']}")
    
    # 连接并启用域
    await client.connect()
    await client.enable_domain("Network")
    await client.enable_domain("Runtime")
    
    # 注册事件处理器
    client.add_event_handler("Network.requestWillBeSent", network_request_handler)
    client.add_event_handler("Runtime.consoleAPICalled", console_handler)
    
    # 保持连接
    await asyncio.sleep(60)  # 监听 60 秒
    
    await client.disconnect()
```

### 多标签页管理

```python
async def manage_multiple_tabs():
    client = ChromeDevToolsClient()
    
    # 获取所有标签页
    tabs = await client.get_tabs()
    
    for tab in tabs:
        print(f"发现标签页: {tab['title']} - {tab['url']}")
    
    # 连接到特定标签页
    await client.connect(tab_url_pattern="localhost")
    
    # 执行操作...
    
    await client.disconnect()
```

## 错误处理

### 常见异常

1. **连接异常**
   ```python
   try:
       await client.connect()
   except Exception as e:
       print(f"连接失败: {e}")
   ```

2. **命令执行异常**
   ```python
   result = await client.execute_command("Invalid.method")
   if not result["success"]:
       print(f"命令执行失败: {result['error']}")
   ```

3. **WebSocket 异常**
   - 自动在事件监听器中处理
   - 连接断开时会记录日志

## 最佳实践

### 1. 资源管理
```python
async def proper_resource_management():
    client = ChromeDevToolsClient()
    try:
        await client.connect()
        # 执行操作...
    finally:
        await client.disconnect()
```

### 2. 错误检查
```python
async def with_error_checking():
    client = ChromeDevToolsClient()
    
    if not await client.connect():
        print("连接失败")
        return
    
    if not await client.enable_domain("Runtime"):
        print("启用域失败")
        return
    
    result = await client.execute_command("Runtime.evaluate", {
        "expression": "document.title"
    })
    
    if result["success"]:
        print(f"成功: {result['result']}")
    else:
        print(f"失败: {result['error']}")
```

### 3. 事件处理器管理
```python
class EventManager:
    def __init__(self, client):
        self.client = client
        self.handlers = []
    
    def add_handler(self, event_name, handler):
        self.client.add_event_handler(event_name, handler)
        self.handlers.append((event_name, handler))
    
    def cleanup(self):
        for event_name, handler in self.handlers:
            self.client.remove_event_handler(event_name, handler)
```

## 扩展开发

### 创建域特定客户端

```python
class RuntimeClient:
    def __init__(self, base_client: ChromeDevToolsClient):
        self.client = base_client
    
    async def evaluate_js(self, expression: str):
        await self.client.enable_domain("Runtime")
        return await self.client.execute_command(
            "Runtime.evaluate",
            {"expression": expression}
        )
```

### 创建业务特定扩展

```python
class WebPageMonitor:
    def __init__(self, client: ChromeDevToolsClient):
        self.client = client
        self.page_loads = 0
    
    async def setup(self):
        await self.client.enable_domain("Page")
        self.client.add_event_handler(
            "Page.loadEventFired",
            self._on_page_load
        )
    
    async def _on_page_load(self, params):
        self.page_loads += 1
        print(f"页面加载次数: {self.page_loads}")
```

## 性能考虑

1. **连接复用**: 尽量复用同一个客户端实例
2. **域管理**: 只启用需要的域，及时禁用不需要的域
3. **事件处理**: 避免在事件处理器中执行耗时操作
4. **内存管理**: 及时移除不需要的事件处理器

## 安全注意事项

1. **端口安全**: 确保调试端口不对外暴露
2. **代码注入**: 谨慎处理用户输入的 JavaScript 代码
3. **权限控制**: 在生产环境中限制 DevTools 访问权限

## 依赖项

- `websockets`: WebSocket 客户端
- `aiohttp`: HTTP 客户端
- `asyncio`: 异步编程支持
- `json`: JSON 数据处理
- `logging`: 日志记录

## 版本兼容性

- Python 3.7+
- Chrome/Chromium 60+
- 支持所有主要的 Chrome DevTools Protocol 版本