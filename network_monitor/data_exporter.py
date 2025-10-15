#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多格式数据导出模块
支持将网络监控数据导出为多种格式
"""

import json
import csv
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataExporter:
    """数据导出器"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 支持的导出格式
        self.supported_formats = ['json', 'csv', 'txt']
        if PANDAS_AVAILABLE and EXCEL_AVAILABLE:
            self.supported_formats.append('excel')
        
        logger.info(f"数据导出器初始化完成，支持格式: {self.supported_formats}")
    
    def export_transactions(self, transactions: List[Dict], 
                          format_type: str = 'json',
                          filename: Optional[str] = None) -> str:
        """导出事务数据"""
        if format_type not in self.supported_formats:
            raise ValueError(f"不支持的格式: {format_type}，支持的格式: {self.supported_formats}")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_data_{timestamp}"
        
        # 移除文件扩展名（如果有）
        filename = os.path.splitext(filename)[0]
        
        if format_type == 'json':
            return self._export_json(transactions, filename)
        elif format_type == 'csv':
            return self._export_csv(transactions, filename)
        elif format_type == 'excel':
            return self._export_excel(transactions, filename)
        elif format_type == 'txt':
            return self._export_txt(transactions, filename)
        else:
            raise ValueError(f"未实现的导出格式: {format_type}")
    
    def _export_json(self, transactions: List[Dict], filename: str) -> str:
        """导出为JSON格式"""
        filepath = self.output_dir / f"{filename}.json"
        
        export_data = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'total_transactions': len(transactions),
                'format_version': '1.0'
            },
            'transactions': transactions
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON导出完成: {filepath}")
        return str(filepath)
    
    def _export_csv(self, transactions: List[Dict], filename: str) -> str:
        """导出为CSV格式"""
        filepath = self.output_dir / f"{filename}.csv"
        
        if not transactions:
            logger.warning("没有数据可导出")
            return str(filepath)
        
        # 扁平化数据
        flattened_data = []
        for transaction in transactions:
            flat_row = self._flatten_transaction(transaction)
            flattened_data.append(flat_row)
        
        # 获取所有字段名
        all_fields = set()
        for row in flattened_data:
            all_fields.update(row.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)
        
        logger.info(f"CSV导出完成: {filepath}")
        return str(filepath)
    
    def _export_excel(self, transactions: List[Dict], filename: str) -> str:
        """导出为Excel格式"""
        if not PANDAS_AVAILABLE or not EXCEL_AVAILABLE:
            raise RuntimeError("Excel导出需要安装pandas和openpyxl库")
        
        filepath = self.output_dir / f"{filename}.xlsx"
        
        if not transactions:
            logger.warning("没有数据可导出")
            return str(filepath)
        
        # 创建多个工作表
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 主要事务数据
            flattened_data = [self._flatten_transaction(t) for t in transactions]
            df_main = pd.DataFrame(flattened_data)
            df_main.to_excel(writer, sheet_name='Transactions', index=False)
            
            # 请求摘要
            summary_data = self._create_summary_data(transactions)
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # API端点统计
            api_stats = self._create_api_stats(transactions)
            if api_stats:
                df_api = pd.DataFrame(api_stats)
                df_api.to_excel(writer, sheet_name='API_Stats', index=False)
            
            # 错误统计
            error_stats = self._create_error_stats(transactions)
            if error_stats:
                df_errors = pd.DataFrame(error_stats)
                df_errors.to_excel(writer, sheet_name='Errors', index=False)
        
        logger.info(f"Excel导出完成: {filepath}")
        return str(filepath)
    
    def _export_txt(self, transactions: List[Dict], filename: str) -> str:
        """导出为文本格式"""
        filepath = self.output_dir / f"{filename}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"网络监控数据报告\n")
            f.write(f"导出时间: {datetime.now().isoformat()}\n")
            f.write(f"总事务数: {len(transactions)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, transaction in enumerate(transactions, 1):
                f.write(f"事务 #{i}\n")
                f.write("-" * 40 + "\n")
                
                # 请求信息
                request = transaction.get('request', {})
                f.write(f"请求: {request.get('method', 'N/A')} {request.get('url', 'N/A')}\n")
                f.write(f"时间: {request.get('timestamp', 'N/A')}\n")
                
                # 响应信息
                response = transaction.get('response', {})
                f.write(f"响应: {response.get('status_code', 'N/A')} {response.get('status_text', 'N/A')}\n")
                f.write(f"类型: {response.get('content_type', 'N/A')}\n")
                
                # 性能信息
                duration = transaction.get('duration_ms', 0)
                f.write(f"耗时: {duration:.2f}ms\n")
                
                # 错误信息
                if transaction.get('error_message'):
                    f.write(f"错误: {transaction['error_message']}\n")
                
                f.write("\n")
        
        logger.info(f"TXT导出完成: {filepath}")
        return str(filepath)
    
    def _flatten_transaction(self, transaction: Dict) -> Dict[str, Any]:
        """扁平化事务数据"""
        flat = {}
        
        # 基本信息
        flat['transaction_id'] = transaction.get('transaction_id', '')
        flat['session_id'] = transaction.get('session_id', '')
        flat['timestamp'] = transaction.get('timestamp', '')
        flat['duration_ms'] = transaction.get('duration_ms', 0)
        flat['success'] = transaction.get('success', False)
        flat['error_message'] = transaction.get('error_message', '')
        
        # 请求信息
        request = transaction.get('request', {})
        flat['request_method'] = request.get('method', '')
        flat['request_url'] = request.get('url', '')
        flat['request_domain'] = request.get('domain', '')
        flat['request_path'] = request.get('path', '')
        flat['request_endpoint'] = request.get('endpoint', '')
        flat['request_content_type'] = request.get('content_type', '')
        flat['request_size_bytes'] = request.get('size_bytes', 0)
        flat['is_api'] = request.get('is_api', False)
        flat['api_version'] = request.get('api_version', '')
        
        # 查询参数（转为字符串）
        query_params = request.get('query_parameters', {})
        flat['query_params'] = json.dumps(query_params) if query_params else ''
        
        # 响应信息
        response = transaction.get('response', {})
        flat['response_status_code'] = response.get('status_code', 0)
        flat['response_status_category'] = response.get('status_category', '')
        flat['response_content_type'] = response.get('content_type', '')
        flat['response_size_bytes'] = response.get('size_bytes', 0)
        flat['response_is_json'] = response.get('is_json', False)
        
        # 标签
        tags = transaction.get('tags', [])
        flat['tags'] = ', '.join(tags) if tags else ''
        
        # 元数据
        metadata = transaction.get('metadata', {})
        flat['performance_category'] = metadata.get('performance_category', '')
        flat['total_size_bytes'] = metadata.get('total_size_bytes', 0)
        flat['is_secure'] = metadata.get('is_secure', False)
        
        return flat
    
    def _create_summary_data(self, transactions: List[Dict]) -> List[Dict]:
        """创建摘要数据"""
        if not transactions:
            return []
        
        # 统计信息
        total_requests = len(transactions)
        successful_requests = sum(1 for t in transactions if t.get('success', False))
        api_requests = sum(1 for t in transactions if t.get('request', {}).get('is_api', False))
        
        # 状态码统计
        status_codes = {}
        for transaction in transactions:
            status = transaction.get('response', {}).get('status_code', 0)
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # 域名统计
        domains = {}
        for transaction in transactions:
            domain = transaction.get('request', {}).get('domain', '')
            if domain:
                domains[domain] = domains.get(domain, 0) + 1
        
        # 性能统计
        durations = [t.get('duration_ms', 0) for t in transactions if t.get('duration_ms', 0) > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        summary = [
            {'指标': '总请求数', '值': total_requests},
            {'指标': '成功请求数', '值': successful_requests},
            {'指标': '成功率', '值': f"{(successful_requests/total_requests*100):.1f}%" if total_requests > 0 else '0%'},
            {'指标': 'API请求数', '值': api_requests},
            {'指标': '平均响应时间(ms)', '值': f"{avg_duration:.2f}"},
            {'指标': '最大响应时间(ms)', '值': f"{max_duration:.2f}"},
            {'指标': '最小响应时间(ms)', '值': f"{min_duration:.2f}"},
            {'指标': '唯一域名数', '值': len(domains)}
        ]
        
        return summary
    
    def _create_api_stats(self, transactions: List[Dict]) -> List[Dict]:
        """创建API统计数据"""
        api_stats = {}
        
        for transaction in transactions:
            request = transaction.get('request', {})
            if not request.get('is_api', False):
                continue
            
            endpoint = request.get('endpoint', request.get('path', ''))
            method = request.get('method', '')
            key = f"{method} {endpoint}"
            
            if key not in api_stats:
                api_stats[key] = {
                    'endpoint': endpoint,
                    'method': method,
                    'count': 0,
                    'success_count': 0,
                    'total_duration': 0,
                    'max_duration': 0,
                    'min_duration': float('inf')
                }
            
            stats = api_stats[key]
            stats['count'] += 1
            
            if transaction.get('success', False):
                stats['success_count'] += 1
            
            duration = transaction.get('duration_ms', 0)
            if duration > 0:
                stats['total_duration'] += duration
                stats['max_duration'] = max(stats['max_duration'], duration)
                stats['min_duration'] = min(stats['min_duration'], duration)
        
        # 转换为列表格式
        result = []
        for key, stats in api_stats.items():
            avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
            success_rate = (stats['success_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            
            result.append({
                'API端点': f"{stats['method']} {stats['endpoint']}",
                '调用次数': stats['count'],
                '成功次数': stats['success_count'],
                '成功率(%)': f"{success_rate:.1f}",
                '平均响应时间(ms)': f"{avg_duration:.2f}",
                '最大响应时间(ms)': f"{stats['max_duration']:.2f}" if stats['max_duration'] != 0 else '0',
                '最小响应时间(ms)': f"{stats['min_duration']:.2f}" if stats['min_duration'] != float('inf') else '0'
            })
        
        # 按调用次数排序
        result.sort(key=lambda x: x['调用次数'], reverse=True)
        return result
    
    def _create_error_stats(self, transactions: List[Dict]) -> List[Dict]:
        """创建错误统计数据"""
        error_stats = {}
        
        for transaction in transactions:
            if transaction.get('success', True):
                continue
            
            error_msg = transaction.get('error_message', 'Unknown error')
            status_code = transaction.get('response', {}).get('status_code', 0)
            url = transaction.get('request', {}).get('url', '')
            
            key = f"{status_code}: {error_msg}"
            
            if key not in error_stats:
                error_stats[key] = {
                    'error_type': error_msg,
                    'status_code': status_code,
                    'count': 0,
                    'urls': set()
                }
            
            error_stats[key]['count'] += 1
            error_stats[key]['urls'].add(url)
        
        # 转换为列表格式
        result = []
        for key, stats in error_stats.items():
            result.append({
                '错误类型': stats['error_type'],
                '状态码': stats['status_code'],
                '出现次数': stats['count'],
                '影响URL数': len(stats['urls']),
                '示例URL': list(stats['urls'])[0] if stats['urls'] else ''
            })
        
        # 按出现次数排序
        result.sort(key=lambda x: x['出现次数'], reverse=True)
        return result
    
    def export_summary_report(self, transactions: List[Dict], filename: Optional[str] = None) -> str:
        """导出摘要报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_summary_{timestamp}"
        
        filepath = self.output_dir / f"{filename}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("网络监控摘要报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据条数: {len(transactions)}\n\n")
            
            # 基本统计
            summary_data = self._create_summary_data(transactions)
            f.write("基本统计:\n")
            f.write("-" * 20 + "\n")
            for item in summary_data:
                f.write(f"{item['指标']}: {item['值']}\n")
            f.write("\n")
            
            # API统计
            api_stats = self._create_api_stats(transactions)
            if api_stats:
                f.write("API端点统计 (Top 10):\n")
                f.write("-" * 30 + "\n")
                for i, api in enumerate(api_stats[:10], 1):
                    f.write(f"{i}. {api['API端点']} - 调用{api['调用次数']}次, 成功率{api['成功率(%)']}%\n")
                f.write("\n")
            
            # 错误统计
            error_stats = self._create_error_stats(transactions)
            if error_stats:
                f.write("错误统计:\n")
                f.write("-" * 20 + "\n")
                for error in error_stats:
                    f.write(f"{error['错误类型']} (状态码: {error['状态码']}) - {error['出现次数']}次\n")
        
        logger.info(f"摘要报告导出完成: {filepath}")
        return str(filepath)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的导出格式"""
        return self.supported_formats.copy()

# 示例使用
if __name__ == "__main__":
    exporter = DataExporter()
    
    # 示例数据
    sample_transactions = [
        {
            'transaction_id': 'test-1',
            'session_id': 'session-123',
            'timestamp': '2024-01-01T12:00:00Z',
            'duration_ms': 150.5,
            'success': True,
            'request': {
                'method': 'GET',
                'url': 'https://api.example.com/v1/users',
                'domain': 'api.example.com',
                'path': '/v1/users',
                'endpoint': '/v1/users',
                'is_api': True,
                'api_version': '1'
            },
            'response': {
                'status_code': 200,
                'status_category': 'success',
                'content_type': 'application/json',
                'is_json': True
            },
            'tags': ['api', 'method:get', 'status:success']
        }
    ]
    
    # 导出为不同格式
    json_file = exporter.export_transactions(sample_transactions, 'json')
    csv_file = exporter.export_transactions(sample_transactions, 'csv')
    txt_file = exporter.export_transactions(sample_transactions, 'txt')
    
    print(f"导出完成:")
    print(f"JSON: {json_file}")
    print(f"CSV: {csv_file}")
    print(f"TXT: {txt_file}")
    
    # 导出摘要报告
    summary_file = exporter.export_summary_report(sample_transactions)
    print(f"摘要报告: {summary_file}")