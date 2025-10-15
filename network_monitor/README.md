# Chrome DevTools Network Monitor

通过 Chrome DevTools Protocol 获取设备后端信息并进行标准化处理的完整解决方案。

## 功能特性

- 🔍 **实时网络监控**: 通过 Chrome DevTools Protocol 实时捕获网络请求和响应
- 📊 **数据标准化**: 将原始网络数据转换为统一的标准格式
- 🎯 **智能过滤**: 支持多种过滤规则，去除无关数据和重复请求
- 📈 **多格式导出**: 支持 JSON、CSV、Excel、TXT 等多种导出格式
- 📋 **详细报告**: 自动生成网络监控摘要报告
- ⚙️ **灵活配置**: 通过配置文件自定义监控行为

## 系统要求

- Python 3.8+
- Chrome/Chromium 浏览器
- Windows/Linux/macOS

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Chrome 调试模式

在启动 Chrome 时添加调试参数：

**Windows:**
```cmd
chrome.exe --remote-debugging-port=9222 --disable-web-security --user-data-dir="C:\temp\chrome_debug"
```

**Linux/macOS:**
```bash
google-chrome --remote-debugging-port=9222 --disable-web-security --user-data-dir="/tmp/chrome_debug"
```

### 3. 验证连接

打开浏览器访问 `http://localhost:9222/json` 确认调试接口可用。

## 快速开始

### 基本使用

```bash
# 使用默认配置开始监控
python main.py

# 监控指定时间（60秒）
python main.py -d 60

# 使用自定义配置文件
python main.py -c my_config.json

# 创建默认配置文件
python main.py --create-config

# 详细日志输出
python main.py -v
```

### 配置文件说明

配置文件 `config.json` 包含以下选项：

```json
{
  "chrome_host": "localhost",          // Chrome 调试接口地址
  "chrome_port": 9222,                 // Chrome 调试接口端口
  "session_id": "demo_session",        // 会话标识
  "output_dir": "./output",            // 输出目录
  "filters": {
    "exclude_static_resources": true,   // 排除静态资源
    "api_only": false,                  // 仅包含API请求
    "exclude_status_codes": [404, 500], // 排除的状态码
    "include_domains": []               // 包含的域名列表
  },
  "export": {
    "formats": ["json", "csv", "txt"],  // 导出格式
    "include_summary": true             // 包含摘要报告
  }
}
```

## 使用示例

### 示例 1: 监控 API 请求

```json
{
  "filters": {
    "api_only": true,
    "include_domains": ["api.example.com"]
  }
}
```

### 示例 2: 排除错误请求

```json
{
  "filters": {
    "exclude_status_codes": [400, 401, 403, 404, 500, 502, 503]
  }
}
```

### 示例 3: 仅导出 Excel 格式

```json
{
  "export": {
    "formats": ["excel"],
    "include_summary": true
  }
}
```

## 编程接口

### 基本用法

```python
import asyncio
from main import NetworkMonitor, get_default_config

async def monitor_example():
    # 创建配置
    config = get_default_config()
    config['filters']['api_only'] = True
    
    # 创建监控器
    monitor = NetworkMonitor(config)
    
    # 开始监控（60秒）
    await monitor.start_monitoring(duration=60)

# 运行示例
asyncio.run(monitor_example())
```

### 自定义事件处理

```python
from chrome_network_listener import ChromeNetworkListener

async def custom_monitor():
    listener = ChromeNetworkListener()
    
    # 自定义请求处理
    async def on_request(request_data):
        print(f"捕获请求: {request_data.get('request', {}).get('url')}")
    
    listener.on_request_sent = on_request
    
    await listener.connect()
    await listener.start_listening()
```

## 输出文件说明

监控完成后，会在输出目录生成以下文件：

- `network_data_YYYYMMDD_HHMMSS.json` - 完整的网络数据（JSON格式）
- `network_data_YYYYMMDD_HHMMSS.csv` - 扁平化的数据表格
- `network_data_YYYYMMDD_HHMMSS.xlsx` - Excel工作簿（包含多个工作表）
- `network_data_YYYYMMDD_HHMMSS.txt` - 可读的文本报告
- `network_summary_YYYYMMDD_HHMMSS.txt` - 监控摘要报告

### Excel 文件结构

- **Transactions** - 主要事务数据
- **Summary** - 基本统计信息
- **API_Stats** - API端点统计
- **Errors** - 错误统计

## 数据结构

### 标准化事务格式

```json
{
  "transaction_id": "unique_id",
  "session_id": "session_123",
  "timestamp": "2024-01-01T12:00:00Z",
  "duration_ms": 150.5,
  "success": true,
  "error_message": null,
  "request": {
    "method": "GET",
    "url": "https://api.example.com/v1/users",
    "domain": "api.example.com",
    "path": "/v1/users",
    "endpoint": "/v1/users",
    "query_parameters": {},
    "headers": {},
    "content_type": "application/json",
    "size_bytes": 1024,
    "is_api": true,
    "api_version": "v1"
  },
  "response": {
    "status_code": 200,
    "status_category": "success",
    "headers": {},
    "content_type": "application/json",
    "size_bytes": 2048,
    "is_json": true
  },
  "tags": ["api", "method:get", "status:success"],
  "metadata": {
    "performance_category": "normal",
    "total_size_bytes": 3072,
    "is_secure": true
  }
}
```

## 故障排除

### 常见问题

1. **连接失败**
   - 确认 Chrome 已启动调试模式
   - 检查端口 9222 是否被占用
   - 验证防火墙设置

2. **没有数据捕获**
   - 确认浏览器中有网络活动
   - 检查过滤器配置是否过于严格
   - 查看日志文件了解详细错误

3. **导出失败**
   - 检查输出目录权限
   - 确认依赖包已正确安装
   - 查看错误日志

### 调试模式

```bash
# 启用详细日志
python main.py -v

# 查看日志文件
tail -f network_monitor.log
```

## 高级功能

### 自定义过滤器

```python
from data_filter import DataFilter

# 创建过滤器
filter_engine = DataFilter()

# 添加自定义规则
filter_engine.add_rule(
    name='custom_api_filter',
    rule_type='include',
    pattern=r'/api/v[0-9]+/',
    field='url'
)
```

### 批量处理

```python
# 处理多个会话数据
sessions = ['session1', 'session2', 'session3']

for session_id in sessions:
    config = get_default_config()
    config['session_id'] = session_id
    
    monitor = NetworkMonitor(config)
    await monitor.start_monitoring(duration=30)
```

## 性能优化

- 使用过滤器减少不必要的数据处理
- 适当设置监控时间，避免过长的监控会话
- 定期清理输出目录
- 在生产环境中禁用详细日志

## 安全注意事项

- Chrome 调试模式会降低浏览器安全性，仅在测试环境使用
- 监控数据可能包含敏感信息，注意数据保护
- 不要在生产环境中长期开启调试模式

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的网络监控功能
- 多格式数据导出
- 配置文件支持