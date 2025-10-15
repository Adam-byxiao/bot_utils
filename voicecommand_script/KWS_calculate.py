#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS (Keyword Spotting) 计算工具
通过SSH连接设备，实时监控语音唤醒词识别日志
解析并记录唤醒词识别的分数和触发状态
"""

import paramiko
import logging
import time
import re
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os
import threading
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kws_calculate.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class KWSRecord:
    """KWS识别记录数据结构"""
    timestamp: str
    phrase: str
    score: float
    begin_time: int
    end_time: int
    triggered: bool
    raw_log: str

class SSHLogMonitor:
    """SSH日志监控器"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ssh_client = None
        self.connected = False
        self.monitoring = False
        
    def connect(self) -> bool:
        """连接SSH服务器"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"正在连接到 {self.host}:{self.port}")
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            self.connected = True
            logger.info("SSH连接成功")
            return True
            
        except paramiko.AuthenticationException:
            logger.error("SSH认证失败，请检查用户名和密码")
        except paramiko.SSHException as e:
            logger.error(f"SSH连接错误: {e}")
        except Exception as e:
            logger.error(f"连接失败: {e}")
            
        return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.ssh_client:
            self.ssh_client.close()
            self.connected = False
            logger.info("SSH连接已断开")
    
    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """执行SSH命令"""
        if not self.connected:
            return False, "", "SSH未连接"
            
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            return True, stdout_data, stderr_data
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return False, "", str(e)

class KWSLogParser:
    """KWS日志解析器"""
    
    def __init__(self):
        # 正则表达式模式
        self.kws_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*?'
            r'Model: (\w+) recognized phrase: (\w+), score: ([\d.]+), begin: (\d+), end: (\d+)'
        )
        
        self.save_record_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*?'
            r'OnKwsSaveRecord: (\w+)'
        )
        
        self.triggered_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*?'
            r'OnKwsTriggered: (\w+)'
        )
    
    def parse_kws_line(self, line: str) -> Optional[Dict]:
        """解析KWS识别行"""
        match = self.kws_pattern.search(line)
        if match:
            timestamp, model, phrase, score, begin, end = match.groups()
            return {
                'timestamp': timestamp,
                'model': model,
                'phrase': phrase,
                'score': float(score),
                'begin': int(begin),
                'end': int(end),
                'raw_log': line.strip()
            }
        return None
    
    def parse_save_record_line(self, line: str) -> Optional[Dict]:
        """解析SaveRecord行"""
        match = self.save_record_pattern.search(line)
        if match:
            timestamp, phrase = match.groups()
            return {
                'timestamp': timestamp,
                'phrase': phrase,
                'triggered': False,
                'raw_log': line.strip()
            }
        return None
    
    def parse_triggered_line(self, line: str) -> Optional[Dict]:
        """解析Triggered行"""
        match = self.triggered_pattern.search(line)
        if match:
            timestamp, phrase = match.groups()
            return {
                'timestamp': timestamp,
                'phrase': phrase,
                'triggered': True,
                'raw_log': line.strip()
            }
        return None

class KWSCalculator:
    """KWS计算主类"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.ssh_monitor = SSHLogMonitor(host, username, password, port)
        self.parser = KWSLogParser()
        self.records = []
        self.triggered_records = []
        self.untriggered_records = []
        self.monitoring = False
        self.output_dir = "kws_output"
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def connect(self) -> bool:
        """连接到设备"""
        return self.ssh_monitor.connect()
    
    def disconnect(self):
        """断开连接"""
        self.ssh_monitor.disconnect()
    
    def start_monitoring(self, log_file_path: str = "/var/log/vibe-ai/vibe-ai.LATEST"):
        """开始监控日志"""
        if not self.ssh_monitor.connected:
            logger.error("SSH未连接，无法开始监控")
            return
        
        self.monitoring = True
        logger.info(f"开始监控日志文件: {log_file_path}")
        
        try:
            # 使用tail -f命令持续监控日志
            command = f"tail -f {log_file_path}"
            stdin, stdout, stderr = self.ssh_monitor.ssh_client.exec_command(command)
            
            # 实时读取输出
            while self.monitoring:
                line = stdout.readline()
                if line:
                    self._process_log_line(line.strip())
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
        finally:
            self.monitoring = False
    
    def _process_log_line(self, line: str):
        """处理单行日志"""
        # 解析KWS识别行
        kws_data = self.parser.parse_kws_line(line)
        if kws_data:
            logger.info(f"检测到KWS识别: phrase={kws_data['phrase']}, score={kws_data['score']}")
            
            # 创建记录
            record = KWSRecord(
                timestamp=kws_data['timestamp'],
                phrase=kws_data['phrase'],
                score=kws_data['score'],
                begin_time=kws_data['begin'],
                end_time=kws_data['end'],
                triggered=False,  # 默认未触发，后续根据SaveRecord/Triggered更新
                raw_log=kws_data['raw_log']
            )
            self.records.append(record)
            return
        
        # 解析SaveRecord行（未触发）
        save_data = self.parser.parse_save_record_line(line)
        if save_data:
            logger.info(f"检测到未触发记录: phrase={save_data['phrase']}")
            self._update_trigger_status(save_data['phrase'], False, save_data['timestamp'])
            return
        
        # 解析Triggered行（已触发）
        triggered_data = self.parser.parse_triggered_line(line)
        if triggered_data:
            logger.info(f"检测到触发记录: phrase={triggered_data['phrase']}")
            self._update_trigger_status(triggered_data['phrase'], True, triggered_data['timestamp'])
            return
    
    def _update_trigger_status(self, phrase: str, triggered: bool, timestamp: str):
        """更新触发状态"""
        # 查找最近的匹配记录
        for record in reversed(self.records):
            if (record.phrase == phrase and 
                not hasattr(record, 'status_updated') and
                abs(self._timestamp_diff(record.timestamp, timestamp)) < 5):  # 5秒内的记录
                
                record.triggered = triggered
                record.status_updated = True
                
                if triggered:
                    self.triggered_records.append(record)
                    logger.info(f"记录已触发: {phrase}, score: {record.score}")
                else:
                    self.untriggered_records.append(record)
                    logger.info(f"记录未触发: {phrase}, score: {record.score}")
                break
    
    def _timestamp_diff(self, ts1: str, ts2: str) -> float:
        """计算时间戳差异（秒）"""
        try:
            dt1 = datetime.fromisoformat(ts1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(ts2.replace('Z', '+00:00'))
            return abs((dt1 - dt2).total_seconds())
        except:
            return 0
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        logger.info("停止监控")
    
    def export_results(self):
        """导出结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出为JSON
        json_file = os.path.join(self.output_dir, f"kws_results_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            data = {
                'all_records': [asdict(record) for record in self.records],
                'triggered_records': [asdict(record) for record in self.triggered_records],
                'untriggered_records': [asdict(record) for record in self.untriggered_records],
                'summary': {
                    'total_records': len(self.records),
                    'triggered_count': len(self.triggered_records),
                    'untriggered_count': len(self.untriggered_records),
                    'trigger_rate': len(self.triggered_records) / len(self.records) if self.records else 0
                }
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 导出为CSV
        csv_file = os.path.join(self.output_dir, f"kws_results_{timestamp}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间戳', '唤醒词', '分数', '开始时间', '结束时间', '是否触发', '原始日志'])
            
            for record in self.records:
                writer.writerow([
                    record.timestamp,
                    record.phrase,
                    record.score,
                    record.begin_time,
                    record.end_time,
                    '是' if record.triggered else '否',
                    record.raw_log
                ])
        
        logger.info(f"结果已导出到: {json_file} 和 {csv_file}")
    
    def print_summary(self):
        """打印统计摘要"""
        print("\n" + "="*60)
        print("KWS 识别统计摘要")
        print("="*60)
        print(f"总记录数: {len(self.records)}")
        print(f"触发记录数: {len(self.triggered_records)}")
        print(f"未触发记录数: {len(self.untriggered_records)}")
        
        if self.records:
            trigger_rate = len(self.triggered_records) / len(self.records) * 100
            print(f"触发率: {trigger_rate:.2f}%")
            
            # 分数统计
            all_scores = [record.score for record in self.records]
            triggered_scores = [record.score for record in self.triggered_records]
            untriggered_scores = [record.score for record in self.untriggered_records]
            
            print(f"\n分数统计:")
            print(f"  所有记录平均分数: {sum(all_scores)/len(all_scores):.4f}")
            if triggered_scores:
                print(f"  触发记录平均分数: {sum(triggered_scores)/len(triggered_scores):.4f}")
            if untriggered_scores:
                print(f"  未触发记录平均分数: {sum(untriggered_scores)/len(untriggered_scores):.4f}")
        
        print("="*60)

def main():
    """主函数"""
    print("KWS 计算工具")
    print("="*50)
    
    # 获取连接参数
    host = input("请输入设备IP地址: ").strip()
    username = input("请输入SSH用户名: ").strip()
    password = input("请输入SSH密码: ").strip()
    
    # 创建KWS计算器
    kws_calc = KWSCalculator(host, username, password)
    
    try:
        # 连接设备
        if not kws_calc.connect():
            print("连接失败，程序退出")
            return
        
        print("连接成功，开始监控...")
        print("按 Ctrl+C 停止监控")
        
        # 开始监控
        monitor_thread = threading.Thread(target=kws_calc.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 等待用户中断
        try:
            while kws_calc.monitoring:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            kws_calc.stop_monitoring()
        
        # 等待监控线程结束
        monitor_thread.join(timeout=5)
        
        # 导出结果和打印摘要
        kws_calc.export_results()
        kws_calc.print_summary()
        
    finally:
        kws_calc.disconnect()

if __name__ == "__main__":
    main()