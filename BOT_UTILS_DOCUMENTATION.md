# Bot Utils 工具包文档

## 概述

Bot Utils 是一个综合性的机器人测试和分析工具包，专门用于音频、视频、网络监控和设备性能测试。该工具包提供了完整的测试框架和分析工具，支持多种测试场景和数据格式。

## 📁 项目结构

```
bot_utils/
├── 📊 音频测试模块
│   ├── audio_script/           # 音频分析脚本
│   ├── AudioFile/             # 音频文件存储
│   ├── noise_generator/       # 噪声生成器
│   └── result/               # 测试结果
├── 📷 视频测试模块
│   ├── camera_script/         # 相机测试脚本
│   └── image/                # 图像文件
├── 🌐 网络监控模块
│   └── network_monitor/       # Chrome网络监控工具
├── 🔧 设备测试模块
│   ├── bot_tests/            # 各种设备测试
│   └── motor_test_gui.py     # 电机测试GUI
├── ⚡ 电源测试模块
│   └── device_power_test.py  # 设备功耗测试
└── 🎯 主要工具
    ├── bot_tool_framework.py # 测试框架
    └── bot_test_gui.py      # 主GUI界面
```

## 🎵 音频测试模块

### 核心功能
- **语音质量分析**: PESQ、STOI评分
- **音频对齐**: 自动音频同步
- **噪声分析**: 环境噪声检测和分析
- **DOA分析**: 声源定位分析
- **信号处理**: 音频格式转换、通道分离

### 主要文件
- `audio_script/UnifiedSpeechQualityApp.py` - 统一语音质量分析应用
- `audio_script/SpeechQualityAnalyzer.py` - 语音质量分析器
- `audio_script/AudioAligner.py` - 音频对齐工具
- `audio_script/ReadDOA.py` - DOA数据读取
- `noise_generator/noise_utils.py` - 噪声生成工具

### 使用方法
```bash
# 运行语音质量分析GUI
python run_speech_quality_app.py

# 运行PESQ分析GUI
python audio_script/Pesq_gui.py

# 音频对齐
python audio_script/AudioAligner.py
```

### 支持的音频格式
- WAV, MP3, MP4, AVI
- 支持多通道音频处理
- 自动格式转换

## 📷 视频/图像测试模块

### 核心功能
- **图像质量分析**: SNR、SFR、对比度
- **色彩分析**: 色彩饱和度、色彩噪声
- **噪声检测**: 总噪声、紫边检测
- **HDR分析**: 高动态范围图像分析
- **色差分析**: 色彩偏差检测

### 主要文件
- `camera_script/SNR.py` - 信噪比分析
- `camera_script/SFR.py` - 空间频率响应
- `camera_script/ColorSaturation.py` - 色彩饱和度
- `camera_script/ChromaticAberration.py` - 色差分析
- `camera_script/hdr.py` - HDR分析

### 使用方法
```python
# SNR分析示例
from camera_script.SNR import calculate_snr
snr_value = calculate_snr(image_path)

# SFR分析示例
from camera_script.SFR import calculate_sfr
sfr_result = calculate_sfr(image_path, roi)
```

## 🌐 网络监控模块

### 核心功能
- **实时网络监控**: Chrome DevTools Protocol
- **数据标准化**: 统一数据格式
- **智能过滤**: 多种过滤规则
- **多格式导出**: JSON、CSV、Excel、TXT
- **统计报告**: 自动生成分析报告

### 主要文件
- `network_monitor/main.py` - 主程序入口
- `network_monitor/chrome_network_listener.py` - Chrome监听器
- `network_monitor/data_standardizer.py` - 数据标准化
- `network_monitor/data_exporter.py` - 数据导出

### 使用方法
```bash
# 基本网络监控
cd network_monitor
python main.py -d 60

# 使用自定义配置
python main.py -c config.json

# 运行示例
python examples.py
```

### 配置选项
- Chrome连接设置
- 过滤器规则配置
- 导出格式选择
- 输出目录设置

## 🔧 设备测试模块

### 核心功能
- **电机测试**: 电机控制和性能测试
- **网络测试**: 网络连接和性能
- **热成像测试**: 温度监控
- **DOA测试**: 声源定位测试
- **媒体测试**: 音视频设备测试

### 主要文件
- `bot_tests/motor_test.py` - 电机测试
- `bot_tests/network_test.py` - 网络测试
- `bot_tests/thermal_test.py` - 热成像测试
- `bot_tests/doa_test.py` - DOA测试
- `bot_tests/media_test.py` - 媒体测试

### 使用方法
```bash
# 运行电机测试GUI
python motor_test_gui.py

# 运行主测试GUI
python bot_test_gui.py
```

## ⚡ 电源测试模块

### 核心功能
- **功耗监控**: 实时功耗测量
- **电池测试**: 电池性能分析
- **电源效率**: 电源转换效率
- **待机功耗**: 待机状态功耗测试

### 主要文件
- `device_power_test.py` - 设备功耗测试
- `device_power_test_config.py` - 功耗测试配置
- `run_power_test.py` - 功耗测试运行器

### 使用方法
```bash
# Windows
run_power_test.bat

# Linux/macOS
./run_power_test.sh

# Python直接运行
python run_power_test.py
```

## 🎯 主要工具和框架

### Bot Tool Framework
核心测试框架，提供统一的测试接口和数据管理。

**主要功能**:
- 测试用例管理
- 结果数据存储
- 测试报告生成
- 配置管理

### GUI界面
- `bot_test_gui.py` - 主测试界面
- `motor_test_gui.py` - 电机测试界面
- `audio_script/Pesq_gui.py` - PESQ分析界面

## 📋 安装和依赖

### 系统要求
- Python 3.8+
- Windows/Linux/macOS
- Chrome浏览器（网络监控功能）

### 安装依赖
```bash
# 音频处理依赖
pip install librosa soundfile pesq pystoi

# 图像处理依赖
pip install opencv-python pillow numpy matplotlib

# 网络监控依赖
pip install -r network_monitor/requirements.txt

# GUI依赖
pip install tkinter PyQt5

# 数据处理依赖
pip install pandas openpyxl xlsxwriter
```

## 🚀 快速开始

### 1. 音频质量测试
```bash
# 启动语音质量分析应用
python run_speech_quality_app.py

# 选择参考音频和测试音频
# 选择分析方法（PESQ/STOI）
# 查看分析结果
```

### 2. 图像质量测试
```python
# 导入测试模块
from camera_script import SNR, SFR, ColorSaturation

# 进行SNR分析
snr_result = SNR.calculate_snr('test_image.jpg')
print(f"SNR: {snr_result}")
```

### 3. 网络监控
```bash
# 启动Chrome调试模式
chrome.exe --remote-debugging-port=9222

# 开始网络监控
cd network_monitor
python main.py -d 60
```

### 4. 设备测试
```bash
# 启动主测试界面
python bot_test_gui.py

# 选择测试项目
# 配置测试参数
# 运行测试并查看结果
```

## 📊 输出格式和结果

### 音频测试结果
- **PESQ分数**: 1.0-4.5 (越高越好)
- **STOI分数**: 0.0-1.0 (越高越好)
- **Excel报告**: 详细分析数据
- **可视化图表**: 频谱分析、波形对比

### 图像测试结果
- **SNR值**: 信噪比数值
- **SFR曲线**: 空间频率响应曲线
- **色彩分析**: RGB通道分析
- **噪声地图**: 噪声分布可视化

### 网络监控结果
- **JSON数据**: 完整的网络事务数据
- **CSV表格**: 扁平化的数据表
- **Excel工作簿**: 多工作表分析
- **摘要报告**: 统计信息和性能分析

### 设备测试结果
- **性能指标**: 各项设备性能数据
- **测试日志**: 详细的测试过程记录
- **图表报告**: 可视化的测试结果

## 🔧 配置和自定义

### 音频测试配置
- 采样率设置
- 分析窗口大小
- 噪声阈值
- 输出格式选择

### 图像测试配置
- ROI区域设置
- 分析参数调整
- 色彩空间选择
- 输出精度设置

### 网络监控配置
```json
{
  "chrome_port": 9222,
  "filters": {
    "exclude_static_resources": true,
    "api_only": false
  },
  "export": {
    "formats": ["json", "csv", "excel"]
  }
}
```

## 🐛 故障排除

### 常见问题

1. **音频文件无法读取**
   - 检查文件格式是否支持
   - 确认文件路径正确
   - 安装必要的音频编解码器

2. **图像分析失败**
   - 检查图像文件完整性
   - 确认ROI区域设置正确
   - 检查内存是否充足

3. **网络监控连接失败**
   - 确认Chrome已启动调试模式
   - 检查端口9222是否被占用
   - 验证防火墙设置

4. **设备测试无响应**
   - 检查设备连接状态
   - 确认驱动程序已安装
   - 检查权限设置

### 调试模式
```bash
# 启用详细日志
python script_name.py --verbose

# 查看错误日志
tail -f error.log
```

## 📈 性能优化建议

1. **音频处理优化**
   - 使用适当的采样率
   - 批量处理多个文件
   - 启用多线程处理

2. **图像处理优化**
   - 调整图像分辨率
   - 使用ROI减少计算量
   - 启用GPU加速（如可用）

3. **网络监控优化**
   - 使用过滤器减少数据量
   - 适当设置监控时间
   - 定期清理输出文件

## 📝 开发和扩展

### 添加新的测试模块
1. 在相应目录创建新的Python文件
2. 继承基础测试类
3. 实现必要的测试方法
4. 更新GUI界面（如需要）

### 自定义分析算法
1. 在相应模块中添加新函数
2. 遵循现有的接口规范
3. 添加必要的文档和测试
4. 更新配置文件

## 📄 许可证和版权

本工具包遵循MIT许可证，允许自由使用、修改和分发。

## 🤝 贡献和支持

欢迎提交Issue和Pull Request来改进这个工具包。如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件反馈
- 参与代码贡献

## 📚 参考资料

- [PESQ标准文档](https://www.itu.int/rec/T-REC-P.862)
- [STOI算法论文](https://ieeexplore.ieee.org/document/5495701)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [OpenCV文档](https://docs.opencv.org/)

---

**最后更新**: 2024年1月
**版本**: 1.0.0
**维护者**: Bot Utils开发团队