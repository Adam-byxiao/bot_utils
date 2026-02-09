#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音对话解析器 - 专门处理 realtimeManager.getHistory() 中的语音消息
支持 input_audio 和 output_audio 的 transcript 提取
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class VoiceDialog:
    """语音对话数据结构"""
    dialog_id: str
    user_input: str  # STT转换后的用户输入文本
    assistant_output: str  # TTS转换前的助手输出文本
    timestamp: str
    raw_data: Dict
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)
    
    def __str__(self) -> str:
        """格式化输出"""
        return f"用户: {self.user_input}\n助手: {self.assistant_output}"

class VoiceDialogParser:
    """语音对话解析器 - 专门处理语音消息的input_audio和output_audio"""
    
    def __init__(self):
        self.dialogs: List[VoiceDialog] = []
        self.raw_messages: List[Dict] = []
        self.session_id: Optional[str] = None
    
    def parse_history_data(self, history_data: Any) -> bool:
        """
        解析历史数据，提取语音对话
        
        Args:
            history_data: 从 realtimeManager.getHistory() 获取的数据
            
        Returns:
            解析是否成功
        """
        try:
            # 清空之前的数据
            self.dialogs.clear()
            self.raw_messages.clear()
            
            # 预处理数据
            processed_data = self._preprocess_data(history_data)
            if not processed_data:
                logger.error("数据预处理失败")
                return False
            
            # 保存原始消息用于调试
            self.raw_messages = processed_data
            
            # 提取会话ID
            self.session_id = self._extract_session_id(processed_data)
            
            # 解析对话
            self._parse_dialogs(processed_data)
            
            logger.info(f"解析完成: 找到 {len(self.dialogs)} 组对话")
            return True
            
        except Exception as e:
            logger.error(f"解析历史数据失败: {e}")
            return False
    
    def _preprocess_data(self, data: Any) -> List[Dict]:
        """预处理数据，提取实际的对话列表"""
        try:
            # 如果数据是字符串，尝试解析为JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.error("历史数据不是有效的JSON格式")
                    return []
            
            # 处理不同的数据格式
            if isinstance(data, dict):
                # 处理包含result字段的情况
                if 'result' in data:
                    result_data = data['result']
                    if isinstance(result_data, dict) and 'result' in result_data:
                        actual_data = result_data['result'].get('value', [])
                    else:
                        actual_data = result_data.get('value', [])
                else:
                    actual_data = data.get('value', [])
            else:
                actual_data = data
            
            # 确保是列表
            if not isinstance(actual_data, list):
                logger.error(f"期望历史数据是列表，但得到: {type(actual_data)}")
                return []
            
            return actual_data
            
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return []
    
    def _extract_session_id(self, messages: List[Dict]) -> str:
        """从消息中提取会话ID"""
        if messages:
            first_msg = messages[0]
            if isinstance(first_msg, dict):
                # 尝试从itemId中提取会话信息
                item_id = first_msg.get('itemId', '')
                if item_id and item_id.startswith('item_'):
                    return f"session_{item_id.split('_')[1]}"
        
        return f"session_{int(datetime.now().timestamp())}"
    
    def _parse_dialogs(self, messages: List[Dict]):
        """解析消息列表，提取完整的对话"""
        user_inputs = []
        assistant_outputs = []
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
                
            # 提取消息类型和内容
            message_type = message.get('type', '')
            role = message.get('role', '')
            
            # 处理用户输入 (input_audio)
            if role == 'user':
                user_text = self._extract_input_audio_content(message)
                if user_text:
                    user_inputs.append({
                        'index': i,
                        'text': user_text,
                        'raw': message
                    })
            
            # 处理助手输出 (output_audio)
            elif role == 'assistant':
                assistant_text = self._extract_output_audio_content(message)
                if assistant_text:
                    assistant_outputs.append({
                        'index': i,
                        'text': assistant_text,
                        'raw': message
                    })
        
        # 配对用户输入和助手输出
        self._pair_dialogs(user_inputs, assistant_outputs)
    
    def _extract_input_audio_content(self, message: Dict) -> Optional[str]:
        """提取input_audio的transcript内容"""
        try:
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'input_audio':
                        transcript = item.get('transcript')
                        if transcript and transcript.strip():
                            return transcript.strip()
            
            # 如果没有找到input_audio，尝试其他字段
            return self._extract_general_content(message)
            
        except Exception as e:
            logger.warning(f"提取input_audio内容失败: {e}")
            return None
    
    def _extract_output_audio_content(self, message: Dict) -> Optional[str]:
        """提取output_audio的transcript内容"""
        try:
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'output_audio':
                        transcript = item.get('transcript')
                        if transcript and transcript.strip():
                            return transcript.strip()
            
            # 如果没有找到output_audio，尝试其他字段
            return self._extract_general_content(message)
            
        except Exception as e:
            logger.warning(f"提取output_audio内容失败: {e}")
            return None
    
    def _extract_general_content(self, message: Dict) -> Optional[str]:
        """提取一般消息内容"""
        try:
            # 尝试各种可能的内容字段
            content_fields = ['content', 'message', 'text', 'data', 'value', 'arguments', 'output']
            
            for field in content_fields:
                if field in message:
                    content = message[field]
                    if isinstance(content, str):
                        return content.strip()
                    elif isinstance(content, dict):
                        return json.dumps(content, ensure_ascii=False)
                    elif isinstance(content, list):
                        # 尝试提取列表中的文本内容
                        texts = []
                        for item in content:
                            if isinstance(item, str):
                                texts.append(item)
                            elif isinstance(item, dict):
                                if 'transcript' in item:
                                    texts.append(item['transcript'])
                                elif 'text' in item:
                                    texts.append(item['text'])
                        if texts:
                            return ' '.join(texts).strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"提取一般内容失败: {e}")
            return None
    
    def _pair_dialogs(self, user_inputs: List[Dict], assistant_outputs: List[Dict]):
        """配对用户输入和助手输出"""
        # 简单的顺序配对
        min_length = min(len(user_inputs), len(assistant_outputs))
        
        for i in range(min_length):
            user_input = user_inputs[i]
            assistant_output = assistant_outputs[i]
            
            # 创建对话对象
            dialog = VoiceDialog(
                dialog_id=f"dialog_{i+1}_{int(datetime.now().timestamp())}",
                user_input=user_input['text'],
                assistant_output=assistant_output['text'],
                timestamp=datetime.now().isoformat(),
                raw_data={
                    'user_input': user_input['raw'],
                    'assistant_output': assistant_output['raw']
                },
                metadata={
                    'user_index': user_input['index'],
                    'assistant_index': assistant_output['index']
                }
            )
            
            self.dialogs.append(dialog)
        
        # 处理不匹配的情况
        if len(user_inputs) > len(assistant_outputs):
            logger.warning(f"有 {len(user_inputs) - len(assistant_outputs)} 条用户输入没有对应的助手回复")
        elif len(assistant_outputs) > len(user_inputs):
            logger.warning(f"有 {len(assistant_outputs) - len(user_inputs)} 条助手回复没有对应的用户输入")
    
    def get_dialogs(self) -> List[VoiceDialog]:
        """获取所有对话"""
        return self.dialogs.copy()
    
    def get_formatted_output(self) -> str:
        """获取格式化的输出"""
        if not self.dialogs:
            return "没有找到对话内容"
        
        output_lines = [f"会话ID: {self.session_id}", f"对话数量: {len(self.dialogs)}", ""]
        
        for i, dialog in enumerate(self.dialogs, 1):
            output_lines.append(f"=== 对话 {i} ===")
            output_lines.append(f"用户: {dialog.user_input}")
            output_lines.append(f"助手: {dialog.assistant_output}")
            output_lines.append("")
        
        return '\n'.join(output_lines)
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """导出为JSON格式"""
        export_data = {
            'session_id': self.session_id,
            'dialogs': [dialog.to_dict() for dialog in self.dialogs],
            'raw_messages': self.raw_messages,
            'export_timestamp': datetime.now().isoformat()
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str

# 测试函数
def test_voice_dialog_parser():
    """测试语音对话解析器"""
    # 你提供的测试数据
    test_data = [
        {
            "itemId": "item_CzH3hZ8xJjoMlREkpwGzl",
            "previousItemId": None,
            "type": "message",
            "role": "user",
            "status": "completed",
            "content": [
                {
                    "type": "input_audio",
                    "audio": None,
                    "transcript": "春节是几号?春节是几号?"
                }
            ]
        },
        {
            "itemId": "item_CzH3lCzEYvKMCTZp8T96j",
            "type": "function_call",
            "status": "completed",
            "arguments": "{  \n  \"query\": \"2026 春节是几月几号\"\n}",
            "name": "search_intelligent",
            "output": "{\"content\": `https://www.baibaidu.com/festivaldate/2026-2-17-101.html?utm_source=openai` )根据国务院办公厅发布的放假安排，春节假期从2月15日（农历腊月二十八，星期日）开始，至2月23日（农历正月初七，星期一）结束，共9天。 ( `https://www.bjfsh.gov.cn/zhxw/fsdt/202511/t20251105_40108387.shtml?utm_source=openai` )其中，2月14日（星期六）和2月28日（星期六）需要上班。 \"}]}"
        },
        {
            "itemId": "item_CzH3pylPPSgoScCSyUO7V",
            "type": "message",
            "role": "assistant",
            "status": "completed",
            "content": [
                {
                    "type": "output_audio",
                    "transcript": "In 2026, the Chinese New Year, or Spring Festival, falls on February 17th. That's the date for the Lunar New Year celebration.",
                    "audio": None
                }
            ]
        }
    ]
    
    parser = VoiceDialogParser()
    
    if parser.parse_history_data(test_data):
        print("解析成功！")
        print("=" * 50)
        print(parser.get_formatted_output())
        print("=" * 50)
        
        # 导出JSON
        json_output = parser.export_to_json()
        print("JSON导出:")
        print(json_output)
    else:
        print("解析失败！")

if __name__ == "__main__":
    test_voice_dialog_parser()