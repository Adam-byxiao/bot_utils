#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
realtimeVoiceAgent.session.history 数据解析器
用于解析和分类语音代理的会话历史数据
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class VoiceMessage:
    """语音消息数据结构"""
    message_id: str
    timestamp: str
    message_type: str  # 'input' 或 'output'
    content: str
    role: str  # 'user', 'assistant', 'system' 等
    raw_data: Dict
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)
    
    def is_user_input(self) -> bool:
        """判断是否为用户输入"""
        return self.message_type == 'input' or self.role == 'user'
    
    def is_assistant_output(self) -> bool:
        """判断是否为助手输出"""
        return self.message_type == 'output' or self.role == 'assistant'
    
@dataclass
class SessionSummary:
    """会话摘要数据结构"""
    session_id: str
    total_messages: int
    input_messages: int
    output_messages: int
    start_time: Optional[str]
    end_time: Optional[str]
    duration_seconds: Optional[float]
    message_types: Optional[Dict[str, int]] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)

class RealtimeVoiceAgentParser:
    """realtimeVoiceAgent 历史数据解析器"""
    
    def __init__(self):
        self.input_messages: List[VoiceMessage] = []
        self.output_messages: List[VoiceMessage] = []
        self.all_messages: List[VoiceMessage] = []
        self.session_summary: Optional[SessionSummary] = None
        
    def parse_history_data(self, history_data: Any) -> bool:
        """
        解析历史数据
        
        Args:
            history_data: 从 realtimeVoiceAgent.session.history 获取的数据
            
        Returns:
            解析是否成功
        """
        try:
            # 清空之前的数据
            self.input_messages.clear()
            self.output_messages.clear()
            self.all_messages.clear()
            
            # 如果数据是字符串，尝试解析为JSON
            if isinstance(history_data, str):
                try:
                    history_data = json.loads(history_data)
                except json.JSONDecodeError:
                    logger.error("历史数据不是有效的JSON格式")
                    return False
            
            # 如果数据是字典且包含result字段
            if isinstance(history_data, dict) and 'result' in history_data:
                if 'result' in history_data['result']:
                    actual_data = history_data['result']['result'].get('value', [])
                else:
                    actual_data = history_data['result'].get('value', [])
            else:
                actual_data = history_data
            
            # 确保数据是列表
            if not isinstance(actual_data, list):
                logger.error(f"期望历史数据是列表，但得到: {type(actual_data)}")
                return False
            
            logger.info(f"开始解析 {len(actual_data)} 条历史记录")
            
            # 解析每条消息
            for i, item in enumerate(actual_data):
                message = self._parse_single_message(item, i)
                if message:
                    self.all_messages.append(message)
                    
                    # 按类型分类
                    if message.message_type == 'input':
                        self.input_messages.append(message)
                    elif message.message_type == 'output':
                        self.output_messages.append(message)
            
            # 生成会话摘要
            self._generate_session_summary()
            
            logger.info(f"解析完成: 总计 {len(self.all_messages)} 条消息")
            logger.info(f"输入消息: {len(self.input_messages)} 条")
            logger.info(f"输出消息: {len(self.output_messages)} 条")
            
            return True
            
        except Exception as e:
            logger.error(f"解析历史数据失败: {e}")
            return False
    
    def _parse_single_message(self, item: Any, index: int) -> Optional[VoiceMessage]:
        """
        解析单条消息
        
        Args:
            item: 单条消息数据
            index: 消息索引
            
        Returns:
            解析后的消息对象
        """
        try:
            # 生成消息ID
            message_id = f"msg_{index}_{int(datetime.now().timestamp())}"
            
            # 获取时间戳
            timestamp = self._extract_timestamp(item)
            
            # 确定消息类型和角色
            message_type, role = self._determine_message_type_and_role(item)
            
            # 提取内容
            content = self._extract_content(item)
            
            # 提取元数据
            metadata = None
            if isinstance(item, dict):
                metadata = item.get('metadata', {})
                # 如果没有metadata字段，从其他字段提取有用信息
                if not metadata:
                    metadata = {}
                    for key in ['source', 'confidence', 'duration', 'response_time']:
                        if key in item:
                            metadata[key] = item[key]
            
            return VoiceMessage(
                message_id=message_id,
                timestamp=timestamp,
                message_type=message_type,
                content=content,
                role=role,
                raw_data=item if isinstance(item, dict) else {"data": item},
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"解析第 {index} 条消息失败: {e}")
            return None
    
    def _extract_timestamp(self, item: Any) -> str:
        """提取时间戳"""
        if isinstance(item, dict):
            # 尝试多种可能的时间戳字段
            for field in ['timestamp', 'time', 'created_at', 'date']:
                if field in item:
                    return str(item[field])
        
        # 如果没有找到时间戳，使用当前时间
        return datetime.now().isoformat()
    
    def _determine_message_type_and_role(self, item: Any) -> Tuple[str, str]:
        """
        确定消息类型和角色
        
        Returns:
            (message_type, role) 元组
        """
        if isinstance(item, dict):
            # 检查角色字段
            role = item.get('role', 'unknown')
            
            # 根据角色确定消息类型
            if role in ['user', 'human']:
                return 'input', role
            elif role in ['assistant', 'bot', 'system']:
                return 'output', role
            
            # 检查其他可能的字段
            if 'type' in item:
                msg_type = item['type'].lower()
                if 'input' in msg_type or 'user' in msg_type:
                    return 'input', role
                elif 'output' in msg_type or 'response' in msg_type:
                    return 'output', role
            
            # 检查内容中的模式
            content = self._extract_content(item)
            if self._is_user_input(content):
                return 'input', 'user'
            elif self._is_assistant_output(content):
                return 'output', 'assistant'
        
        # 默认返回
        return 'unknown', 'unknown'
    
    def _extract_content(self, item: Any) -> str:
        """提取消息内容，专门处理语音消息的transcript"""
        if isinstance(item, str):
            return item
        elif isinstance(item, dict):
            # 首先检查是否是语音消息格式
            if 'content' in item and isinstance(item['content'], list):
                # 遍历content数组，查找transcript
                transcripts = []
                for content_item in item['content']:
                    if isinstance(content_item, dict):
                        # 检查是否有transcript字段
                        if 'transcript' in content_item:
                            transcript = content_item['transcript']
                            if transcript and transcript.strip():  # 确保不是空字符串
                                transcripts.append(transcript.strip())
                
                # 如果找到了transcript，返回合并的文本
                if transcripts:
                    return ' '.join(transcripts)
            
            # 如果没有找到transcript，尝试其他字段
            for field in ['content', 'message', 'text', 'data', 'value']:
                if field in item:
                    content = item[field]
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list) and content:
                        # 如果是列表，尝试提取第一个元素的文本
                        first_item = content[0]
                        if isinstance(first_item, dict) and 'transcript' in first_item:
                            return first_item['transcript']
                        elif isinstance(first_item, str):
                            return first_item
                    else:
                        return json.dumps(content, ensure_ascii=False)
        
        # 如果都没有找到，返回JSON字符串
        return json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
    
    def _is_user_input(self, content: str) -> bool:
        """判断是否为用户输入"""
        # 可以根据实际情况调整这些模式
        user_patterns = [
            r'^用户[：:]',
            r'^User[：:]',
            r'^Human[：:]',
            r'^\[用户\]',
            r'^\[User\]'
        ]
        
        for pattern in user_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _is_assistant_output(self, content: str) -> bool:
        """判断是否为助手输出"""
        # 可以根据实际情况调整这些模式
        assistant_patterns = [
            r'^助手[：:]',
            r'^Assistant[：:]',
            r'^Bot[：:]',
            r'^\[助手\]',
            r'^\[Assistant\]',
            r'^\[Bot\]'
        ]
        
        for pattern in assistant_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _generate_session_summary(self):
        """生成会话摘要"""
        if not self.all_messages:
            return
        
        # 提取时间信息
        timestamps = [msg.timestamp for msg in self.all_messages if msg.timestamp]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        
        # 计算持续时间（如果时间戳是ISO格式）
        duration_seconds = None
        if start_time and end_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_seconds = (end_dt - start_dt).total_seconds()
            except:
                pass
        
        self.session_summary = SessionSummary(
            session_id=f"session_{int(datetime.now().timestamp())}",
            total_messages=len(self.all_messages),
            input_messages=len(self.input_messages),
            output_messages=len(self.output_messages),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds
        )
    
    def get_input_messages(self) -> List[VoiceMessage]:
        """获取所有输入消息"""
        return self.input_messages.copy()
    
    def get_output_messages(self) -> List[VoiceMessage]:
        """获取所有输出消息"""
        return self.output_messages.copy()
    
    def get_all_messages(self) -> List[VoiceMessage]:
        """获取所有消息"""
        return self.all_messages.copy()
    
    def get_session_summary(self) -> Optional[SessionSummary]:
        """获取会话摘要"""
        return self.session_summary
    
    def export_to_dict(self) -> Dict:
        """导出为字典格式"""
        return {
            "session_summary": asdict(self.session_summary) if self.session_summary else None,
            "input_messages": [asdict(msg) for msg in self.input_messages],
            "output_messages": [asdict(msg) for msg in self.output_messages],
            "all_messages": [asdict(msg) for msg in self.all_messages],
            "export_timestamp": datetime.now().isoformat()
        }

# 测试代码
if __name__ == "__main__":
    # 模拟测试数据
    test_data = [
        {"role": "user", "content": "你好，我想了解一下产品信息", "timestamp": "2024-01-01T10:00:00Z"},
        {"role": "assistant", "content": "您好！我很乐意为您介绍我们的产品。", "timestamp": "2024-01-01T10:00:05Z"},
        {"role": "user", "content": "价格是多少？", "timestamp": "2024-01-01T10:00:30Z"},
        {"role": "assistant", "content": "我们的产品价格是999元。", "timestamp": "2024-01-01T10:00:35Z"}
    ]
    
    parser = RealtimeVoiceAgentParser()
    
    if parser.parse_history_data(test_data):
        print("解析成功！")
        
        summary = parser.get_session_summary()
        if summary:
            print(f"会话摘要: {asdict(summary)}")
        
        print(f"\n输入消息 ({len(parser.get_input_messages())} 条):")
        for msg in parser.get_input_messages():
            print(f"  - {msg.content}")
        
        print(f"\n输出消息 ({len(parser.get_output_messages())} 条):")
        for msg in parser.get_output_messages():
            print(f"  - {msg.content}")
    else:
        print("解析失败！")