# KWS (Keyword Spotting) 计算工具

## 概述

KWS计算工具用于通过SSH连接到设备，实时监控语音唤醒词识别日志，解析并记录唤醒词识别的分数和触发状态。

## 功能特性

- **实时日志监控**: 通过SSH连接设备，实时监控vibe-ai日志文件
- **智能日志解析**: 自动解析KWS识别记录，提取phrase、score等关键信息
- **触发状态跟踪**: 区分已触发和未触发的唤醒词识别记录
- **数据导出**: 支持JSON和CSV格式的数据导出
- **统计分析**: 提供详细的识别统计和分析报告

## 系统要求

- Python 3.7+
- paramiko库（SSH连接）
- 目标设备需要支持SSH连接

## 安装依赖

```bash
pip install paramiko
```

## 使用方法

### 1. 基本使用

```bash
python KWS_calculate.py
```

运行后按提示输入：
- 设备IP地址
- SSH用户名
- SSH密码

### 2. 编程方式使用

```python
from KWS_calculate import KWSCalculator

# 创建KWS计算器
kws_calc = KWSCalculator("192.168.1.100", "root", "password")

# 连接设备
if kws_calc.connect():
    # 开始监控（在单独线程中）
    import threading
    monitor_thread = threading.Thread(target=kws_calc.start_monitoring)
    monitor_thread.start()
    
    # 监控一段时间后停止
    time.sleep(60)  # 监控60秒
    kws_calc.stop_monitoring()
    
    # 导出结果
    kws_calc.export_results()
    kws_calc.print_summary()
    
    # 断开连接
    kws_calc.disconnect()
```

## 日志格式说明

工具能够解析以下格式的日志：

### KWS识别记录
```
2025-10-14T07:36:02.463710Z INFO vibe-ai-server: [kws_sensory.cc(112)] Model: hey_hello_vibe recognized phrase: hello_vibe, score: 0.947266, begin: 560400, end: 571200
```

### 未触发记录
```
2025-10-14T07:36:02.463935Z INFO vibe-ai-server: [vibe_ai_server_impl.cc(560)] OnKwsSaveRecord: hello_vibe /* 此次分数接近但未达到触发阈值 */
```

### 已触发记录
```
2025-10-14T07:36:05.886494Z INFO vibe-ai-server: [vibe_ai_server_impl.cc(550)] OnKwsTriggered: hello_vibe /* 触发唤醒词 */
```

## 输出文件

### JSON格式 (kws_results_YYYYMMDD_HHMMSS.json)
```json
{
  "all_records": [...],
  "triggered_records": [...],
  "untriggered_records": [...],
  "summary": {
    "total_records": 100,
    "triggered_count": 85,
    "untriggered_count": 15,
    "trigger_rate": 0.85
  }
}
```

### CSV格式 (kws_results_YYYYMMDD_HHMMSS.csv)
包含以下列：
- 时间戳
- 唤醒词
- 分数
- 开始时间
- 结束时间
- 是否触发
- 原始日志

## 数据结构

### KWSRecord
```python
@dataclass
class KWSRecord:
    timestamp: str      # 时间戳
    phrase: str         # 唤醒词
    score: float        # 识别分数
    begin_time: int     # 开始时间
    end_time: int       # 结束时间
    triggered: bool     # 是否触发
    raw_log: str        # 原始日志
```

## 配置文件

可以使用 `config.json` 文件进行配置：

```json
{
  "ssh_connection": {
    "host": "192.168.1.100",
    "username": "root",
    "password": "your_password",
    "port": 22
  },
  "log_monitoring": {
    "log_file_path": "/var/log/vibe-ai/vibe-ai.LATEST",
    "monitoring_interval": 0.1,
    "timeout_seconds": 5
  },
  "output_settings": {
    "output_directory": "kws_output",
    "export_formats": ["json", "csv"],
    "auto_export_interval": 300
  }
}
```

## 故障排除

### 常见问题

1. **SSH连接失败**
   - 检查IP地址、用户名、密码是否正确
   - 确认设备SSH服务已启动
   - 检查网络连接

2. **日志文件不存在**
   - 确认日志文件路径是否正确
   - 检查用户是否有读取权限

3. **解析失败**
   - 检查日志格式是否与预期一致
   - 查看日志文件中的实际内容

### 调试模式

设置日志级别为DEBUG：
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## 性能优化

- 监控大量日志时，建议适当增加监控间隔
- 定期导出数据以避免内存占用过高
- 使用过滤条件减少不必要的数据处理

## 扩展功能

工具支持以下扩展：
- 自定义日志解析规则
- 多设备并行监控
- 实时数据可视化
- 告警和通知功能

## 许可证

本工具遵循项目整体许可证。

## 更新日志

### v1.0.0
- 初始版本
- 基本SSH连接和日志监控功能
- 支持KWS识别记录解析
- 触发状态跟踪
- JSON和CSV数据导出