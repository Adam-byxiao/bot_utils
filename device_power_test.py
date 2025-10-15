#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备上下电压测试脚本
通过ADB控制手机向日葵软件来操作可控开关插座
通过SSH检查目标设备的vibe_dsp_server服务状态
"""

import subprocess
import time
import paramiko
import logging
from typing import Tuple, Optional
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('device_power_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ADBController:
    """ADB控制器，用于连接和控制Android设备"""
    
    def __init__(self):
        self.device_connected = False
        
    def check_adb_installed(self) -> bool:
        """检查ADB是否已安装"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("ADB已安装")
                return True
        except FileNotFoundError:
            logger.error("ADB未安装，请先安装Android SDK或ADB工具")
        except subprocess.TimeoutExpired:
            logger.error("ADB命令执行超时")
        return False
    
    def connect_device(self) -> bool:
        """连接Android设备"""
        try:
            # 检查设备连接状态
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                devices = [line.split('\t')[0] for line in lines if line.strip() and '\tdevice' in line]
                
                if devices:
                    logger.info(f"发现设备: {devices[0]}")
                    self.device_connected = True
                    return True
                else:
                    logger.error("未发现已连接的Android设备")
                    return False
        except Exception as e:
            logger.error(f"连接设备失败: {e}")
            return False
    
    def tap_screen(self, x: int, y: int) -> bool:
        """点击屏幕指定坐标"""
        if not self.device_connected:
            logger.error("设备未连接")
            return False
            
        try:
            result = subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"点击坐标 ({x}, {y})")
                return True
            else:
                logger.error(f"点击失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"点击操作异常: {e}")
            return False
    
    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
        """获取屏幕分辨率"""
        if not self.device_connected:
            return None
            
        try:
            result = subprocess.run(['adb', 'shell', 'wm', 'size'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # 输出格式: Physical size: 1080x2400
                size_str = result.stdout.strip().split(': ')[1]
                width, height = map(int, size_str.split('x'))
                logger.info(f"屏幕分辨率: {width}x{height}")
                return width, height
        except Exception as e:
            logger.error(f"获取屏幕分辨率失败: {e}")
        return None

class SunflowerController:
    """向日葵软件控制器"""
    
    def __init__(self, adb_controller: ADBController):
        self.adb = adb_controller
        # 这些坐标需要根据实际向日葵软件界面调整
        self.switch_button_coords = (540, 1200)  # 开关按钮坐标
        self.confirm_button_coords = (540, 1400)  # 确定按钮坐标
        
    def power_on(self) -> bool:
        """上电操作"""
        logger.info("开始上电操作...")
        
        # 点击开关按钮
        if not self.adb.tap_screen(*self.switch_button_coords):
            logger.error("点击开关按钮失败")
            return False
            
        time.sleep(1)  # 等待界面响应
        
        # 点击确定按钮
        if not self.adb.tap_screen(*self.confirm_button_coords):
            logger.error("点击确定按钮失败")
            return False
            
        logger.info("上电操作完成")
        return True
    
    def power_off(self) -> bool:
        """下电操作"""
        logger.info("开始下电操作...")
        
        # 点击开关按钮
        if not self.adb.tap_screen(*self.switch_button_coords):
            logger.error("点击开关按钮失败")
            return False
            
        time.sleep(1)  # 等待界面响应
        
        # 点击确定按钮
        if not self.adb.tap_screen(*self.confirm_button_coords):
            logger.error("点击确定按钮失败")
            return False
            
        logger.info("下电操作完成")
        return True

class SSHController:
    """SSH远程控制器"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        
    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host, 
                self.port, 
                self.username, 
                self.password, 
                timeout=30
            )
            logger.info(f"SSH连接成功: {self.host}")
            return True
        except paramiko.AuthenticationException:
            logger.error("SSH认证失败")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH连接异常: {e}")
            return False
        except Exception as e:
            logger.error(f"SSH连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("SSH连接已断开")
    
    def check_dsp_server(self) -> Tuple[bool, str]:
        """检查vibe_dsp_server服务状态"""
        if not self.client:
            logger.error("SSH未连接")
            return False, "SSH未连接"
            
        try:
            # 使用top命令检查进程
            stdin, stdout, stderr = self.client.exec_command("top -n 1 -b | grep vibe_dsp_server")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                logger.warning(f"命令执行警告: {error}")
            
            if output:
                logger.info("vibe_dsp_server服务正在运行")
                return True, output
            else:
                logger.warning("vibe_dsp_server服务未运行")
                return False, "服务未运行"
                
        except Exception as e:
            logger.error(f"检查服务状态失败: {e}")
            return False, f"检查失败: {e}"

class DevicePowerTest:
    """设备上下电压测试主控制器"""
    
    def __init__(self, ssh_host: str, ssh_username: str, ssh_password: str):
        self.adb_controller = ADBController()
        self.sunflower_controller = SunflowerController(self.adb_controller)
        self.ssh_controller = SSHController(ssh_host, ssh_username, ssh_password)
        
        # 测试统计
        self.total_tests = 0
        self.dsp_server_errors = 0
        self.connection_errors = 0
        
    def setup(self) -> bool:
        """初始化设置"""
        logger.info("开始初始化设备...")
        
        # 检查ADB
        if not self.adb_controller.check_adb_installed():
            return False
        
        # 连接Android设备
        if not self.adb_controller.connect_device():
            return False
        
        # 获取屏幕分辨率（可选，用于调试坐标）
        resolution = self.adb_controller.get_screen_resolution()
        if resolution:
            logger.info(f"设备屏幕分辨率: {resolution[0]}x{resolution[1]}")
        
        logger.info("设备初始化完成")
        return True
    
    def run_single_test(self) -> bool:
        """执行单次测试"""
        self.total_tests += 1
        logger.info(f"开始第 {self.total_tests} 次测试")
        
        # 1. 上电
        if not self.sunflower_controller.power_on():
            logger.error("上电失败")
            return False
        
        # 2. 等待20秒
        logger.info("等待20秒让设备启动...")
        time.sleep(20)
        
        # 3. SSH连接检查服务
        if not self.ssh_controller.connect():
            logger.error("SSH连接失败")
            self.connection_errors += 1
            return False
        
        try:
            service_running, message = self.ssh_controller.check_dsp_server()
            if not service_running:
                logger.error("没有开启dspserver")
                self.dsp_server_errors += 1
        finally:
            self.ssh_controller.disconnect()
        
        # 4. 下电
        if not self.sunflower_controller.power_off():
            logger.error("下电失败")
            return False
        
        # 5. 等待设备完全关闭
        logger.info("等待设备完全关闭...")
        time.sleep(10)
        
        logger.info(f"第 {self.total_tests} 次测试完成")
        return True
    
    def run_test_cycle(self, duration_minutes: int = 1):
        """运行测试循环"""
        logger.info(f"开始测试循环，持续 {duration_minutes} 分钟")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                self.run_single_test()
                # 测试间隔
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("用户中断测试")
                break
            except Exception as e:
                logger.error(f"测试过程中发生异常: {e}")
                continue
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        logger.info("=" * 50)
        logger.info("测试总结")
        logger.info("=" * 50)
        logger.info(f"总测试次数: {self.total_tests}")
        logger.info(f"DSP服务错误次数: {self.dsp_server_errors}")
        logger.info(f"连接错误次数: {self.connection_errors}")
        logger.info(f"成功率: {((self.total_tests - self.dsp_server_errors - self.connection_errors) / self.total_tests * 100):.2f}%" if self.total_tests > 0 else "0%")
        logger.info("=" * 50)

def main():
    """主函数"""
    # 配置参数
    SSH_HOST = "192.168.20.195"
    SSH_USERNAME = "root"  # 需要根据实际情况修改
    SSH_PASSWORD = "password"  # 需要根据实际情况修改
    
    # 创建测试实例
    test = DevicePowerTest(SSH_HOST, SSH_USERNAME, SSH_PASSWORD)
    
    # 初始化
    if not test.setup():
        logger.error("初始化失败，退出程序")
        return
    
    try:
        # 运行测试循环（1分钟）
        test.run_test_cycle(duration_minutes=1)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()
