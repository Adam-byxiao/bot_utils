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
    timestamp: str                  # 时间戳
    phrase: str                     # 唤醒词
    score: float                    # 识别分数
    begin_time: int                 # 开始时间
    end_time: int                   # 结束时间
    triggered: bool                 # 是否触发
    raw_log: str                    # 原始日志
    predicted_label_id: int = None   # 预测标签ID (0或1)
    confidence_score: float = None  # 置信度分数
    raw_logits: str = None          # 原始logits
    probabilities: str = None        # 概率分布
    preprocess_cost: int = None     # 预处理耗时(ms)
    rknn_run_cost: int = None       # RKNN运行耗时(ms)
    sum_cost: int = None            # 总耗时(ms)
    detailed_raw_log: str = None    # 详细原始日志

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
        # 正则表达式模式 - 更新为新的日志格式
        self.kws_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*?'
            r'Model: (\w+) recognized phrase: (\w+), score: ([\d.]+), begin: ([\d.e+-]+), end: ([\d.e+-]+)'
        )
        
        # 新的结果详情模式 (多行匹配)
        self.results_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z).*?'
            r'--- Model:(\w+) Results ---[\s\S]*?'
            r'Raw Logits:\s*\[(.*?)\][\s\S]*?'
            r'Probabilities:\s*\[(.*?)\][\s\S]*?'
            r'==> Predicted Label ID:\s*(\d+)[\s\S]*?'
            r'==> Confidence Score:\s*([\d.]+)[\s\S]*?'
            r'==> Preprocess Cost:\s*(\d+)ms[\s\S]*?'
            r'==> Rknn Run Cost:\s*(\d+)ms[\s\S]*?'
            r'==> Sum Cost:\s*(\d+)ms'
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
                'begin': int(float(begin)),  # 支持科学计数法
                'end': int(float(end)),      # 支持科学计数法
                'raw_log': line.strip()
            }
        return None
    
    def parse_results_line(self, line: str) -> Optional[Dict]:
        """解析结果详情行"""
        match = self.results_pattern.search(line)
        if match:
            timestamp, model, raw_logits, probabilities, label_id, confidence_score, preprocess_cost, rknn_cost, sum_cost = match.groups()
            return {
                'timestamp': timestamp,
                'model': model.strip(),
                'raw_logits': raw_logits.strip(),
                'probabilities': probabilities.strip(),
                'predicted_label_id': int(label_id),
                'confidence_score': float(confidence_score),
                'preprocess_cost': int(preprocess_cost),
                'rknn_run_cost': int(rknn_cost),
                'sum_cost': int(sum_cost),
                'triggered': int(label_id) == 1,  # Label ID为1表示检测到唤醒
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
        self.connection_start_time = None  # 记录连接开始时间
        self._current_multiline_buffer = ""  # 多行日志缓冲区
        self._in_results_section = False     # 是否在结果详情部分
        
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
        # 记录监控开始时间（UTC时间）
        self.connection_start_time = datetime.utcnow()
        logger.info(f"开始监控日志文件: {log_file_path}")
        logger.info(f"监控开始时间: {self.connection_start_time.isoformat()}Z")
        
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
        """处理日志行，支持多行日志"""
        # 检查是否开始新的结果详情部分
        if "--- Model:" in line and "Results ---" in line:
            self._in_results_section = True
            self._current_multiline_buffer = line + " "
            return
        
        # 如果在结果详情部分，累积日志行
        if self._in_results_section:
            self._current_multiline_buffer += line + " "
            
            # 检查是否到达结果详情结束（包含Sum Cost表示结束）
            if "Sum Cost:" in line:
                # 尝试解析完整的多行结果详情
                results_data = self.parser.parse_results_line(self._current_multiline_buffer)
                if results_data:
                    # 检查时间戳是否在连接后
                    if not self._is_after_connection(results_data['timestamp']):
                        logger.debug(f"忽略连接前的结果详情记录: {results_data['timestamp']}")
                        self._in_results_section = False
                        self._current_multiline_buffer = ""
                        return
                        
                    logger.info(f"检测到结果详情: model={results_data['model']}, label_id={results_data['predicted_label_id']}, confidence={results_data['confidence_score']}")
                    
                    # 创建详细记录
                    detailed_record = {
                        'timestamp': results_data['timestamp'],
                        'model': results_data['model'],
                        'predicted_label_id': results_data['predicted_label_id'],
                        'confidence_score': results_data['confidence_score'],
                        'raw_logits': results_data['raw_logits'],
                        'probabilities': results_data['probabilities'],
                        'preprocess_cost': results_data['preprocess_cost'],
                        'rknn_run_cost': results_data['rknn_run_cost'],
                        'sum_cost': results_data['sum_cost'],
                        'triggered': results_data['triggered'],
                        'raw_log': results_data['raw_log']
                    }
                    
                    # 更新最近的KWS记录状态
                    self._update_trigger_status(results_data['model'], results_data['triggered'], results_data['timestamp'], detailed_record)
                
                # 重置状态
                self._in_results_section = False
                self._current_multiline_buffer = ""
            return
        
        # 解析KWS识别行（单行）
        kws_data = self.parser.parse_kws_line(line)
        if kws_data:
            # 检查时间戳是否在连接后
            if not self._is_after_connection(kws_data['timestamp']):
                logger.debug(f"忽略连接前的KWS识别记录: {kws_data['timestamp']}")
                return
                
            logger.info(f"检测到KWS识别: phrase={kws_data['phrase']}, score={kws_data['score']}")
            
            # 创建记录
            record = KWSRecord(
                timestamp=kws_data['timestamp'],
                phrase=kws_data['phrase'],
                score=kws_data['score'],
                begin_time=kws_data['begin'],
                end_time=kws_data['end'],
                triggered=False,  # 默认未触发，后续根据结果详情更新
                raw_log=kws_data['raw_log']
            )
            self.records.append(record)
            return
        
        # 解析SaveRecord行（未触发）
        save_data = self.parser.parse_save_record_line(line)
        if save_data:
            # 检查时间戳是否在连接后
            if not self._is_after_connection(save_data['timestamp']):
                logger.debug(f"忽略连接前的未触发记录: {save_data['timestamp']}")
                return
                
            logger.info(f"检测到未触发记录: phrase={save_data['phrase']}")
            self._update_trigger_status(save_data['phrase'], False, save_data['timestamp'])
            return
        
        # 解析Triggered行（已触发）
        triggered_data = self.parser.parse_triggered_line(line)
        if triggered_data:
            # 检查时间戳是否在连接后
            if not self._is_after_connection(triggered_data['timestamp']):
                logger.debug(f"忽略连接前的触发记录: {triggered_data['timestamp']}")
                return
                
            # 检查是否已经有详细的结果信息，避免重复更新
            has_detailed_info = False
            for record in self.records:
                if (record.phrase == triggered_data['phrase'] and 
                    abs(self._timestamp_diff(record.timestamp, triggered_data['timestamp'])) < 5 and
                    record.predicted_label_id is not None):
                    has_detailed_info = True
                    break
            
            # 如果没有详细结果信息，才进行状态更新
            if not has_detailed_info:
                logger.info(f"检测到触发记录: phrase={triggered_data['phrase']}")
                self._update_trigger_status(triggered_data['phrase'], True, triggered_data['timestamp'])
            else:
                logger.debug(f"跳过重复的触发记录（已有详细结果）: phrase={triggered_data['phrase']}")
            return
    
    def _update_trigger_status(self, phrase: str, triggered: bool, timestamp: str, detailed_record: Optional[Dict] = None):
        """更新触发状态"""
        # 查找最近的匹配记录
        for record in reversed(self.records):
            if (record.phrase == phrase and 
                abs(self._timestamp_diff(record.timestamp, timestamp)) < 5):  # 5秒内的记录
                
                record.triggered = triggered
                
                # 添加详细结果信息
                if detailed_record:
                    record.predicted_label_id = detailed_record['predicted_label_id']
                    record.confidence_score = detailed_record['confidence_score']
                    record.raw_logits = detailed_record['raw_logits']
                    record.probabilities = detailed_record['probabilities']
                    record.preprocess_cost = detailed_record['preprocess_cost']
                    record.rknn_run_cost = detailed_record['rknn_run_cost']
                    record.sum_cost = detailed_record['sum_cost']
                    record.detailed_raw_log = detailed_record['raw_log']
                
                if triggered:
                    self.triggered_records.append(record)
                    if detailed_record:
                        logger.info(f"记录已触发: {phrase}, label_id: {record.predicted_label_id}, confidence: {record.confidence_score}")
                    else:
                        logger.info(f"记录已触发: {phrase}, score: {record.score}")
                else:
                    self.untriggered_records.append(record)
                    if detailed_record:
                        logger.info(f"记录未触发: {phrase}, label_id: {record.predicted_label_id}, confidence: {record.confidence_score}")
                    else:
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
    
    def _is_after_connection(self, timestamp: str) -> bool:
        """检查时间戳是否在连接开始时间之后"""
        if not self.connection_start_time:
            return True  # 如果没有记录连接时间，则不过滤
        
        try:
            log_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # 转换为UTC时间进行比较
            log_time_utc = log_time.replace(tzinfo=None)
            return log_time_utc >= self.connection_start_time
        except Exception as e:
            logger.warning(f"时间戳解析失败: {timestamp}, 错误: {e}")
            return True  # 解析失败时不过滤
    
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
            writer.writerow(['时间戳', '唤醒词', '分数', '开始时间', '结束时间', '是否触发', 
                           '预测标签ID', '置信度分数', '预处理耗时(ms)', 'RKNN运行耗时(ms)', '总耗时(ms)', '原始日志'])
            
            for record in self.records:
                writer.writerow([
                    record.timestamp,
                    record.phrase,
                    record.score,
                    record.begin_time,
                    record.end_time,
                    '是' if record.triggered else '否',
                    record.predicted_label_id if hasattr(record, 'predicted_label_id') else 'N/A',
                    record.confidence_score if hasattr(record, 'confidence_score') else 'N/A',
                    record.preprocess_cost if hasattr(record, 'preprocess_cost') else 'N/A',
                    record.rknn_run_cost if hasattr(record, 'rknn_run_cost') else 'N/A',
                    record.sum_cost if hasattr(record, 'sum_cost') else 'N/A',
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