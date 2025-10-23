"""
语音数据导出器
用于将解析后的 realtimeVoiceAgent.session.history 数据按 input/output 分类输出到本地文件
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from realtime_voice_agent_parser import VoiceMessage, SessionSummary


class VoiceDataExporter:
    """语音数据导出器"""
    
    def __init__(self, output_dir: str = "voice_output"):
        """
        初始化导出器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_input_output_files(self, input_messages: List[VoiceMessage], 
                                 output_messages: List[VoiceMessage],
                                 session_summary: SessionSummary = None) -> Dict[str, str]:
        """
        导出 input 和 output 消息到分别的文件
        
        Args:
            input_messages: 用户输入消息列表
            output_messages: 助手输出消息列表
            session_summary: 会话摘要（可选）
            
        Returns:
            包含导出文件路径的字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出文件路径
        input_file = os.path.join(self.output_dir, f"user_inputs_{timestamp}.txt")
        output_file = os.path.join(self.output_dir, f"assistant_outputs_{timestamp}.txt")
        json_file = os.path.join(self.output_dir, f"session_data_{timestamp}.json")
        summary_file = os.path.join(self.output_dir, f"session_summary_{timestamp}.txt")
        
        # 导出用户输入
        self._export_messages_to_text(input_messages, input_file, "用户输入")
        
        # 导出助手输出
        self._export_messages_to_text(output_messages, output_file, "助手输出")
        
        # 导出完整 JSON 数据
        self._export_to_json(input_messages, output_messages, session_summary, json_file)
        
        # 导出会话摘要
        if session_summary:
            self._export_summary(session_summary, summary_file)
        
        return {
            "input_file": input_file,
            "output_file": output_file,
            "json_file": json_file,
            "summary_file": summary_file if session_summary else None
        }
    
    def _export_messages_to_text(self, messages: List[VoiceMessage], 
                                file_path: str, title: str):
        """
        将消息导出到文本文件
        
        Args:
            messages: 消息列表
            file_path: 文件路径
            title: 文件标题
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {title} ===\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"消息总数: {len(messages)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, message in enumerate(messages, 1):
                f.write(f"[{i}] 时间: {message.timestamp}\n")
                f.write(f"    类型: {message.message_type}\n")
                f.write(f"    角色: {message.role}\n")
                f.write(f"    内容: {message.content}\n")
                if message.metadata:
                    f.write(f"    元数据: {json.dumps(message.metadata, ensure_ascii=False, indent=2)}\n")
                f.write("-" * 40 + "\n\n")
    
    def _export_to_json(self, input_messages: List[VoiceMessage], 
                       output_messages: List[VoiceMessage],
                       session_summary: SessionSummary, file_path: str):
        """
        将所有数据导出到 JSON 文件
        
        Args:
            input_messages: 用户输入消息
            output_messages: 助手输出消息
            session_summary: 会话摘要
            file_path: 文件路径
        """
        data = {
            "export_time": datetime.now().isoformat(),
            "session_summary": session_summary.to_dict() if session_summary else None,
            "input_messages": [msg.to_dict() for msg in input_messages],
            "output_messages": [msg.to_dict() for msg in output_messages],
            "statistics": {
                "total_input_messages": len(input_messages),
                "total_output_messages": len(output_messages),
                "total_messages": len(input_messages) + len(output_messages)
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_summary(self, session_summary: SessionSummary, file_path: str):
        """
        导出会话摘要到文本文件
        
        Args:
            session_summary: 会话摘要
            file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=== 会话摘要 ===\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"会话开始时间: {session_summary.start_time}\n")
            f.write(f"会话结束时间: {session_summary.end_time}\n")
            f.write(f"会话持续时间: {session_summary.duration_seconds}秒\n")
            f.write(f"总消息数: {session_summary.total_messages}\n")
            f.write(f"用户输入数: {session_summary.input_messages}\n")
            f.write(f"助手输出数: {session_summary.output_messages}\n\n")
            
            if session_summary.message_types:
                f.write("消息类型统计:\n")
                for msg_type, count in session_summary.message_types.items():
                    f.write(f"  {msg_type}: {count}\n")
                f.write("\n")
            
            if session_summary.metadata:
                f.write("会话元数据:\n")
                f.write(json.dumps(session_summary.metadata, ensure_ascii=False, indent=2))
    
    def export_combined_file(self, input_messages: List[VoiceMessage], 
                           output_messages: List[VoiceMessage],
                           session_summary: SessionSummary = None) -> str:
        """
        导出合并的对话文件（按时间顺序）
        
        Args:
            input_messages: 用户输入消息
            output_messages: 助手输出消息
            session_summary: 会话摘要
            
        Returns:
            导出文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_file = os.path.join(self.output_dir, f"conversation_{timestamp}.txt")
        
        # 合并并按时间排序
        all_messages = input_messages + output_messages
        all_messages.sort(key=lambda x: x.timestamp)
        
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write("=== 完整对话记录 ===\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总消息数: {len(all_messages)}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, message in enumerate(all_messages, 1):
                role_label = "👤 用户" if message.is_user_input() else "🤖 助手"
                f.write(f"[{i}] {role_label} ({message.timestamp})\n")
                f.write(f"{message.content}\n")
                f.write("-" * 40 + "\n\n")
        
        return combined_file
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """
        获取导出统计信息
        
        Returns:
            导出统计信息
        """
        if not os.path.exists(self.output_dir):
            return {"total_files": 0, "files": []}
        
        files = os.listdir(self.output_dir)
        file_info = []
        
        for file in files:
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                file_info.append({
                    "name": file,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return {
            "output_directory": self.output_dir,
            "total_files": len(file_info),
            "files": file_info
        }