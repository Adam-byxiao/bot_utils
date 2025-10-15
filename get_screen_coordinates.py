#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕坐标获取工具
用于获取Android设备屏幕上的点击坐标，帮助配置向日葵软件的点击位置
"""

import subprocess
import time
import sys
import os

def check_adb():
    """检查ADB是否可用"""
    try:
        result = subprocess.run(['adb', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ ADB已安装")
            return True
    except FileNotFoundError:
        print("✗ ADB未安装，请先安装ADB工具")
        return False
    except Exception as e:
        print(f"✗ ADB检查失败: {e}")
        return False

def get_screen_resolution():
    """获取屏幕分辨率"""
    try:
        result = subprocess.run(['adb', 'shell', 'wm', 'size'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 输出格式: Physical size: 1080x2400
            size_str = result.stdout.strip().split(': ')[1]
            width, height = map(int, size_str.split('x'))
            print(f"屏幕分辨率: {width}x{height}")
            return width, height
    except Exception as e:
        print(f"获取屏幕分辨率失败: {e}")
        return None, None

def start_coordinate_monitor():
    """启动坐标监控"""
    print("\n=== 屏幕坐标监控模式 ===")
    print("请在手机上点击需要获取坐标的位置")
    print("程序将显示点击的坐标信息")
    print("按 Ctrl+C 退出监控模式")
    print("=" * 30)
    
    try:
        # 启动getevent命令监控触摸事件
        process = subprocess.Popen(
            ['adb', 'shell', 'getevent', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        coordinates = []
        
        while True:
            line = process.stdout.readline()
            if not line:
                break
                
            # 解析触摸事件
            if 'ABS_MT_POSITION_X' in line:
                # 提取X坐标
                try:
                    x_hex = line.split()[-1]
                    x = int(x_hex, 16)
                    coordinates.append(('x', x))
                except:
                    pass
            elif 'ABS_MT_POSITION_Y' in line:
                # 提取Y坐标
                try:
                    y_hex = line.split()[-1]
                    y = int(y_hex, 16)
                    coordinates.append(('y', y))
                    
                    # 如果同时有X和Y坐标，输出完整坐标
                    if len(coordinates) >= 2:
                        x_coord = None
                        y_coord = None
                        for coord_type, value in coordinates[-2:]:
                            if coord_type == 'x':
                                x_coord = value
                            elif coord_type == 'y':
                                y_coord = value
                        
                        if x_coord is not None and y_coord is not None:
                            print(f"点击坐标: ({x_coord}, {y_coord})")
                            coordinates = []  # 重置坐标列表
                except:
                    pass
                    
    except KeyboardInterrupt:
        print("\n监控模式已退出")
    except Exception as e:
        print(f"监控模式异常: {e}")
    finally:
        if 'process' in locals():
            process.terminate()

def test_coordinate(x, y):
    """测试指定坐标的点击"""
    try:
        print(f"测试点击坐标 ({x}, {y})...")
        result = subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ 点击成功")
            return True
        else:
            print(f"✗ 点击失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 点击异常: {e}")
        return False

def manual_input_coordinates():
    """手动输入坐标进行测试"""
    print("\n=== 手动坐标测试 ===")
    
    try:
        x = int(input("请输入X坐标: "))
        y = int(input("请输入Y坐标: "))
        
        test_coordinate(x, y)
        
        # 询问是否保存到配置文件
        save = input("\n是否保存到配置文件? (y/n): ").lower().strip()
        if save == 'y':
            save_to_config(x, y)
            
    except ValueError:
        print("坐标必须是数字")
    except KeyboardInterrupt:
        print("\n操作已取消")

def save_to_config(x, y):
    """保存坐标到配置文件"""
    config_content = f"""# -*- coding: utf-8 -*-
# 向日葵软件界面坐标配置
# 自动生成的坐标配置

SUNFLOWER_CONFIG = {{
    'switch_button_coords': ({x}, {y}),  # 开关按钮坐标
    'confirm_button_coords': ({x}, {y + 200}),  # 确定按钮坐标（Y坐标+200）
}}

# 使用说明：
# 1. 将上述配置复制到 device_power_test_config.py 中
# 2. 根据实际向日葵软件界面调整坐标
# 3. 确认按钮通常位于开关按钮下方
"""
    
    filename = f"sunflower_coords_{int(time.time())}.py"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✓ 坐标配置已保存到 {filename}")
    except Exception as e:
        print(f"✗ 保存配置失败: {e}")

def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 40)
    print("屏幕坐标获取工具")
    print("=" * 40)
    print("1. 获取屏幕分辨率")
    print("2. 启动坐标监控模式")
    print("3. 手动输入坐标测试")
    print("4. 退出")
    print("=" * 40)

def main():
    """主函数"""
    print("屏幕坐标获取工具")
    print("用于获取Android设备屏幕坐标，配置向日葵软件点击位置")
    
    # 检查ADB
    if not check_adb():
        return
    
    # 检查设备连接
    try:
        result = subprocess.run(['adb', 'devices'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line.split('\t')[0] for line in lines if line.strip() and '\tdevice' in line]
            
            if devices:
                print(f"✓ 发现设备: {devices[0]}")
            else:
                print("✗ 未发现已连接的Android设备")
                print("请确保：")
                print("1. 手机已通过USB连接到电脑")
                print("2. 已启用USB调试")
                print("3. 已在手机上允许USB调试")
                return
    except Exception as e:
        print(f"✗ 检查设备连接失败: {e}")
        return
    
    while True:
        show_menu()
        try:
            choice = input("请选择操作 (1-4): ").strip()
            
            if choice == '1':
                get_screen_resolution()
            elif choice == '2':
                start_coordinate_monitor()
            elif choice == '3':
                manual_input_coordinates()
            elif choice == '4':
                print("退出程序")
                break
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"操作异常: {e}")

if __name__ == "__main__":
    main()
