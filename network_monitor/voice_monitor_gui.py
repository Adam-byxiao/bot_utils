#!/usr/bin/env python3
"""
语音代理监控可视化GUI
基于wxPython的实时对话监控界面
"""

import wx
import threading
import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional
import logging

from sync_voice_monitor import SyncVoiceMonitor
from realtime_voice_agent_parser import VoiceMessage

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceMonitorFrame(wx.Frame):
    """语音监控主窗口"""
    
    def __init__(self):
        super().__init__(None, title="语音代理监控器", size=(1000, 700))
        
        # 初始化监控器
        self.monitor = SyncVoiceMonitor()
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # 创建界面
        self.create_ui()
        self.center_on_screen()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def create_ui(self):
        """创建用户界面"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title = wx.StaticText(panel, label="实时语音代理监控")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # 控制面板
        control_panel = self.create_control_panel(panel)
        main_sizer.Add(control_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 状态显示
        self.status_text = wx.StaticText(panel, label="状态: 未连接")
        main_sizer.Add(self.status_text, 0, wx.ALL, 5)
        
        # 创建左右分区的主要内容区域
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧面板 - 原始数据
        left_panel = wx.Panel(panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 左侧标题
        left_label = wx.StaticText(left_panel, label="原始监控数据:")
        left_label_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        left_label.SetFont(left_label_font)
        left_sizer.Add(left_label, 0, wx.ALL, 5)
        
        # 原始数据显示区域
        self.raw_data_text = wx.TextCtrl(
            left_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 350)
        )
        # 设置等宽字体以便更好地显示格式化文本
        raw_font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.raw_data_text.SetFont(raw_font)
        left_sizer.Add(self.raw_data_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # 统计信息
        stats_label = wx.StaticText(left_panel, label="统计信息:")
        left_sizer.Add(stats_label, 0, wx.ALL, 5)
        
        self.stats_text = wx.TextCtrl(
            left_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80)
        )
        left_sizer.Add(self.stats_text, 0, wx.EXPAND | wx.ALL, 5)
        
        left_panel.SetSizer(left_sizer)
        content_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # 右侧面板 - 简化对话
        right_panel = wx.Panel(panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 右侧标题
        right_label = wx.StaticText(right_panel, label="简化对话视图:")
        right_label_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        right_label.SetFont(right_label_font)
        right_sizer.Add(right_label, 0, wx.ALL, 5)
        
        # 简化对话显示区域
        self.conversation_text = wx.TextCtrl(
            right_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(-1, 430)
        )
        # 设置更美观的字体
        conv_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.conversation_text.SetFont(conv_font)
        # 设置背景色为浅色
        self.conversation_text.SetBackgroundColour(wx.Colour(248, 249, 250))
        # 设置文本颜色
        self.conversation_text.SetForegroundColour(wx.Colour(33, 37, 41))
        right_sizer.Add(self.conversation_text, 1, wx.EXPAND | wx.ALL, 5)
        
        right_panel.SetSizer(right_sizer)
        content_sizer.Add(right_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 连接设置
        conn_box = wx.StaticBox(panel, label="连接设置")
        conn_sizer = wx.StaticBoxSizer(conn_box, wx.HORIZONTAL)
        
        conn_sizer.Add(wx.StaticText(panel, label="主机:"), 0, wx.ALL | wx.CENTER, 5)
        self.host_text = wx.TextCtrl(panel, value="localhost", size=(100, -1))
        conn_sizer.Add(self.host_text, 0, wx.ALL, 5)
        
        conn_sizer.Add(wx.StaticText(panel, label="端口:"), 0, wx.ALL | wx.CENTER, 5)
        self.port_text = wx.TextCtrl(panel, value="9222", size=(60, -1))
        conn_sizer.Add(self.port_text, 0, wx.ALL, 5)
        
        sizer.Add(conn_sizer, 0, wx.ALL, 5)
        
        # 控制按钮
        btn_box = wx.StaticBox(panel, label="控制")
        btn_sizer = wx.StaticBoxSizer(btn_box, wx.HORIZONTAL)
        
        self.connect_btn = wx.Button(panel, label="连接")
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        btn_sizer.Add(self.connect_btn, 0, wx.ALL, 5)
        
        self.start_btn = wx.Button(panel, label="开始监控")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_monitoring)
        self.start_btn.Enable(False)
        btn_sizer.Add(self.start_btn, 0, wx.ALL, 5)
        
        self.stop_btn = wx.Button(panel, label="停止监控")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop_monitoring)
        self.stop_btn.Enable(False)
        btn_sizer.Add(self.stop_btn, 0, wx.ALL, 5)
        
        self.export_btn = wx.Button(panel, label="导出对话")
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_conversation)
        self.export_btn.Enable(False)
        btn_sizer.Add(self.export_btn, 0, wx.ALL, 5)
        
        self.clear_btn = wx.Button(panel, label="清空显示")
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_display)
        btn_sizer.Add(self.clear_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 1, wx.ALL, 5)
        
        panel.SetSizer(sizer)
        return panel
    
    def center_on_screen(self):
        """窗口居中显示"""
        self.Center()
    
    def update_status(self, status: str):
        """更新状态显示"""
        wx.CallAfter(self._update_status_ui, status)
    
    def _update_status_ui(self, status: str):
        """在主线程中更新状态UI"""
        self.status_text.SetLabel(f"状态: {status}")
    
    def append_conversation(self, message: str):
        """添加对话内容（线程安全）"""
        wx.CallAfter(self._append_conversation_ui, message)
    
    def _append_conversation_ui(self, message: str):
        """更新对话显示UI（必须在主线程中调用）"""
        current_text = self.conversation_text.GetValue()
        if current_text:
            new_text = current_text + "\n\n" + message
        else:
            new_text = message
        
        self.conversation_text.SetValue(new_text)
        # 滚动到底部
        self.conversation_text.SetInsertionPointEnd()
    
    def append_raw_data(self, message: str):
        """添加原始数据内容（线程安全）"""
        wx.CallAfter(self._append_raw_data_ui, message)
    
    def _append_raw_data_ui(self, message: str):
        """更新原始数据显示UI（必须在主线程中调用）"""
        current_text = self.raw_data_text.GetValue()
        if current_text:
            new_text = current_text + "\n" + message
        else:
            new_text = message
        
        self.raw_data_text.SetValue(new_text)
        # 滚动到底部
        self.raw_data_text.SetInsertionPointEnd()
    
    def update_stats(self, stats: Dict):
        """更新统计信息"""
        wx.CallAfter(self._update_stats_ui, stats)
    
    def _update_stats_ui(self, stats: Dict):
        """在主线程中更新统计UI"""
        stats_text = f"用户输入: {stats.get('input_count', 0)} 条\n"
        stats_text += f"助手输出: {stats.get('output_count', 0)} 条\n"
        stats_text += f"总消息数: {stats.get('total_count', 0)} 条"
        self.stats_text.SetValue(stats_text)
    
    def on_connect(self, event):
        """连接按钮事件"""
        host = self.host_text.GetValue()
        port = int(self.port_text.GetValue())
        
        # 在后台线程中执行连接
        threading.Thread(target=self.connect_to_device, args=(host, port), daemon=True).start()
    
    def connect_to_device(self, host: str, port: int):
        """连接到设备"""
        try:
            self.update_status("正在连接...")
            
            # 更新监控器配置
            self.monitor = SyncVoiceMonitor(chrome_host=host, chrome_port=port)
            
            # 连接到设备（同步监控器已经包含了连接和检查的逻辑）
            success = self.monitor.connect_to_device()
            
            if success:
                self.update_status("已连接 - 语音代理可用")
                wx.CallAfter(self._enable_monitoring_controls, True)
            else:
                self.update_status("连接失败")
                wx.CallAfter(self._enable_monitoring_controls, False)
                
        except Exception as e:
            self.update_status(f"连接错误: {str(e)}")
            wx.CallAfter(self._enable_monitoring_controls, False)
    
    def _enable_monitoring_controls(self, enable: bool):
        """启用/禁用监控控制"""
        self.start_btn.Enable(enable)
        self.export_btn.Enable(enable)
    
    def on_start_monitoring(self, event):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.start_btn.Enable(False)
            self.stop_btn.Enable(True)
            self.update_status("监控中...")
            
            # 启动监控线程
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()
    
    def on_stop_monitoring(self, event):
        """停止监控"""
        self.is_monitoring = False
        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)
        self.update_status("已停止监控")
    
    def monitoring_loop(self):
        """监控循环（在后台线程中运行）"""
        import time
        
        input_count = 0
        output_count = 0
        
        while self.is_monitoring:
            try:
                # 使用同步方式获取会话历史
                history_data = self.monitor.get_session_history()
                
                if history_data:
                    # 解析数据
                    input_messages, output_messages, session_summary = self.monitor.parse_and_classify_data(history_data)
                    
                    # 检查是否有新消息
                    new_input_count = len(input_messages)
                    new_output_count = len(output_messages)
                    
                    if new_input_count > input_count or new_output_count > output_count:
                        # 显示新消息
                        self.display_new_messages(input_messages[input_count:], output_messages[output_count:])
                        
                        input_count = new_input_count
                        output_count = new_output_count
                        
                        # 更新统计
                        self.update_stats({
                            'input_count': input_count,
                            'output_count': output_count,
                            'total_count': input_count + output_count
                        })
                
                # 等待一段时间再次检查
                if self.is_monitoring:
                    time.sleep(2)  # 2秒检查一次
                    
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                if self.is_monitoring:
                    time.sleep(5)  # 错误时等待更长时间
    

    
    def display_new_messages(self, new_input_messages: List[VoiceMessage], new_output_messages: List[VoiceMessage]):
        """显示新消息"""
        # 合并并按时间排序
        all_new_messages = []
        
        for msg in new_input_messages:
            all_new_messages.append(('input', msg))
        
        for msg in new_output_messages:
            all_new_messages.append(('output', msg))
        
        # 按时间戳排序
        all_new_messages.sort(key=lambda x: x[1].timestamp)
        
        # 显示消息
        for msg_type, msg in all_new_messages:
            # 处理时间戳 - 支持多种格式
            try:
                # 尝试解析ISO格式时间戳
                if isinstance(msg.timestamp, str):
                    # 处理ISO格式时间戳
                    if 'T' in msg.timestamp:
                        # ISO格式: 2024-01-01T10:00:00Z 或 2024-01-01T10:00:00.123Z
                        timestamp_str = msg.timestamp.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%H:%M:%S')
                    else:
                        # 可能是其他字符串格式，直接使用
                        formatted_time = msg.timestamp
                else:
                    # 如果是数字，按Unix时间戳处理
                    formatted_time = datetime.fromtimestamp(float(msg.timestamp)).strftime('%H:%M:%S')
            except (ValueError, TypeError) as e:
                # 如果时间戳解析失败，使用当前时间
                logger.warning(f"时间戳解析失败: {msg.timestamp}, 错误: {e}")
                formatted_time = datetime.now().strftime('%H:%M:%S')
            
            # 原始数据格式（左侧）
            raw_msg = f"[{formatted_time}] {msg_type.upper()}: {msg.content}"
            self.append_raw_data(raw_msg)
            
            # 简化对话格式（右侧）
            if msg_type == 'input':
                # 用户消息
                simple_msg = f"👤 用户：\n{msg.content}\n{'─' * 50}"
            else:
                # 助手消息
                simple_msg = f"🤖 助手：\n{msg.content}\n{'─' * 50}"
            
            self.append_conversation(simple_msg)
    
    def on_export_conversation(self, event):
        """导出对话为markdown格式"""
        try:
            # 获取当前对话内容
            conversation_content = self.conversation_text.GetValue()
            
            if not conversation_content.strip():
                wx.MessageBox("没有对话内容可导出", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            # 确保voice_output目录存在
            voice_output_dir = os.path.join(os.path.dirname(__file__), "voice_output")
            os.makedirs(voice_output_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"conversation_{timestamp}.md"
            filepath = os.path.join(voice_output_dir, filename)
            
            # 转换为markdown格式
            markdown_content = self.convert_to_markdown(conversation_content)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            
            wx.MessageBox(f"对话记录已导出为markdown格式:\n{filepath}", "导出成功", wx.OK | wx.ICON_INFORMATION)
                
        except Exception as e:
            wx.MessageBox(f"导出失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def convert_to_markdown(self, conversation_content: str) -> str:
        """将对话内容转换为markdown格式"""
        lines = conversation_content.split('\n')
        markdown_lines = []
        
        # 添加标题
        markdown_lines.append("# 语音代理对话记录")
        markdown_lines.append("")
        markdown_lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")
        
        current_speaker = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("👤 用户："):
                # 保存之前的内容
                if current_speaker and current_content:
                    self.add_speaker_content_to_markdown(markdown_lines, current_speaker, current_content)
                    current_content = []
                
                current_speaker = "用户"
                
            elif line.startswith("🤖 助手："):
                # 保存之前的内容
                if current_speaker and current_content:
                    self.add_speaker_content_to_markdown(markdown_lines, current_speaker, current_content)
                    current_content = []
                
                current_speaker = "助手"
                
            else:
                # 内容行
                if current_speaker:
                    current_content.append(line)
        
        # 添加最后的内容
        if current_speaker and current_content:
            self.add_speaker_content_to_markdown(markdown_lines, current_speaker, current_content)
        
        return '\n'.join(markdown_lines)
    
    def add_speaker_content_to_markdown(self, markdown_lines: list, speaker: str, content: list):
        """添加说话者内容到markdown"""
        if speaker == "用户":
            markdown_lines.append("**用户**：")
        else:
            markdown_lines.append("**助手**：")
        
        markdown_lines.append("")
        
        # 添加内容，每行前面加上引用符号
        for line in content:
            if line.strip():
                markdown_lines.append(f"> {line}")
        
        markdown_lines.append("")
    
    def cleanup_temp_files(self):
        """清理中间文件"""
        try:
            # 清理voice_output目录中的临时文件
            voice_output_dir = "voice_output"
            if os.path.exists(voice_output_dir):
                temp_files = glob.glob(os.path.join(voice_output_dir, "*"))
                for file_path in temp_files:
                    try:
                        os.remove(file_path)
                        logger.info(f"已删除临时文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"删除文件失败 {file_path}: {e}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def on_clear_display(self, event):
        """清空显示内容"""
        self.conversation_text.SetValue("")
        self.raw_data_text.SetValue("")
        self.stats_text.SetValue("")
    
    def on_close(self, event):
        """关闭窗口事件"""
        # 停止监控
        self.is_monitoring = False
        
        # 断开连接
        if hasattr(self, 'monitor'):
            try:
                self.monitor.disconnect()
            except:
                pass
        
        # 关闭窗口
        self.Destroy()


class VoiceMonitorApp(wx.App):
    """语音监控应用程序"""
    
    def OnInit(self):
        frame = VoiceMonitorFrame()
        frame.Show()
        return True


def main():
    """主函数"""
    app = VoiceMonitorApp()
    app.MainLoop()


if __name__ == "__main__":
    main()