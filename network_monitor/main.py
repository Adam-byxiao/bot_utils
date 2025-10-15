#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Network Monitor Demo
通过Chrome DevTools Protocol获取设备后端信息并进行标准化处理的完整解决方案
"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

# 导入自定义模块
from chrome_network_listener import ChromeNetworkListener
from data_parser import DataParser
from data_standardizer import DataStandardizer
from data_filter import DataFilter
from data_exporter import DataExporter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('network_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class NetworkMonitor:
    """网络监控主程序"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.running = False
        
        # 初始化组件
        self.listener = ChromeNetworkListener(
            host=config.get('chrome_host', 'localhost'),
            port=config.get('chrome_port', 9222)
        )
        
        self.parser = DataParser()
        self.standardizer = DataStandardizer()
        self.filter = DataFilter()
        self.exporter = DataExporter(config.get('output_dir', './output'))
        
        # 数据存储
        self.raw_transactions = []
        self.processed_transactions = []
        
        # 配置过滤器
        self._setup_filters()
        
        logger.info("网络监控器初始化完成")
    
    def _setup_filters(self):
        """设置过滤规则"""
        filter_config = self.config.get('filters', {})
        
        # 静态资源过滤
        if filter_config.get('exclude_static_resources', True):
            self.filter.add_rule(
                name='exclude_static',
                rule_type='exclude',
                pattern=r'\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$',
                field='url'
            )
        
        # API请求过滤
        if filter_config.get('api_only', False):
            self.filter.add_rule(
                name='api_only',
                rule_type='include',
                pattern=r'/api/',
                field='url'
            )
        
        # 状态码过滤
        exclude_status = filter_config.get('exclude_status_codes', [])
        if exclude_status:
            for status in exclude_status:
                self.filter.add_rule(
                    name=f'exclude_status_{status}',
                    rule_type='exclude',
                    pattern=str(status),
                    field='status_code'
                )
        
        # 域名过滤
        include_domains = filter_config.get('include_domains', [])
        if include_domains:
            for domain in include_domains:
                self.filter.add_rule(
                    name=f'include_domain_{domain}',
                    rule_type='include',
                    pattern=domain,
                    field='domain'
                )
        
        logger.info(f"过滤器配置完成，共{len(self.filter.rules)}条规则")
    
    async def start_monitoring(self, duration: Optional[int] = None):
        """开始监控"""
        try:
            logger.info("开始网络监控...")
            self.running = True
            
            # 连接Chrome
            await self.listener.connect()
            
            # 设置事件处理器
            self.listener.on_request_sent = self._on_request_sent
            self.listener.on_response_received = self._on_response_received
            self.listener.on_loading_finished = self._on_loading_finished
            self.listener.on_loading_failed = self._on_loading_failed
            
            # 开始监听
            await self.listener.start_listening()
            
            # 如果指定了持续时间，设置定时器
            if duration:
                logger.info(f"监控将在{duration}秒后自动停止")
                await asyncio.sleep(duration)
                await self.stop_monitoring()
            else:
                # 等待手动停止
                while self.running:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
            raise
    
    async def stop_monitoring(self):
        """停止监控"""
        logger.info("停止网络监控...")
        self.running = False
        
        if self.listener:
            await self.listener.stop_listening()
            await self.listener.disconnect()
        
        # 处理收集到的数据
        await self._process_collected_data()
        
        logger.info("监控已停止")
    
    async def _on_request_sent(self, request_data: Dict):
        """处理请求发送事件"""
        try:
            # 解析请求
            parsed_request = self.parser.parse_request(request_data)
            
            # 创建事务记录
            transaction = self.parser.create_transaction(
                request=parsed_request,
                session_id=self.config.get('session_id', 'default')
            )
            
            self.raw_transactions.append(transaction)
            
            logger.debug(f"记录请求: {parsed_request.method} {parsed_request.url}")
            
        except Exception as e:
            logger.error(f"处理请求事件时发生错误: {e}")
    
    async def _on_response_received(self, response_data: Dict):
        """处理响应接收事件"""
        try:
            request_id = response_data.get('requestId')
            if not request_id:
                return
            
            # 查找对应的事务
            transaction = None
            for t in self.raw_transactions:
                if t.request and t.request.request_id == request_id:
                    transaction = t
                    break
            
            if not transaction:
                logger.warning(f"未找到请求ID为{request_id}的事务")
                return
            
            # 解析响应
            parsed_response = self.parser.parse_response(response_data)
            transaction.response = parsed_response
            
            logger.debug(f"记录响应: {parsed_response.status_code} for {request_id}")
            
        except Exception as e:
            logger.error(f"处理响应事件时发生错误: {e}")
    
    async def _on_loading_finished(self, event_data: Dict):
        """处理加载完成事件"""
        try:
            request_id = event_data.get('requestId')
            if not request_id:
                return
            
            # 查找对应的事务并标记为成功
            for transaction in self.raw_transactions:
                if transaction.request and transaction.request.request_id == request_id:
                    transaction.success = True
                    transaction.end_time = datetime.now()
                    
                    # 计算持续时间
                    if transaction.start_time:
                        duration = (transaction.end_time - transaction.start_time).total_seconds() * 1000
                        transaction.duration_ms = duration
                    
                    logger.debug(f"请求完成: {request_id}")
                    break
                    
        except Exception as e:
            logger.error(f"处理加载完成事件时发生错误: {e}")
    
    async def _on_loading_failed(self, event_data: Dict):
        """处理加载失败事件"""
        try:
            request_id = event_data.get('requestId')
            error_text = event_data.get('errorText', 'Unknown error')
            
            if not request_id:
                return
            
            # 查找对应的事务并标记为失败
            for transaction in self.raw_transactions:
                if transaction.request and transaction.request.request_id == request_id:
                    transaction.success = False
                    transaction.error_message = error_text
                    transaction.end_time = datetime.now()
                    
                    logger.debug(f"请求失败: {request_id} - {error_text}")
                    break
                    
        except Exception as e:
            logger.error(f"处理加载失败事件时发生错误: {e}")
    
    async def _process_collected_data(self):
        """处理收集到的数据"""
        logger.info(f"开始处理收集到的{len(self.raw_transactions)}条数据...")
        
        try:
            # 标准化数据
            for transaction in self.raw_transactions:
                if transaction.request:
                    standardized = self.standardizer.standardize_transaction(transaction)
                    
                    # 应用过滤器
                    if self.filter.should_include(standardized):
                        self.processed_transactions.append(standardized)
            
            # 去重
            before_dedup = len(self.processed_transactions)
            self.processed_transactions = self.filter.deduplicate(self.processed_transactions)
            after_dedup = len(self.processed_transactions)
            
            logger.info(f"数据处理完成: 原始{len(self.raw_transactions)}条 -> 过滤后{before_dedup}条 -> 去重后{after_dedup}条")
            
            # 导出数据
            await self._export_data()
            
        except Exception as e:
            logger.error(f"处理数据时发生错误: {e}")
    
    async def _export_data(self):
        """导出数据"""
        if not self.processed_transactions:
            logger.warning("没有数据可导出")
            return
        
        export_config = self.config.get('export', {})
        formats = export_config.get('formats', ['json'])
        
        logger.info(f"开始导出数据，格式: {formats}")
        
        # 转换为字典格式
        export_data = []
        for transaction in self.processed_transactions:
            export_data.append(transaction.__dict__)
        
        # 导出为指定格式
        exported_files = []
        for format_type in formats:
            try:
                if format_type in self.exporter.get_supported_formats():
                    filepath = self.exporter.export_transactions(export_data, format_type)
                    exported_files.append(filepath)
                    logger.info(f"导出{format_type.upper()}格式完成: {filepath}")
                else:
                    logger.warning(f"不支持的导出格式: {format_type}")
            except Exception as e:
                logger.error(f"导出{format_type}格式时发生错误: {e}")
        
        # 导出摘要报告
        if export_config.get('include_summary', True):
            try:
                summary_file = self.exporter.export_summary_report(export_data)
                exported_files.append(summary_file)
                logger.info(f"摘要报告导出完成: {summary_file}")
            except Exception as e:
                logger.error(f"导出摘要报告时发生错误: {e}")
        
        logger.info(f"数据导出完成，共{len(exported_files)}个文件")
        
        # 显示统计信息
        self._show_statistics()
    
    def _show_statistics(self):
        """显示统计信息"""
        total = len(self.processed_transactions)
        if total == 0:
            return
        
        # 基本统计
        successful = sum(1 for t in self.processed_transactions if t.success)
        api_requests = sum(1 for t in self.processed_transactions if t.request and t.request.is_api)
        
        # 状态码统计
        status_codes = {}
        for transaction in self.processed_transactions:
            if transaction.response:
                status = transaction.response.status_code
                status_codes[status] = status_codes.get(status, 0) + 1
        
        # 域名统计
        domains = {}
        for transaction in self.processed_transactions:
            if transaction.request:
                domain = transaction.request.domain
                if domain:
                    domains[domain] = domains.get(domain, 0) + 1
        
        # 性能统计
        durations = [t.duration_ms for t in self.processed_transactions if t.duration_ms and t.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        logger.info("=" * 50)
        logger.info("监控统计信息:")
        logger.info(f"总请求数: {total}")
        logger.info(f"成功请求: {successful} ({successful/total*100:.1f}%)")
        logger.info(f"API请求: {api_requests} ({api_requests/total*100:.1f}%)")
        logger.info(f"平均响应时间: {avg_duration:.2f}ms")
        logger.info(f"涉及域名: {len(domains)}个")
        
        if status_codes:
            logger.info("状态码分布:")
            for status, count in sorted(status_codes.items()):
                logger.info(f"  {status}: {count}次")
        
        if domains:
            logger.info("域名分布 (Top 5):")
            sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]
            for domain, count in sorted_domains:
                logger.info(f"  {domain}: {count}次")
        
        logger.info("=" * 50)

def load_config(config_file: str) -> Dict:
    """加载配置文件"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
        return get_default_config()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"配置文件加载成功: {config_file}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}，使用默认配置")
        return get_default_config()

def get_default_config() -> Dict:
    """获取默认配置"""
    return {
        "chrome_host": "localhost",
        "chrome_port": 9222,
        "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "output_dir": "./output",
        "filters": {
            "exclude_static_resources": True,
            "api_only": False,
            "exclude_status_codes": [],
            "include_domains": []
        },
        "export": {
            "formats": ["json", "csv", "txt"],
            "include_summary": True
        }
    }

def create_default_config_file(config_file: str):
    """创建默认配置文件"""
    config = get_default_config()
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"默认配置文件已创建: {config_file}")
    except Exception as e:
        logger.error(f"创建配置文件失败: {e}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Chrome DevTools Network Monitor')
    parser.add_argument('-c', '--config', default='config.json', help='配置文件路径')
    parser.add_argument('-d', '--duration', type=int, help='监控持续时间（秒）')
    parser.add_argument('--create-config', action='store_true', help='创建默认配置文件')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细日志输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建配置文件
    if args.create_config:
        create_default_config_file(args.config)
        return
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建监控器
    monitor = NetworkMonitor(config)
    
    # 设置信号处理器
    def signal_handler(signum, frame):
        logger.info("接收到停止信号，正在停止监控...")
        asyncio.create_task(monitor.stop_monitoring())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 开始监控
        await monitor.start_monitoring(args.duration)
    except KeyboardInterrupt:
        logger.info("用户中断监控")
    except Exception as e:
        logger.error(f"监控过程中发生错误: {e}")
        sys.exit(1)
    finally:
        if monitor.running:
            await monitor.stop_monitoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)