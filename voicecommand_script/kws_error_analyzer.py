#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS测试错误分析工具
用于分析TTS播放记录与KWS识别结果的对应关系，找出错误识别的情况
"""

import json
import csv
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

class KWSErrorAnalyzer:
    """KWS测试错误分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.tts_records = []
        self.kws_records = []
        self.error_records = []
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_tts_records(self, json_file_path: str) -> bool:
        """
        加载TTS播放记录JSON文件
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.tts_records = json.load(f)
            
            self.logger.info(f"成功加载TTS记录文件: {json_file_path}")
            self.logger.info(f"TTS记录总数: {len(self.tts_records)}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载TTS记录文件失败: {e}")
            return False
    
    def load_kws_records(self, csv_file_path: str) -> bool:
        """
        加载KWS识别结果CSV文件
        
        Args:
            csv_file_path: CSV文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.kws_records = []
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.kws_records.append(row)
            
            self.logger.info(f"成功加载KWS记录文件: {csv_file_path}")
            self.logger.info(f"KWS记录总数: {len(self.kws_records)}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载KWS记录文件失败: {e}")
            return False
    
    def parse_timestamp(self, timestamp_str: str, format_type: str) -> datetime:
        """
        解析时间戳字符串
        
        Args:
            timestamp_str: 时间戳字符串
            format_type: 格式类型 ('tts' 或 'kws')
            
        Returns:
            datetime: 解析后的时间对象
        """
        try:
            if format_type == 'tts':
                # TTS格式: "2025/10/16 15:21:22.758"
                return datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S.%f")
            elif format_type == 'kws':
                # KWS格式: "2025-10-15T08:12:21.340056Z"
                # 移除末尾的Z并解析
                timestamp_str = timestamp_str.rstrip('Z')
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            self.logger.error(f"时间戳解析失败: {timestamp_str}, 错误: {e}")
            raise
    
    def is_timestamp_match(self, tts_time: datetime, kws_time: datetime) -> bool:
        """
        检查时间戳是否匹配
        TTS播放时间应该在KWS识别时间之前，且差值不超过1秒
        
        Args:
            tts_time: TTS播放时间
            kws_time: KWS识别时间
            
        Returns:
            bool: 时间戳是否匹配
        """
        time_diff = (kws_time - tts_time).total_seconds()
        return 0 <= time_diff <= 1.0
    
    def normalize_text(self, text: str) -> str:
        """
        标准化文本内容，用于比较
        
        Args:
            text: 原始文本
            
        Returns:
            str: 标准化后的文本
        """
        return text.lower().strip().replace('_', '').replace('-', '')
    
    def is_content_match(self, tts_text: str, kws_phrase: str) -> bool:
        """
        检查TTS文本与KWS提示词是否匹配
        
        Args:
            tts_text: TTS播放的文本
            kws_phrase: KWS识别的提示词
            
        Returns:
            bool: 内容是否匹配
        """
        normalized_tts = self.normalize_text(tts_text)
        normalized_kws = self.normalize_text(kws_phrase)
        return normalized_tts == normalized_kws
    
    def analyze_records(self) -> List[Dict]:
        """
        分析TTS记录与KWS记录的对应关系
        
        Returns:
            List[Dict]: 错误记录列表
        """
        if not self.tts_records or not self.kws_records:
            self.logger.error("TTS记录或KWS记录为空，无法进行分析")
            return []
        
        self.error_records = []
        tts_index = 0
        kws_index = 0
        
        self.logger.info("开始分析TTS记录与KWS记录的对应关系...")
        
        while tts_index < len(self.tts_records) and kws_index < len(self.kws_records):
            tts_record = self.tts_records[tts_index]
            kws_record = self.kws_records[kws_index]
            
            try:
                # 解析时间戳
                tts_time = self.parse_timestamp(tts_record['timestamp'], 'tts')
                kws_time = self.parse_timestamp(kws_record['时间戳'], 'kws')
                
                # 检查时间戳匹配
                if self.is_timestamp_match(tts_time, kws_time):
                    # 时间戳匹配，进行内容分析
                    self._analyze_content_match(tts_record, kws_record, tts_time, kws_time)
                    tts_index += 1
                    kws_index += 1
                    
                elif tts_time > kws_time:
                    # TTS时间晚于KWS时间，报错并停止
                    error_msg = f"时间戳顺序错误: TTS时间({tts_time}) > KWS时间({kws_time})"
                    self.logger.error(error_msg)
                    break
                    
                else:
                    # TTS时间早于KWS时间但差值超过1秒，TTS向下一位
                    tts_index += 1
                    
            except Exception as e:
                self.logger.error(f"分析记录时出错: {e}")
                tts_index += 1
                kws_index += 1
        
        self.logger.info(f"分析完成，发现错误记录: {len(self.error_records)} 条")
        return self.error_records
    
    def _analyze_content_match(self, tts_record: Dict, kws_record: Dict, 
                              tts_time: datetime, kws_time: datetime):
        """
        分析内容匹配情况
        
        Args:
            tts_record: TTS记录
            kws_record: KWS记录
            tts_time: TTS时间
            kws_time: KWS时间
        """
        tts_text = tts_record['text']
        kws_phrase = kws_record['提示词']
        sample_type = tts_record['sample_type']
        is_triggered = kws_record['是否触发'] == '是'
        
        content_match = self.is_content_match(tts_text, kws_phrase)
        
        if content_match:
            # 内容匹配的情况
            if sample_type == 'negative':
                # negative样本被正确识别，这是错误
                error_record = {
                    'error_type': 'negative_sample_recognized',
                    'kws_timestamp': kws_record['时间戳'],
                    'kws_phrase': kws_phrase,
                    'kws_score': kws_record['分数'],
                    'kws_triggered': kws_record['是否触发'],
                    'tts_text': tts_text,
                    'tts_time': tts_record['timestamp'],
                    'sample_type': sample_type
                }
                self.error_records.append(error_record)
                self.logger.error(f"ERROR: negative样本被错误识别 - TTS文本: {tts_text}, KWS提示词: {kws_phrase}")
            
        else:
            # 内容不匹配的情况
            if is_triggered and sample_type == 'negative':
                # negative样本触发了不同的提示词，这是错误
                error_record = {
                    'error_type': 'negative_sample_wrong_trigger',
                    'kws_timestamp': kws_record['时间戳'],
                    'kws_phrase': kws_phrase,
                    'kws_score': kws_record['分数'],
                    'kws_triggered': kws_record['是否触发'],
                    'tts_text': tts_text,
                    'tts_time': tts_record['timestamp'],
                    'sample_type': sample_type
                }
                self.error_records.append(error_record)
                self.logger.error(f"ERROR: negative样本触发错误提示词 - TTS文本: {tts_text}, KWS提示词: {kws_phrase}")
    
    def save_error_analysis(self, output_file: str = None) -> str:
        """
        保存错误分析结果到文件
        
        Args:
            output_file: 输出文件路径，如果为None则自动生成
            
        Returns:
            str: 输出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"kws_error_analysis_{timestamp}.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if self.error_records:
                    fieldnames = self.error_records[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.error_records)
                else:
                    # 如果没有错误记录，写入表头
                    fieldnames = ['error_type', 'kws_timestamp', 'kws_phrase', 'kws_score', 
                                'kws_triggered', 'tts_text', 'tts_time', 'sample_type']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
            
            self.logger.info(f"错误分析结果已保存到: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"保存错误分析结果失败: {e}")
            return ""
    
    def print_summary(self):
        """打印分析摘要"""
        self.logger.info("=" * 50)
        self.logger.info("KWS测试错误分析摘要")
        self.logger.info("=" * 50)
        self.logger.info(f"TTS记录总数: {len(self.tts_records)}")
        self.logger.info(f"KWS记录总数: {len(self.kws_records)}")
        self.logger.info(f"发现错误记录: {len(self.error_records)}")
        
        if self.error_records:
            error_types = {}
            for record in self.error_records:
                error_type = record['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            self.logger.info("错误类型统计:")
            for error_type, count in error_types.items():
                self.logger.info(f"  {error_type}: {count} 条")
        
        self.logger.info("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法: python kws_error_analyzer.py <TTS_JSON_FILE> <KWS_CSV_FILE>")
        print("示例: python kws_error_analyzer.py realtime_parse_info.json kws_data.csv")
        sys.exit(1)
    
    tts_file = sys.argv[1]
    kws_file = sys.argv[2]
    
    # 检查文件是否存在
    if not os.path.exists(tts_file):
        print(f"错误: TTS文件不存在: {tts_file}")
        sys.exit(1)
    
    if not os.path.exists(kws_file):
        print(f"错误: KWS文件不存在: {kws_file}")
        sys.exit(1)
    
    # 创建分析器并执行分析
    analyzer = KWSErrorAnalyzer()
    
    # 加载数据
    if not analyzer.load_tts_records(tts_file):
        sys.exit(1)
    
    if not analyzer.load_kws_records(kws_file):
        sys.exit(1)
    
    # 执行分析
    analyzer.analyze_records()
    
    # 保存结果
    output_file = analyzer.save_error_analysis()
    
    # 打印摘要
    analyzer.print_summary()
    
    if output_file:
        print(f"\n分析完成！错误分析结果已保存到: {output_file}")


if __name__ == "__main__":
    main()