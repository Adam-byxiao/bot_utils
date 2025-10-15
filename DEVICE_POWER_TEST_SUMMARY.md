# 设备上下电压测试工具 - 项目总结

## 项目概述

本项目实现了一个完整的设备上下电压测试自动化工具，通过ADB控制Android手机上的向日葵软件来操作可控开关插座，并通过SSH远程检查目标设备的服务状态。

## 文件结构

```
bot_utils/
├── device_power_test.py              # 主测试脚本
├── device_power_test_config.py       # 配置文件
├── get_screen_coordinates.py         # 坐标获取工具
├── run_power_test.py                 # Python启动脚本
├── run_power_test.bat                # Windows批处理脚本
├── run_power_test.sh                 # Linux/macOS shell脚本
├── README_device_power_test.md       # 详细使用说明
└── DEVICE_POWER_TEST_SUMMARY.md      # 项目总结（本文件）
```

## 核心功能

### 1. ADB控制模块 (`ADBController`)
- 检查ADB工具安装状态
- 连接Android设备
- 执行屏幕点击操作
- 获取屏幕分辨率

### 2. 向日葵软件控制 (`SunflowerController`)
- 上电操作（点击开关按钮 + 确定按钮）
- 下电操作（点击开关按钮 + 确定按钮）
- 可配置的界面坐标

### 3. SSH远程控制 (`SSHController`)
- 建立SSH连接
- 检查`vibe_dsp_server`服务状态
- 错误处理和重连机制

### 4. 测试主控制器 (`DevicePowerTest`)
- 完整的测试流程管理
- 错误统计和报告
- 可配置的测试参数

## 测试流程

1. **初始化阶段**
   - 检查ADB安装
   - 连接Android设备
   - 获取屏幕分辨率

2. **测试循环**
   - 上电操作（向日葵软件控制）
   - 等待20秒设备启动
   - SSH连接检查服务状态
   - 下电操作
   - 等待10秒设备关闭
   - 统计错误信息

3. **报告生成**
   - 总测试次数
   - DSP服务错误次数
   - 连接错误次数
   - 成功率统计

## 配置参数

### SSH配置
```python
SSH_CONFIG = {
    'host': '192.168.20.195',
    'username': 'root',
    'password': 'password',
    'port': 22
}
```

### 向日葵软件坐标
```python
SUNFLOWER_CONFIG = {
    'switch_button_coords': (540, 1200),
    'confirm_button_coords': (540, 1400),
}
```

### 测试时间配置
```python
TEST_CONFIG = {
    'power_on_wait_time': 20,      # 上电后等待时间
    'power_off_wait_time': 10,     # 下电后等待时间
    'test_interval': 5,            # 测试间隔
    'total_duration_minutes': 1,   # 总测试时长
}
```

## 使用方法

### 快速启动
```bash
# Windows
run_power_test.bat

# Linux/macOS
./run_power_test.sh

# Python直接运行
python run_power_test.py
```

### 命令行参数
```bash
python run_power_test.py --host 192.168.20.195 --duration 2 --dry-run
```

### 坐标获取
```bash
python get_screen_coordinates.py
```

## 错误处理

### 常见错误类型
1. **ADB相关错误**
   - ADB未安装
   - 设备未连接
   - USB调试未启用

2. **SSH相关错误**
   - 网络连接失败
   - 认证失败
   - 服务检查失败

3. **向日葵软件错误**
   - 坐标不准确
   - 界面变化
   - 点击失败

### 错误统计
- 区分DSP服务错误和连接错误
- 动态IP变化不影响错误统计
- 详细的日志记录

## 日志系统

### 日志文件
- `device_power_test.log`: 详细测试日志
- 控制台实时输出
- 错误级别分类

### 日志内容
- 测试开始/结束时间
- 每个操作的状态
- 错误详情和堆栈信息
- 统计报告

## 扩展性

### 可扩展的功能
1. **GUI界面**: 可以添加图形用户界面
2. **多设备支持**: 支持同时测试多个设备
3. **更多服务检查**: 扩展其他服务的检查
4. **报告导出**: 支持Excel、PDF等格式
5. **邮件通知**: 测试结果邮件通知

### 模块化设计
- 每个功能模块独立
- 易于维护和扩展
- 配置与代码分离

## 安全考虑

### 密码安全
- 避免明文存储密码
- 支持环境变量配置
- 运行时密码输入

### 网络安全
- SSH连接加密
- 超时机制
- 错误重试限制

## 性能优化

### 时间优化
- 可配置的等待时间
- 并行操作支持
- 快速失败机制

### 资源优化
- 连接复用
- 内存管理
- 异常处理

## 测试建议

### 首次使用
1. 先运行坐标获取工具确定界面坐标
2. 使用`--dry-run`模式测试配置
3. 短时间测试验证功能
4. 逐步增加测试时长

### 生产环境
1. 确保网络稳定性
2. 定期检查日志文件
3. 监控设备状态
4. 备份重要配置

## 技术支持

### 故障排除
1. 检查日志文件
2. 验证网络连接
3. 确认设备配置
4. 测试ADB连接

### 常见问题
- 坐标不准确：使用坐标获取工具重新校准
- 连接失败：检查网络和SSH配置
- 服务检查失败：验证目标设备状态

## 版本信息

- **版本**: 1.0.0
- **Python要求**: 3.6+
- **依赖包**: paramiko
- **支持平台**: Windows, Linux, macOS
- **最后更新**: 2024年

## 许可证

本项目基于MIT许可证开源，可自由使用和修改。
