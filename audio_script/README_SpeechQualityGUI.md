# 语音质量分析GUI工具

## 功能概述

`SpeechQualityAnalyzer.py` 为 `speech_quality_ana.py` 提供了一个现代化的图形用户界面，具有以下功能：

### 主要特性

1. **用户友好的GUI界面** - 基于wxPython的现代化界面
2. **实时可视化** - 显示音频波形图和频谱图
3. **质量指标显示** - 实时显示SNR、RMS等质量指标
4. **批量处理** - 支持单个文件或整个文件夹的批量分析
5. **多种对齐算法** - 支持互相关和DTW两种对齐算法
6. **进度监控** - 实时显示处理进度和日志信息
7. **历史记录** - 记住最近使用的文件和文件夹
8. **智能路径显示** - 长路径自动截断显示，鼠标悬停显示完整路径
9. **独立选择列表** - 每个选择控件维护独立的最近使用列表

### 界面布局

- **左侧控制面板**：
  - 参考音频选择
  - 待分析音频选择（文件或文件夹）
  - 输出文件夹选择
  - 分析参数设置
  - 质量指标显示
  - 处理日志
  - 进度条

- **右侧可视化面板**：
  - 音频波形图（参考音频 vs 待分析音频）
  - 频谱图显示
  - 分析文件列表

## 安装依赖

```bash
pip install wxPython numpy scipy matplotlib librosa soundfile dtw
```

## 使用方法

### 方法1：直接运行
```bash
python SpeechQualityAnalyzer.py
```

### 方法2：使用启动脚本
```bash
python run_speech_quality_gui.py
```

## 操作步骤

1. **选择参考音频**：点击"浏览..."选择纯净的参考音频文件
2. **选择待分析音频**：可以选择单个文件或包含多个音频文件的文件夹
3. **选择输出文件夹**（可选）：用于保存对齐后的音频文件
4. **设置分析参数**：
   - 对齐算法：互相关或DTW
   - 文件类型筛选
5. **开始分析**：点击"开始分析"按钮
6. **查看结果**：
   - 实时查看波形图和频谱图
   - 查看质量指标（SNR、RMS等）
   - 在文件列表中切换查看不同文件的分析结果

## 质量指标说明

- **SNR (信噪比)**：衡量信号与噪声的比例，数值越高表示质量越好
- **RMS值**：均方根值，表示音频信号的强度
- **对齐偏移量**：音频对齐时的时间偏移量
- **音频长度**：处理后的音频时长

## 支持的文件格式

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- AIFF (.aiff)
- OGG (.ogg)

## 技术特点

- **多线程处理**：避免界面卡顿
- **实时更新**：处理过程中实时显示结果
- **错误处理**：完善的错误处理和用户提示
- **内存优化**：高效的内存使用和文件处理
- **中文字体支持**：自动检测并设置合适的中文字体，支持Windows、macOS、Linux系统

## 与原始命令行工具的区别

| 特性 | 原始命令行工具 | GUI工具 |
|------|----------------|---------|
| 界面 | 命令行 | 图形界面 |
| 可视化 | 静态图表 | 实时动态图表 |
| 批量处理 | 需要脚本 | 内置支持 |
| 用户体验 | 技术用户 | 普通用户友好 |
| 实时反馈 | 无 | 实时进度和日志 |
| 交互性 | 低 | 高 |

## 故障排除

### 常见问题

1. **导入错误**：确保已安装所有依赖包
2. **音频格式不支持**：检查文件格式是否在支持列表中
3. **内存不足**：处理大文件时可能需要更多内存
4. **采样率不匹配**：工具会自动重采样，但可能影响质量

### 性能优化

- 对于大文件，建议使用互相关算法（更快）
- 对于复杂音频，建议使用DTW算法（更准确）
- 批量处理时建议分批进行，避免内存溢出 