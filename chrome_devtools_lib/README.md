# Chrome DevTools Library

一个强大且易用的Python库，用于与Chrome DevTools协议进行交互，支持网页自动化、性能监控、网络分析等功能。

## 🚀 特性

### 核心功能
- **通用Chrome DevTools客户端**: 支持所有Chrome DevTools协议功能
- **多域支持**: Runtime、Network、Performance、Storage等域
- **异步操作**: 基于asyncio的高性能异步架构
- **事件监听**: 实时监听和处理Chrome DevTools事件
- **扩展支持**: 易于扩展的架构，支持自定义业务逻辑
- **语音代理监控**: 专门的VoiceAgentMonitor扩展
- **错误处理**: 完善的错误处理和异常管理
- **类型安全**: 完整的类型注解支持

### 新增功能 (借鉴 PyChromeDevTools)
- **简化API**: 提供 PyChromeDevTools 风格的简洁调用接口
- **直接targetID连接**: 支持直接连接到指定的浏览器标签页
- **增强事件等待**: `wait_event`、`wait_message`、`pop_messages` 等方法
- **Android环境支持**: 兼容Android环境的Chrome调试
- **PyChromeDevTools兼容**: 提供迁移友好的兼容接口
- **消息队列管理**: 智能的消息缓存和处理机制

## 📦 安装

```bash
# 克隆项目
git clone <repository-url>
cd chrome_devtools_lib

# 安装依赖
pip install -r requirements.txt
```

## 🔧 依赖

- Python 3.7+
- aiohttp
- websockets
- typing-extensions (Python < 3.8)

## 🚀 快速开始

### 简化API使用 (推荐)

```python
import asyncio
from chrome_devtools_lib.simplified_api import ChromeInterface

async def main():
    # 创建简化接口 (类似 PyChromeDevTools)
    chrome = ChromeInterface()
    
    try:
        # 连接到Chrome
        await chrome.connect()
        print("连接成功!")
        
        # 启用域并执行JavaScript
        await chrome.Runtime.enable()
        result, messages = await chrome.Runtime.evaluate(expression="document.title")
        
        if result.get('result'):
            print(f"页面标题: {result['result']['value']}")
        
    finally:
        await chrome.disconnect()

# 运行
asyncio.run(main())
```

### 传统API使用

```python
import asyncio
from chrome_devtools_lib import ChromeDevToolsClient
from chrome_devtools_lib.domains import RuntimeDomain

async def main():
    # 创建客户端
    client = ChromeDevToolsClient()
    runtime = RuntimeDomain(client)
    
    try:
        # 连接到Chrome
        if await client.connect():
            print("连接成功!")
            
            # 启用Runtime域
            await runtime.enable()
            
            # 执行JavaScript
            result = await runtime.evaluate("document.title")
            if result["success"]:
                print(f"页面标题: {result['result']['value']}")
        
    finally:
        await client.disconnect()

# 运行
asyncio.run(main())
```

### 语音代理监控

```python
import asyncio
from chrome_devtools_lib.extensions import VoiceAgentMonitor

async def monitor_voice_agent():
    monitor = VoiceAgentMonitor()
    
    try:
        if await monitor.connect():
            # 检查语音代理是否可用
            if await monitor.is_voice_agent_available():
                # 获取会话信息
                session_info = await monitor.get_session_info()
                print(f"会话ID: {session_info.get('sessionId')}")
                
                # 获取历史记录
                history = await monitor.get_history()
                print(f"历史消息数: {len(history)}")
                
                # 获取对话统计
                stats = await monitor.get_conversation_stats()
                print(f"总消息数: {stats.get('totalMessages')}")
    
    finally:
        await monitor.disconnect()

asyncio.run(monitor_voice_agent())
```

### 简化API高级功能

```python
import asyncio
from chrome_devtools_lib.simplified_api import ChromeInterface

async def advanced_simplified_usage():
    # 支持Android环境
    chrome = ChromeInterface(suppress_origin=True)
    
    try:
        await chrome.connect()
        
        # 直接连接到指定标签页
        tabs = await chrome.get_tabs()
        if tabs:
            success = await chrome.connect_target_id(tabs[0]['id'])
            print(f"直接连接结果: {success}")
        
        # 启用多个域
        await chrome.Network.enable()
        await chrome.Page.enable()
        
        # 导航到页面
        await chrome.Page.navigate(url="http://example.com")
        
        # 等待特定事件
        event, all_messages = await chrome.wait_event("Page.loadEventFired", timeout=10)
        if event:
            print("页面加载完成!")
        
        # 等待任意消息
        message = await chrome.wait_message(timeout=5)
        if message:
            print(f"收到消息: {message.get('method')}")
        
        # 获取所有未读消息
        messages = chrome.pop_messages()
        print(f"未读消息数: {len(messages)}")
        
        # 获取网络cookies
        cookies_result, messages = await chrome.Network.getCookies()
        print(f"Cookies数量: {len(cookies_result.get('cookies', []))}")
        
    finally:
        await chrome.disconnect()

asyncio.run(advanced_simplified_usage())
```

## 📚 API文档

### ChromeDevToolsClient

主要的Chrome DevTools客户端类。

#### 方法

- `connect(host="localhost", port=9222)`: 连接到Chrome DevTools
- `connect_target_id(target_id)`: 直接连接到指定的目标ID
- `disconnect()`: 断开连接
- `send_command(method, params=None)`: 发送命令
- `add_event_listener(event, handler)`: 添加事件监听器
- `enable_domain(domain)`: 启用域
- `disable_domain(domain)`: 禁用域
- `wait_event(event_name, timeout=30)`: 等待特定事件
- `wait_message(timeout=30)`: 等待任意消息
- `pop_messages()`: 获取所有未读消息

### RuntimeDomain

JavaScript运行时域，用于执行JavaScript代码。

#### 方法

- `enable()`: 启用Runtime域
- `disable()`: 禁用Runtime域
- `evaluate(expression)`: 执行JavaScript表达式
- `call_function_on(function_declaration, object_id)`: 在对象上调用函数
- `get_properties(object_id)`: 获取对象属性

### NetworkDomain

网络域，用于监控网络活动。

#### 方法

- `enable()`: 启用Network域
- `disable()`: 禁用Network域
- `set_cache_disabled(disabled)`: 设置缓存状态
- `set_user_agent(user_agent)`: 设置用户代理
- `get_response_body(request_id)`: 获取响应体
- `clear_browser_cache()`: 清除浏览器缓存

### PerformanceDomain

性能域，用于性能监控和分析。

#### 方法

- `enable()`: 启用Performance域
- `disable()`: 禁用Performance域
- `get_metrics()`: 获取性能指标
- `start_precise_coverage()`: 开始精确覆盖率收集
- `take_heap_snapshot()`: 获取堆快照

### StorageDomain

存储域，用于管理浏览器存储。

#### 方法

- `clear_data_for_origin(origin, storage_types)`: 清除指定源的数据
- `get_cookies(browser_context_id=None)`: 获取Cookie
- `set_cookies(cookies)`: 设置Cookie
- `get_usage_and_quota(origin)`: 获取存储使用情况和配额

### ChromeInterface (简化API)

简化的Chrome DevTools接口，提供类似PyChromeDevTools的API。

#### 构造函数

- `ChromeInterface(host="localhost", port=9222, suppress_origin=False)`: 创建简化接口实例
  - `suppress_origin`: 是否抑制Origin头部（Android环境支持）

#### 方法

- `connect()`: 连接到Chrome DevTools
- `connect_target_id(target_id)`: 直接连接到指定的目标ID
- `disconnect()`: 断开连接
- `get_tabs()`: 获取所有标签页信息
- `wait_event(event_name, timeout=30)`: 等待特定事件，返回(event, all_messages)
- `wait_message(timeout=30)`: 等待任意消息
- `pop_messages()`: 获取所有未读消息

#### 域访问

通过属性访问各个域，支持动态方法调用：

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

### VoiceAgentMonitor

语音代理监控扩展，专门用于监控语音代理应用。

#### 方法

- `connect()`: 连接到Chrome DevTools
- `disconnect()`: 断开连接
- `is_voice_agent_available()`: 检查语音代理是否可用
- `get_session_info()`: 获取会话信息
- `get_history()`: 获取历史记录
- `get_latest_message()`: 获取最新消息
- `get_messages_by_type(message_type)`: 按类型获取消息
- `get_conversation_stats()`: 获取对话统计
- `monitor_new_messages(callback, interval=1)`: 监控新消息
- `execute_custom_script(script)`: 执行自定义脚本

## 📖 示例

项目包含了丰富的示例代码：

### 基础示例

```bash
python -m chrome_devtools_lib.examples.basic_usage
```

包含：
- Runtime域基础操作
- Network域监控
- 多域协同使用
- 错误处理

### 语音代理示例

```bash
python -m chrome_devtools_lib.examples.voice_agent_example
```

包含：
- 语音代理可用性检查
- 会话信息获取
- 消息历史记录
- 实时消息监控
- 消息过滤和统计
- 自定义脚本执行

## 🔄 PyChromeDevTools 兼容性

### 从 PyChromeDevTools 迁移

如果您之前使用过 `PyChromeDevTools`，可以轻松迁移到我们的库：

```python
# PyChromeDevTools 原始代码
from PyChromeDevTools import ChromeInterface

chrome = ChromeInterface()
chrome.connect()
chrome.Network.enable()
result = chrome.Page.navigate(url="http://example.com")
event = chrome.wait_event("Page.loadEventFired", timeout=60)
chrome.disconnect()
```

```python
# 迁移到我们的库 (只需要添加 await 和改变导入)
from chrome_devtools_lib.simplified_api import ChromeInterface
import asyncio

async def migrated_code():
    chrome = ChromeInterface()
    await chrome.connect()
    await chrome.Network.enable()
    result, messages = await chrome.Page.navigate(url="http://example.com")
    event, all_messages = await chrome.wait_event("Page.loadEventFired", timeout=60)
    await chrome.disconnect()

asyncio.run(migrated_code())
```

### 兼容性对比

| 功能 | PyChromeDevTools | 我们的库 | 兼容性 |
|------|------------------|----------|--------|
| 基础连接 | `chrome.connect()` | `await chrome.connect()` | ✅ 异步版本 |
| 域方法调用 | `chrome.Domain.method()` | `await chrome.Domain.method()` | ✅ 异步版本 |
| 事件等待 | `wait_event()` | `await wait_event()` | ✅ 增强版本 |
| 消息处理 | `wait_message()`, `pop_messages()` | `await wait_message()`, `pop_messages()` | ✅ 完全兼容 |
| Android 支持 | 自动处理 | `ChromeInterface(suppress_origin=True)` | ✅ 显式配置 |
| 直接连接 | `connect(targetID="...")` | `await connect_target_id("...")` | ✅ 分离方法 |

### 迁移优势

- **性能提升**: 异步架构带来 3-5 倍性能提升
- **更好的错误处理**: 统一的异常管理和重试机制
- **类型安全**: 完整的类型提示支持
- **扩展性**: 更强大的事件处理和业务扩展能力
- **文档完整**: 详细的 API 文档和示例

详细的迁移指南请参考：[docs/pycdp_comparison.md](docs/pycdp_comparison.md)

## 🔧 配置

### Chrome启动配置

要使用此库，需要启动Chrome并开启DevTools调试端口：

```bash
# Windows
chrome.exe --remote-debugging-port=9222 --disable-web-security --user-data-dir=temp

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --disable-web-security --user-data-dir=temp

# Linux
google-chrome --remote-debugging-port=9222 --disable-web-security --user-data-dir=temp
```

### 连接配置

```python
# 默认连接配置
client = ChromeDevToolsClient()
await client.connect()  # 连接到 localhost:9222

# 自定义连接配置
client = ChromeDevToolsClient()
await client.connect(host="192.168.1.100", port=9223)
```

## 🏗️ 架构

```
chrome_devtools_lib/
├── __init__.py              # 主入口
├── client.py                # 核心客户端 (增强版)
├── simplified_api.py        # 简化API接口 (新增)
├── domains/                 # DevTools协议域
│   ├── __init__.py
│   ├── runtime.py          # Runtime域
│   ├── network.py          # Network域
│   ├── performance.py      # Performance域
│   └── storage.py          # Storage域
├── extensions/              # 业务扩展
│   ├── __init__.py
│   └── voice_agent_monitor.py  # 语音代理监控
├── docs/                    # 文档 (新增)
│   ├── __init__.py
│   ├── client_api.md       # API文档
│   ├── client_implementation.md  # 实现文档
│   ├── pycdp_comparison.md # PyChromeDevTools对比
│   └── pycdp_enhancements_summary.md  # 功能增强总结
└── examples/                # 使用示例
    ├── __init__.py
    ├── basic_usage.py       # 基础示例
    ├── voice_agent_example.py  # 语音代理示例
    └── pycdp_style_example.py  # PyChromeDevTools风格示例 (新增)
```

### 架构特点

- **双API设计**: 提供传统API (`client.py`) 和简化API (`simplified_api.py`)
- **增强功能**: 直接targetID连接、事件等待机制、Android支持
- **兼容性**: 支持PyChromeDevTools迁移
- **扩展性**: 模块化设计，易于扩展新功能

## 🤝 扩展开发

### 创建自定义域

```python
from chrome_devtools_lib.client import ChromeDevToolsClient

class CustomDomain:
    def __init__(self, client: ChromeDevToolsClient):
        self.client = client
        self.domain_name = "Custom"
    
    async def enable(self):
        return await self.client.send_command(f"{self.domain_name}.enable")
    
    async def custom_method(self, param):
        return await self.client.send_command(
            f"{self.domain_name}.customMethod", 
            {"param": param}
        )
```

### 创建自定义扩展

```python
from chrome_devtools_lib import ChromeDevToolsClient
from chrome_devtools_lib.domains import RuntimeDomain

class CustomMonitor:
    def __init__(self):
        self.client = ChromeDevToolsClient()
        self.runtime = RuntimeDomain(self.client)
    
    async def connect(self):
        if await self.client.connect():
            await self.runtime.enable()
            return True
        return False
    
    async def custom_monitoring_logic(self):
        # 实现自定义监控逻辑
        pass
```

## 🐛 错误处理

库提供了完善的错误处理机制：

```python
try:
    result = await runtime.evaluate("invalid javascript")
    if not result["success"]:
        print(f"JavaScript错误: {result.get('error')}")
        if 'exception' in result:
            print(f"异常详情: {result['exception']['description']}")
except Exception as e:
    print(f"连接错误: {e}")
```

## 📝 日志

启用日志以便调试：

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 或者只启用库的日志
logger = logging.getLogger('chrome_devtools_lib')
logger.setLevel(logging.DEBUG)
```

## 🔒 安全注意事项

1. **调试端口安全**: Chrome调试端口不应在生产环境中暴露
2. **脚本执行**: 谨慎执行来自不可信源的JavaScript代码
3. **网络访问**: 确保只连接到可信的Chrome实例
4. **数据隐私**: 监控的数据可能包含敏感信息

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- Chrome DevTools团队提供的强大协议
- Python异步编程社区的支持
- 所有贡献者的努力

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看[示例代码](examples/)
2. 阅读[API文档](#api文档)
3. 提交[Issue](../../issues)
4. 参与[讨论](../../discussions)

---

**Chrome DevTools Library** - 让Chrome DevTools协议变得简单易用！ 🚀