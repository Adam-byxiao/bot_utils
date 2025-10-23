# 远程语音代理监控器使用说明

## 概述

这个工具集用于通过 SSH 端口转发连接远程设备，获取 Chrome DevTools 中的 `realtimeVoiceAgent.session.history` 数据，并按照 input/output 分类输出到本地文件。

## 功能特性

- 🔗 通过 Chrome DevTools Protocol (CDP) 连接远程设备
- 🎯 执行 JavaScript 代码获取语音代理会话历史
- 📊 智能解析和分类语音消息数据
- 📁 按用户输入/助手输出分类导出数据
- 📈 生成会话统计摘要
- 🔄 支持实时监控和数据更新

## 文件结构

```
network_monitor/
├── chrome_console_executor.py      # Chrome DevTools 连接和 JavaScript 执行
├── realtime_voice_agent_parser.py  # 语音代理数据解析器
├── voice_data_exporter.py          # 数据分类和文件导出
├── remote_voice_agent_monitor.py   # 主监控器（整合所有功能）
├── test_remote_voice_monitor.py    # 测试脚本
└── README_远程语音代理监控.md       # 本说明文档
```

## 使用步骤

### 1. 环境准备

确保已安装必要的 Python 依赖：
```bash
pip install websockets aiohttp asyncio
```

### 2. 建立 SSH 端口转发

连接到远程设备并建立端口转发：
```bash
ssh root@device_ip -L 9222:localhost:9222
```

这将把远程设备的 9222 端口转发到本地的 9222 端口。

### 3. 启动 Chrome 调试模式

在远程设备上，确保 Chrome 以调试模式启动：
```bash
chrome --remote-debugging-port=9222
```

### 4. 打开 DevTools

1. 在本地浏览器中打开 `chrome://inspect`
2. 找到 "Bot Controller" 项目
3. 点击对应的 "inspect" 链接进入 DevTools
4. 确保可以在 Console 中执行 `realtimeVoiceAgent.session.history`

### 5. 运行监控器

#### 方法一：使用主监控器（推荐）

```python
import asyncio
from remote_voice_agent_monitor import RemoteVoiceAgentMonitor

async def main():
    monitor = RemoteVoiceAgentMonitor(
        chrome_host="localhost",
        chrome_port=9222,
        output_dir="voice_output"
    )
    
    # 运行完整的监控周期
    success = await monitor.run_monitoring_cycle()
    if success:
        print("监控完成，数据已导出")
    else:
        print("监控失败，请检查连接")

# 运行监控
asyncio.run(main())
```

#### 方法二：分步执行

```python
import asyncio
from chrome_console_executor import ChromeConsoleExecutor
from realtime_voice_agent_parser import RealtimeVoiceAgentParser
from voice_data_exporter import VoiceDataExporter

async def step_by_step_monitoring():
    # 1. 连接 Chrome DevTools
    executor = ChromeConsoleExecutor("localhost", 9222)
    connected = await executor.connect()
    if not connected:
        print("连接失败")
        return
    
    # 2. 获取会话历史数据
    history_data = await executor.get_session_history()
    if not history_data:
        print("获取数据失败")
        return
    
    # 3. 解析数据
    parser = RealtimeVoiceAgentParser()
    success = parser.parse_history_data(history_data)
    if not success:
        print("解析数据失败")
        return
    
    # 4. 导出数据
    exporter = VoiceDataExporter("voice_output")
    input_messages = parser.get_input_messages()
    output_messages = parser.get_output_messages()
    session_summary = parser.get_session_summary()
    
    result = exporter.export_classified_data(input_messages, output_messages, session_summary)
    print(f"导出完成: {result}")
    
    # 5. 断开连接
    await executor.disconnect()

# 运行分步监控
asyncio.run(step_by_step_monitoring())
```

## 输出文件说明

监控器会在指定的输出目录中生成以下文件：

### 1. 用户输入文件 (`user_inputs_YYYYMMDD_HHMMSS.txt`)
包含所有用户的语音输入内容，格式：
```
时间: 2024-01-15T10:30:00.000Z
角色: user
内容: 你好，请帮我查询天气
---
```

### 2. 助手输出文件 (`assistant_outputs_YYYYMMDD_HHMMSS.txt`)
包含所有助手的回复内容，格式：
```
时间: 2024-01-15T10:30:02.000Z
角色: assistant
内容: 好的，我来为您查询天气信息
---
```

### 3. 完整 JSON 数据 (`session_data_YYYYMMDD_HHMMSS.json`)
包含所有原始数据的 JSON 格式文件，便于程序处理。

### 4. 会话摘要 (`session_summary_YYYYMMDD_HHMMSS.txt`)
包含会话的统计信息：
```
会话摘要
========
会话开始时间: 2024-01-15T10:30:00.000Z
会话结束时间: 2024-01-15T10:30:07.000Z
会话持续时间: 7秒
总消息数: 4
用户输入数: 2
助手输出数: 2

消息类型分布:
- user: 2
- assistant: 2
```

### 5. 合并对话记录 (`conversation_YYYYMMDD_HHMMSS.txt`)
按时间顺序合并的完整对话记录，便于阅读。

## 测试功能

运行测试脚本验证功能：
```bash
python test_remote_voice_monitor.py
```

测试包括：
- ✅ 语音消息解析器测试
- ✅ 数据导出器测试  
- ⚠️ Chrome 连接测试（需要实际连接）
- ✅ 完整工作流程测试（使用模拟数据）

## 故障排除

### 1. 连接失败
**错误**: `连接Chrome DevTools失败`
**解决方案**:
- 确认 SSH 端口转发正常：`ssh root@device_ip -L 9222:localhost:9222`
- 确认远程设备 Chrome 已启动调试模式
- 检查端口是否被占用：`netstat -an | findstr 9222`

### 2. 数据获取失败
**错误**: `realtimeVoiceAgent is not available`
**解决方案**:
- 确认已在正确的页面（Bot Controller）
- 在 DevTools Console 中手动执行 `realtimeVoiceAgent.session.history` 确认可用
- 检查页面是否完全加载

### 3. 解析错误
**错误**: 数据解析失败
**解决方案**:
- 检查获取的数据格式是否正确
- 查看错误日志了解具体问题
- 使用测试脚本验证解析器功能

## API 参考

### ChromeConsoleExecutor
- `connect()`: 连接到 Chrome DevTools
- `execute_js(code)`: 执行 JavaScript 代码
- `get_session_history()`: 获取语音代理会话历史
- `check_realtime_voice_agent()`: 检查语音代理可用性
- `disconnect()`: 断开连接

### RealtimeVoiceAgentParser
- `parse_history_data(data)`: 解析历史数据
- `get_input_messages()`: 获取用户输入消息
- `get_output_messages()`: 获取助手输出消息
- `get_all_messages()`: 获取所有消息
- `get_session_summary()`: 获取会话摘要

### VoiceDataExporter
- `export_classified_data(inputs, outputs, summary)`: 导出分类数据
- `export_to_json(messages, filename)`: 导出 JSON 格式
- `export_session_summary(summary, filename)`: 导出会话摘要
- `get_export_stats()`: 获取导出统计信息

## 注意事项

1. **安全性**: 确保 SSH 连接的安全性，使用强密码或密钥认证
2. **网络稳定性**: 保持网络连接稳定，避免数据传输中断
3. **权限**: 确保有足够的权限访问远程设备和写入本地文件
4. **数据隐私**: 注意保护语音数据的隐私和安全

## 更新日志

- **v1.0.0**: 初始版本，支持基本的数据获取和分类导出功能
- 支持 SSH 端口转发连接
- 支持 Chrome DevTools JavaScript 执行
- 支持数据解析和分类
- 支持多种格式的文件导出