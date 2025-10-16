# KWS测试错误分析工具

## 概述

KWS测试错误分析工具用于分析TTS播放记录与KWS识别结果的对应关系，自动检测KWS测试中的错误识别情况。

## 功能特性

- **时间戳对比**：确保TTS播放时间在KWS识别时间之前，且时间差不超过1秒
- **内容匹配**：比较TTS播放文本与KWS识别提示词的一致性
- **错误检测**：自动识别以下错误类型：
  - `negative_sample_recognized`：negative样本被错误识别为正确的提示词
  - `negative_sample_wrong_trigger`：negative样本触发了错误的提示词
- **结果输出**：生成详细的错误分析报告（CSV格式）

## 文件结构

```
voicecommand_script/
├── kws_error_analyzer.py      # 核心分析器类
├── run_kws_error_analysis.py  # 启动脚本
├── sample_tts_data.json       # 示例TTS数据
└── KWS_ERROR_ANALYSIS_README.md  # 使用说明
```

## 输入文件格式

### TTS播放记录文件 (JSON格式)

```json
[
  {
    "filename": "negative_001_hello_system_20251015_081220_500.wav",
    "sample_type": "negative",
    "speaker_id": "001",
    "text": "hello_system",
    "audio_type": "original",
    "timestamp": "2025/10/15 08:12:20.500"
  }
]
```

**字段说明：**
- `sample_type`: 样本类型（"positive" 或 "negative"）
- `text`: TTS播放的文本内容
- `timestamp`: 播放时间戳（格式：YYYY/MM/DD HH:MM:SS.fff）

### KWS识别结果文件 (CSV格式)

```csv
时间戳,提示词,分数,是否触发,开始时间,结束时间,原始日志
2025-10-15T08:12:21.340056Z,hello_vibe,1.0,是,24413800,24425500,"原始日志内容"
```

**字段说明：**
- `时间戳`: KWS识别时间戳（ISO格式）
- `提示词`: 识别到的关键词
- `是否触发`: 是否触发（"是" 或 "否"）

## 使用方法

### 方法1：自动模式

```bash
python run_kws_error_analysis.py
```

工具会自动查找最新的TTS和KWS文件进行分析。

### 方法2：手动指定文件

```bash
python run_kws_error_analysis.py <TTS_JSON_FILE> <KWS_CSV_FILE>
```

**示例：**
```bash
python run_kws_error_analysis.py ../realtime_parse_info_20251016_152145.json kws_output/kws_data_20251015_161706.csv
```

### 方法3：直接使用分析器类

```python
from kws_error_analyzer import KWSErrorAnalyzer

analyzer = KWSErrorAnalyzer()
analyzer.load_tts_records("tts_file.json")
analyzer.load_kws_records("kws_file.csv")
analyzer.analyze_records()
analyzer.save_error_analysis("output.csv")
analyzer.print_summary()
```

## 输出结果

### 控制台输出

```
KWS测试错误分析工具
========================================
TTS文件: sample_tts_data.json
KWS文件: kws_output/kws_data_20251015_161706.csv
----------------------------------------
正在加载数据文件...
2025-10-16 17:28:50,740 - INFO - 成功加载TTS记录文件: sample_tts_data.json
2025-10-16 17:28:50,741 - INFO - TTS记录总数: 6
2025-10-16 17:28:50,741 - INFO - 成功加载KWS记录文件: kws_output/kws_data_20251015_161706.csv
2025-10-16 17:28:50,741 - INFO - KWS记录总数: 10
正在执行错误分析...
2025-10-16 17:28:50,741 - INFO - 开始分析TTS记录与KWS记录的对应关系...
2025-10-16 17:28:50,745 - ERROR - ERROR: negative样本触发错误提示词 - TTS文本: hello_system, KWS提示词: hello_vibe
2025-10-16 17:28:50,746 - INFO - 分析完成，发现错误记录: 3 条
==================================================
KWS测试错误分析摘要
==================================================
TTS记录总数: 6
KWS记录总数: 10
发现错误记录: 3
错误类型统计:
  negative_sample_wrong_trigger: 3 条
==================================================

✅ 分析完成！
📄 错误分析结果已保存到: kws_error_analysis_20251016_172850.csv
⚠️  发现 3 条错误记录，请查看输出文件了解详情
```

### CSV输出文件

生成的CSV文件包含以下字段：

| 字段 | 说明 |
|------|------|
| error_type | 错误类型 |
| kws_timestamp | KWS识别时间戳 |
| kws_phrase | KWS识别的提示词 |
| kws_score | KWS识别分数 |
| kws_triggered | KWS是否触发 |
| tts_text | TTS播放的文本 |
| tts_time | TTS播放时间 |
| sample_type | 样本类型 |

## 错误类型说明

### 1. negative_sample_recognized
- **描述**：negative样本被错误识别为正确的提示词
- **条件**：TTS文本与KWS提示词匹配，且sample_type为"negative"
- **影响**：表示KWS系统对不应该识别的内容进行了错误识别

### 2. negative_sample_wrong_trigger
- **描述**：negative样本触发了错误的提示词
- **条件**：TTS文本与KWS提示词不匹配，KWS触发了识别，且sample_type为"negative"
- **影响**：表示KWS系统对错误的内容进行了误触发

## 分析逻辑

1. **时间戳验证**：
   - TTS播放时间必须在KWS识别时间之前
   - 时间差不能超过1秒
   - 如果TTS时间晚于KWS时间，报错并停止分析

2. **内容匹配**：
   - 标准化文本内容（转小写、去除下划线和连字符）
   - 比较TTS文本与KWS提示词是否一致

3. **错误检测**：
   - 根据sample_type和内容匹配结果判断是否为错误
   - 记录错误详情并输出到结果文件

## 注意事项

1. **时间戳格式**：确保TTS和KWS文件的时间戳格式正确
2. **文件编码**：建议使用UTF-8编码
3. **数据质量**：确保输入数据的完整性和准确性
4. **时间同步**：TTS和KWS数据应来自同一测试会话，确保时间同步

## 故障排除

### 常见错误

1. **"时间戳顺序错误"**
   - 原因：TTS和KWS数据来自不同的测试会话
   - 解决：使用同一测试会话的数据文件

2. **"文件不存在"**
   - 原因：文件路径错误或文件不存在
   - 解决：检查文件路径和文件是否存在

3. **"时间戳解析失败"**
   - 原因：时间戳格式不正确
   - 解决：检查时间戳格式是否符合要求

### 调试建议

1. 使用示例数据测试工具功能
2. 检查输入文件的数据格式
3. 查看控制台输出的详细日志信息
4. 检查生成的CSV文件内容

## 扩展功能

可以根据需要扩展以下功能：

1. **支持更多错误类型**
2. **添加统计图表生成**
3. **支持批量文件处理**
4. **添加配置文件支持**
5. **集成到GUI界面**