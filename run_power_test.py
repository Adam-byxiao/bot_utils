#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备上下电压测试快速启动脚本
"""

import sys
import os
import argparse
from device_power_test import DevicePowerTest
from device_power_test_config import SSH_CONFIG, TEST_CONFIG

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='设备上下电压测试工具')
    parser.add_argument('--host', type=str, default=SSH_CONFIG['host'],
                       help=f'SSH主机地址 (默认: {SSH_CONFIG["host"]})')
    parser.add_argument('--username', type=str, default=SSH_CONFIG['username'],
                       help=f'SSH用户名 (默认: {SSH_CONFIG["username"]})')
    parser.add_argument('--password', type=str, default=SSH_CONFIG['password'],
                       help='SSH密码')
    parser.add_argument('--port', type=int, default=SSH_CONFIG['port'],
                       help=f'SSH端口 (默认: {SSH_CONFIG["port"]})')
    parser.add_argument('--duration', type=int, default=TEST_CONFIG['total_duration_minutes'],
                       help=f'测试持续时间(分钟) (默认: {TEST_CONFIG["total_duration_minutes"]})')
    parser.add_argument('--power-on-wait', type=int, default=TEST_CONFIG['power_on_wait_time'],
                       help=f'上电后等待时间(秒) (默认: {TEST_CONFIG["power_on_wait_time"]})')
    parser.add_argument('--power-off-wait', type=int, default=TEST_CONFIG['power_off_wait_time'],
                       help=f'下电后等待时间(秒) (默认: {TEST_CONFIG["power_off_wait_time"]})')
    parser.add_argument('--test-interval', type=int, default=TEST_CONFIG['test_interval'],
                       help=f'测试间隔时间(秒) (默认: {TEST_CONFIG["test_interval"]})')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，不执行实际测试')
    
    args = parser.parse_args()
    
    # 显示配置信息
    print("=" * 60)
    print("设备上下电压测试工具")
    print("=" * 60)
    print(f"SSH主机: {args.host}:{args.port}")
    print(f"SSH用户: {args.username}")
    print(f"测试时长: {args.duration} 分钟")
    print(f"上电等待: {args.power_on_wait} 秒")
    print(f"下电等待: {args.power_off_wait} 秒")
    print(f"测试间隔: {args.test_interval} 秒")
    print("=" * 60)
    
    if args.dry_run:
        print("试运行模式 - 不会执行实际测试")
        return
    
    # 检查密码
    if args.password == SSH_CONFIG['password']:
        print("警告: 使用默认密码，建议通过 --password 参数指定实际密码")
        password = input("请输入SSH密码: ").strip()
        if not password:
            print("未输入密码，使用默认密码")
            password = args.password
    else:
        password = args.password
    
    # 确认开始测试
    confirm = input("\n确认开始测试? (y/n): ").lower().strip()
    if confirm != 'y':
        print("测试已取消")
        return
    
    try:
        # 创建测试实例
        test = DevicePowerTest(args.host, args.username, password)
        
        # 初始化
        if not test.setup():
            print("初始化失败，退出程序")
            return
        
        # 运行测试
        test.run_test_cycle(duration_minutes=args.duration)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试执行异常: {e}")
    finally:
        print("测试结束")

if __name__ == "__main__":
    main()
