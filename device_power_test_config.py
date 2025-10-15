# -*- coding: utf-8 -*-
"""
设备上下电压测试配置文件
"""

# SSH连接配置
SSH_CONFIG = {
    'host': '192.168.20.195',
    'username': 'root',  # 请根据实际情况修改
    'password': 'password',  # 请根据实际情况修改
    'port': 22
}

# 向日葵软件界面坐标配置
# 注意：这些坐标需要根据实际手机屏幕分辨率和向日葵软件界面调整
SUNFLOWER_CONFIG = {
    'switch_button_coords': (540, 1200),  # 开关按钮坐标 (x, y)
    'confirm_button_coords': (540, 1400),  # 确定按钮坐标 (x, y)
}

# 测试时间配置
TEST_CONFIG = {
    'power_on_wait_time': 20,  # 上电后等待时间（秒）
    'power_off_wait_time': 10,  # 下电后等待时间（秒）
    'test_interval': 5,  # 测试间隔时间（秒）
    'total_duration_minutes': 1,  # 总测试持续时间（分钟）
    'tap_delay': 1,  # 点击操作间隔时间（秒）
}

# 日志配置
LOG_CONFIG = {
    'log_file': 'device_power_test.log',
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'console_output': True,  # 是否同时输出到控制台
}

# ADB配置
ADB_CONFIG = {
    'timeout': 10,  # ADB命令超时时间（秒）
    'retry_count': 3,  # 重试次数
}

# SSH命令配置
SSH_COMMANDS = {
    'check_dsp_server': 'top -n 1 -b | grep vibe_dsp_server',
    'alternative_check': 'ps aux | grep vibe_dsp_server | grep -v grep',  # 备用检查命令
}
