# bot_utils

## 项目简介

`bot_utils` 是一个多功能的自动化测试与分析工具集，面向音频、图像、摄像头、硬件bot等多领域的质量评测和信号处理。项目包含丰富的脚本、专业的图形界面和高度可扩展的自动化测试框架，支持音频质量分析（如 PESQ、SNR、RMS、STOI）、音频对齐、图像噪声/色差/对比度/动态范围分析，以及硬件bot的批量用例自动化测试。

---

## 目录结构

```
bot_utils/
├── audio_script/         # 语音/音频质量分析与工具（主GUI、PESQ、SNR、对齐、STOI等）
├── camera_script/        # 摄像头/图像质量分析（噪声、色差、对比度、SFR等）
├── bot_tests/            # 统一的bot自动化测试用例（Audio、Camera、Motor等）
│   ├── audio_test.py
│   ├── camera_test.py
│   ├── media_test.py
│   ├── motor_test.py
│   ├── motor_controller.py
│   ├── doa_test.py
│   ├── tracking_test.py
│   ├── network_test.py


│   ├── thermal_test.py
│   └── ...
├── AudioFile/            # 各类音频测试文件、结果、原始/对齐/会议录音等
├── image/                # 图像测试样本、分析用图片
├── test/                 # 测试用图片、结果可视化等
├── AudioBox.py           # 音频工具箱GUI（集成对齐、格式转换等）
├── bot_tool_framework.py # 统一的bot测试后端框架（设备管理、用例注册、批量参数等）
├── bot_test_gui.py       # 整合型bot自动化测试GUI（支持批量用例、参数模板、日志输出）
├── motor_test_gui.py     # Motor测试专用GUI（可选）
├── bot_tool.py           # 早期硬件/电机等bot自动化测试入口
├── ImageTest.py          # 图像测试GUI
├── NoiseTest.py          # 时域噪声分析GUI
├── run_speech_quality_app.py # 一键启动语音质量分析主界面的脚本
├── README.md             # 项目说明文档
└── ...
```

---

## 主要功能模块

### 1. 语音/音频质量分析（audio_script/）

- **UnifiedSpeechQualityApp.py**  
  现代化 wxPython 图形界面，支持单文件和批量音频质量分析，PESQ、SNR、RMS、对齐偏移量等多指标，支持结果可视化、Excel 导出、直方图分析。
- **audio_analysis_utils.py**  
  封装音频对齐、SNR、RMS、PESQ等核心算法，供主界面和批量分析复用。
- **AudioAligner.py / Video2Audio.py / record_inout.py**  
  音频对齐、视频转音频、录音等辅助工具。

### 2. 图像/摄像头质量分析（camera_script/）

- **CheckNoise.py / ColorNoise.py / SNR.py / TotalNoise.py**  
  图像噪声、色彩噪声、信噪比、动态范围等分析。
- **ChromaticAberration.py / PurpleDetection.py**  
  横向色差、紫边检测。
- **Contrast.py / SFR.py / hdr.py**  
  对比度、空间频率响应、动态范围等专业图像质量指标。

### 3. bot自动化测试框架与用例（bot_tests/ + bot_tool_framework.py）

- **bot_tool_framework.py**  
  统一的后端测试框架，支持设备管理、用例注册、批量参数、日志等。
- **bot_tests/**  
  各类自动化测试用例（如 AudioTest、CameraTest、MotorTest、DOATest、TrackingTest、NetworkTest、ThermalTest），每个用例支持参数模板和批量执行，便于扩展和维护。
- **motor_controller.py**  
  电机控制命令生成与管理，供 MotorTest 等用例复用。

### 4. 图形界面与批量用例（GUI）

- **bot_test_gui.py**  
  整合型 bot 测试GUI，支持所有测试类型的批量用例参数配置、设备管理、日志输出，适合测试人员交互使用。
- **motor_test_gui.py**  
  Motor测试专用GUI（可选）。
- **AudioBox.py**  
  音频工具箱GUI，集成音频对齐、格式转换等功能。
- **ImageTest.py**  
  图像测试GUI，支持图像质量分析、SFR、色差、对比度等。
- **NoiseTest.py**  
  时域噪声分析GUI，支持图像噪声、色彩噪声等分析。
- **run_speech_quality_app.py**  
  语音质量分析主界面，一键启动音频质量分析GUI。

---

## 安装依赖

建议使用 Python 3.8 及以上版本。

```bash
pip install wxPython librosa matplotlib scipy pesq openpyxl paramiko pillow requests retrying
```
- Windows 下可用 pip 安装 wxPython。

---

## 运行方法

- **bot自动化测试整合GUI**  
  ```bash
  python bot_test_gui.py
  ```
- **语音质量分析主界面**  
  ```bash
  python run_speech_quality_app.py
  ```
- **图像测试主界面**  
  ```bash
  python ImageTest.py
  ```
- **音频工具箱**  
  ```bash
  python AudioBox.py
  ```
- 其他脚本可根据需要单独运行。

---

## 参考/致谢

- [PESQ ITU-T P.862 标准实现（pesq 包）](https://github.com/ludlows/python-pesq)
- [librosa: Python 音频分析库](https://librosa.org/)
- [wxPython: 跨平台GUI](https://wxpython.org/)
- [matplotlib: 科学绘图](https://matplotlib.org/)
- [paramiko: SSH 远程控制](https://www.paramiko.org/)
- [bot_acoustic_test (ShawnYang23)](https://github.com/ShawnYang23/bot_acoustic_test)

---

## 作者信息

- 作者：Adam
- 邮箱：adam@vibe.us
- 项目主页：[https://github.com/Adam-byxiao/bot_utils](https://github.com/Adam-byxiao/bot_utils)

---

如有建议或问题，欢迎 issue 或 PR！

---

你可以在 [项目主页](https://github.com/Adam-byxiao/bot_utils) 查看最新代码和文档。
