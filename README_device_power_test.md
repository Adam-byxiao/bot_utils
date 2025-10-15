# 设备上下电压测试工具

## 功能概述

这个工具通过以下方式实现设备的自动化上下电压测试：

1. **ADB控制手机**：通过USB调试连接Android手机
2. **向日葵软件控制**：远程控制手机上的向日葵软件来操作可控开关插座
3. **SSH远程检查**：连接到目标设备检查`vibe_dsp_server`服务状态
4. **错误统计**：统计DSP服务未启动和连接错误的情况

## 系统要求

### 必需软件
1. **ADB工具**：Android Debug Bridge
   - Windows: 下载Android SDK Platform Tools
   - Linux: `sudo apt-get install android-tools-adb`
   - macOS: `brew install android-platform-tools`

2. **Python依赖**
   ```bash
   pip install paramiko
   ```

### 硬件要求
1. **Android手机**：支持USB调试
2. **可控开关插座**：通过向日葵软件控制
3. **目标设备**：运行Linux系统，支持SSH连接

## 安装步骤

### 1. 安装ADB
#### Windows
1. 下载 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
2. 解压到某个目录（如 `C:\adb`）
3. 将 `C:\adb` 添加到系统PATH环境变量
4. 验证安装：打开命令提示符，输入 `adb version`

#### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install android-tools-adb

# macOS
brew install android-platform-tools
```

### 2. 配置Android手机
1. 启用开发者选项：
   - 设置 → 关于手机 → 连续点击"版本号"7次
2. 启用USB调试：
   - 设置 → 开发者选项 → USB调试
3. 连接手机到电脑
4. 在手机上允许USB调试
5. 验证连接：`adb devices`

### 3. 配置向日葵软件
1. 在手机上安装向日葵软件
2. 配置可控开关插座
3. 记录开关按钮和确定按钮的屏幕坐标

## 配置说明

### 1. 修改配置文件
编辑 `device_power_test_config.py`：

```python
# SSH连接配置
SSH_CONFIG = {
    'host': '192.168.20.195',  # 目标设备IP
    'username': 'root',        # SSH用户名
    'password': 'your_password', # SSH密码
    'port': 22
}

# 向日葵软件界面坐标
SUNFLOWER_CONFIG = {
    'switch_button_coords': (540, 1200),  # 根据实际界面调整
    'confirm_button_coords': (540, 1400), # 根据实际界面调整
}
```

### 2. 获取屏幕坐标
使用以下命令获取屏幕分辨率：
```bash
adb shell wm size
```

然后使用以下命令获取点击坐标：
```bash
adb shell getevent -l
```

## 使用方法

### 基本使用
```bash
python device_power_test.py
```

### 自定义参数
修改 `device_power_test_config.py` 中的配置参数：

- `power_on_wait_time`: 上电后等待时间（默认20秒）
- `power_off_wait_time`: 下电后等待时间（默认10秒）
- `total_duration_minutes`: 总测试时间（默认1分钟）

## 测试流程

1. **初始化**：检查ADB安装，连接Android设备
2. **上电**：通过向日葵软件控制插座上电
3. **等待**：等待20秒让设备启动
4. **检查服务**：SSH连接检查`vibe_dsp_server`服务
5. **下电**：通过向日葵软件控制插座下电
6. **统计**：记录错误并生成报告

## 错误处理

### 常见错误及解决方案

1. **ADB未安装**
   ```
   错误：ADB未安装，请先安装Android SDK或ADB工具
   解决：按照安装步骤安装ADB
   ```

2. **设备未连接**
   ```
   错误：未发现已连接的Android设备
   解决：检查USB连接，确保USB调试已启用
   ```

3. **SSH连接失败**
   ```
   错误：SSH连接失败
   解决：检查网络连接，验证IP地址和凭据
   ```

4. **坐标点击失败**
   ```
   错误：点击坐标失败
   解决：重新获取并调整向日葵软件界面坐标
   ```

## 日志文件

测试过程中会生成以下日志文件：
- `device_power_test.log`: 详细测试日志
- 控制台输出：实时测试状态

## 测试报告

测试结束后会显示统计信息：
```
==================================================
测试总结
==================================================
总测试次数: 5
DSP服务错误次数: 1
连接错误次数: 0
成功率: 80.00%
==================================================
```

## 故障排除

### 1. 坐标不准确
- 使用 `adb shell getevent -l` 获取精确坐标
- 考虑不同屏幕分辨率的适配

### 2. 网络连接问题
- 检查目标设备IP地址是否正确
- 验证SSH服务是否正常运行
- 检查防火墙设置

### 3. 设备启动时间
- 根据实际设备调整 `power_on_wait_time`
- 考虑设备硬件性能差异

## 注意事项

1. **安全**：确保SSH密码安全，避免明文存储
2. **稳定性**：测试前确保网络连接稳定
3. **备份**：重要数据请提前备份
4. **监控**：测试过程中注意观察设备状态

## 技术支持

如遇到问题，请检查：
1. 日志文件中的详细错误信息
2. 网络连接状态
3. 设备配置是否正确
4. ADB和SSH连接是否正常
