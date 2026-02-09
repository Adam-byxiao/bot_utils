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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoundedPanel(wx.Panel):
    """自定义圆角面板类"""
    def __init__(self, parent, radius=12, bg_color=wx.Colour(255, 255, 255)):
        super().__init__(parent)
        self.radius = radius
        self.bg_color = bg_color
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
    
    def on_erase_background(self, event):
        """阻止默认背景擦除"""
        pass
    
    def on_paint(self, event):
        """绘制圆角矩形和子控件"""
        dc = wx.AutoBufferedPaintDC(self)
        self.draw_rounded_rect(dc)
        
        # 让子控件正常绘制
        event.Skip()
    
    def on_size(self, event):
        """尺寸改变时重绘"""
        self.Refresh()
        event.Skip()
    
    def draw_rounded_rect(self, dc):
        """绘制圆角矩形背景"""
        # 获取面板尺寸
        size = self.GetSize()
        width, height = size.width, size.height
        
        if width <= 0 or height <= 0:
            return
        
        # 清除背景
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        
        # 设置画刷和画笔
        dc.SetBrush(wx.Brush(self.bg_color))
        dc.SetPen(wx.Pen(self.bg_color, 1))
        
        # 绘制圆角矩形
        dc.DrawRoundedRectangle(0, 0, width, height, self.radius)
    
    def set_background_color(self, color):
        """设置背景颜色"""
        self.bg_color = color
        self.Refresh()


class VoiceMonitorFrame(wx.Frame):
    """语音监控主窗口"""
    
    def __init__(self):
        super().__init__(None, title="AI 语音助手监控器", size=(1200, 800))
        
        # 现代化浅色系主题配色
        self.colors = {
            'primary_bg': wx.Colour(255, 255, 255),      # 主背景 - 纯白
            'secondary_bg': wx.Colour(248, 249, 250),    # 次要背景 - 浅灰白
            'toolbar_bg': wx.Colour(248, 249, 250),      # 工具栏背景 - 浅灰白
            'chat_bg': wx.Colour(250, 251, 252),         # 聊天区域背景 - 极浅灰
            'user_bubble': wx.Colour(74, 144, 226),      # 用户消息气泡 - 蓝色
            'assistant_bubble': wx.Colour(240, 242, 245), # 助手消息气泡 - 浅灰
            'accent_green': wx.Colour(40, 167, 69),      # 绿色强调色
            'accent_red': wx.Colour(220, 53, 69),        # 红色强调色
            'accent_orange': wx.Colour(250, 166, 26),    # 橙色强调色
            'text_primary': wx.Colour(33, 37, 41),       # 主要文字 - 深色
            'text_secondary': wx.Colour(108, 117, 125),  # 次要文字 - 中灰
            'text_muted': wx.Colour(134, 142, 150),      # 静音文字
            'border': wx.Colour(222, 226, 230),          # 边框颜色
            'hover': wx.Colour(233, 236, 239),           # 悬停效果
        }
        
        # 初始化监控器
        self.monitor = SyncVoiceMonitor()
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # 对话历史记录
        self.conversation_history = []
        
        # 创建界面
        self.create_ui()
        self.center_on_screen()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def create_ui(self):
        """创建现代化AI聊天界面"""
        # 设置窗口背景色
        self.SetBackgroundColour(self.colors['primary_bg'])
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 主面板
        panel = wx.Panel(self)
        panel.SetBackgroundColour(self.colors['primary_bg'])  # 深色背景
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部工具栏 - 简化的连接控制
        toolbar = self.create_modern_toolbar(panel)
        main_sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 0)
        
        # 状态栏 - 现代化深色样式
        status_panel = wx.Panel(panel)
        status_panel.SetBackgroundColour(self.colors['secondary_bg'])
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.status_text = wx.StaticText(status_panel, label="● 未连接")
        # 使用现代化状态字体
        status_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM, faceName="Segoe UI")
        self.status_text.SetFont(status_font)
        self.status_text.SetForegroundColour(self.colors['text_secondary'])
        status_sizer.Add(self.status_text, 0, wx.ALL | wx.CENTER, 12)
        
        status_sizer.AddStretchSpacer()
        status_panel.SetSizer(status_sizer)
        main_sizer.Add(status_panel, 0, wx.EXPAND, 0)
        
        # 主对话区域 - 现代化深色聊天应用风格
        chat_panel = wx.Panel(panel)
        chat_panel.SetBackgroundColour(self.colors['chat_bg'])
        chat_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 对话标题
        chat_title = wx.StaticText(chat_panel, label="🤖 AI 语音助手对话")
        # 使用现代化标题字体
        title_font = wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Segoe UI")
        chat_title.SetFont(title_font)
        chat_title.SetForegroundColour(self.colors['text_primary'])
        chat_sizer.Add(chat_title, 0, wx.ALL | wx.CENTER, 24)
        
        # 对话显示区域 - 使用滚动窗口
        self.chat_scroll = wx.ScrolledWindow(chat_panel, style=wx.VSCROLL | wx.BORDER_NONE)
        self.chat_scroll.SetScrollRate(0, 20)
        self.chat_scroll.SetBackgroundColour(self.colors['chat_bg'])
        
        # 对话内容面板
        self.chat_content_panel = wx.Panel(self.chat_scroll)
        self.chat_content_panel.SetBackgroundColour(self.colors['chat_bg'])
        self.chat_content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.chat_content_panel.SetSizer(self.chat_content_sizer)
        
        # 滚动窗口的sizer
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        scroll_sizer.Add(self.chat_content_panel, 1, wx.EXPAND | wx.ALL, 20)
        self.chat_scroll.SetSizer(scroll_sizer)
        
        chat_sizer.Add(self.chat_scroll, 1, wx.EXPAND | wx.ALL, 10)
        chat_panel.SetSizer(chat_sizer)
        
        main_sizer.Add(chat_panel, 1, wx.EXPAND, 0)
        
        panel.SetSizer(main_sizer)
        
        # 初始化原始数据存储（隐藏但保留功能）
        self.raw_data_content = ""
        self.stats_content = ""
        
        # 添加初始欢迎消息
        self.add_welcome_message()
    
    def add_welcome_message(self):
        """添加现代化浅色主题欢迎消息"""
        welcome_panel = wx.Panel(self.chat_content_panel)
        welcome_panel.SetBackgroundColour(self.colors['chat_bg'])
        welcome_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 欢迎图标
        icon_text = wx.StaticText(welcome_panel, label="🚀")
        icon_font = wx.Font(48, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI Emoji")
        icon_text.SetFont(icon_font)
        welcome_sizer.Add(icon_text, 0, wx.ALL | wx.CENTER, 20)
        
        # 欢迎标题
        title_text = wx.StaticText(welcome_panel, label="欢迎使用 AI 语音助手监控工具")
        title_font = wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, faceName="Segoe UI")
        title_text.SetFont(title_font)
        title_text.SetForegroundColour(self.colors['text_primary'])
        welcome_sizer.Add(title_text, 0, wx.ALL | wx.CENTER, 10)
        
        # 欢迎描述
        desc_text = wx.StaticText(welcome_panel, label="请连接设备并开始监控以查看实时对话内容\n\n🔄 实时监控 | 📊 数据分析", style=wx.ALIGN_CENTER)
        desc_font = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
        desc_text.SetFont(desc_font)
        desc_text.SetForegroundColour(self.colors['text_secondary'])
        welcome_sizer.Add(desc_text, 0, wx.ALL | wx.CENTER, 15)
        
        welcome_panel.SetSizer(welcome_sizer)
        
        self.chat_content_sizer.Add(welcome_panel, 1, wx.EXPAND | wx.ALL, 30)
        
        self.chat_content_panel.Layout()
        self.chat_scroll.FitInside()
    
    def add_assistant_message(self, message):
        """添加助手消息"""
        # 创建消息容器
        msg_container = wx.Panel(self.chat_content_panel)
        msg_container.SetBackgroundColour(self.colors['chat_bg'])
        container_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧间距
        container_sizer.Add((20, 0))
        
        # 创建助手头像区域 - 现代化圆形头像
        avatar_panel = RoundedPanel(msg_container, radius=20, bg_color=self.colors['accent_green'])
        avatar_panel.SetMinSize((40, 40))
        avatar_panel.SetMaxSize((40, 40))
        
        # 添加AI图标
        avatar_sizer = wx.BoxSizer(wx.VERTICAL)
        avatar_text = wx.StaticText(avatar_panel, label="🤖")
        avatar_font = wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI Emoji")
        avatar_text.SetFont(avatar_font)
        avatar_text.SetBackgroundColour(self.colors['accent_green'])
        avatar_sizer.Add(avatar_text, 1, wx.ALIGN_CENTER | wx.ALL, 8)
        avatar_panel.SetSizer(avatar_sizer)
        
        container_sizer.Add(avatar_panel, 0, wx.ALL | wx.ALIGN_TOP, 12)
        
        # 创建助手消息气泡 - 现代化圆角效果
        bubble_panel = RoundedPanel(msg_container, radius=18, bg_color=self.colors['assistant_bubble'])
        bubble_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 格式化消息文本
        formatted_message = self.format_message_text(message, max_width=60)
        
        # 创建消息文本
        msg_text = wx.StaticText(bubble_panel, label=formatted_message)
        msg_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
        msg_text.SetFont(msg_font)
        msg_text.SetForegroundColour(self.colors['text_primary'])
        msg_text.SetBackgroundColour(self.colors['assistant_bubble'])
        msg_text.Wrap(500)
        
        bubble_sizer.Add(msg_text, 0, wx.ALL, 18)
        bubble_panel.SetSizer(bubble_sizer)
        
        container_sizer.Add(bubble_panel, 0, wx.ALL, 12)
        container_sizer.AddStretchSpacer(1)
        
        msg_container.SetSizer(container_sizer)
        
        # 添加到聊天内容面板
        self.chat_content_sizer.Add(msg_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # 添加消息间距
        self.chat_content_sizer.Add((0, 12))
        
        # 刷新布局
        self.chat_content_panel.Layout()
        self.chat_scroll.FitInside()
        
        # 滚动到底部
        self.chat_scroll.Scroll(0, self.chat_scroll.GetVirtualSize()[1])
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        export_item = file_menu.Append(wx.ID_ANY, "导出对话\tCtrl+E", "导出对话为Markdown文件")
        clear_item = file_menu.Append(wx.ID_ANY, "清空对话\tCtrl+L", "清空当前对话内容")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "退出\tCtrl+Q", "退出应用程序")
        menubar.Append(file_menu, "文件")
        
        # 查看菜单
        view_menu = wx.Menu()
        self.raw_data_item = view_menu.Append(wx.ID_ANY, "显示原始数据", "显示原始监控数据窗口", wx.ITEM_CHECK)
        self.stats_item = view_menu.Append(wx.ID_ANY, "显示统计信息", "显示统计信息窗口", wx.ITEM_CHECK)
        menubar.Append(view_menu, "查看")
        
        # 连接菜单
        connect_menu = wx.Menu()
        connect_item = connect_menu.Append(wx.ID_ANY, "连接设备\tCtrl+C", "连接到远程设备")
        disconnect_item = connect_menu.Append(wx.ID_ANY, "断开连接\tCtrl+D", "断开设备连接")
        connect_menu.AppendSeparator()
        start_monitor_item = connect_menu.Append(wx.ID_ANY, "开始监控\tCtrl+S", "开始监控语音对话")
        stop_monitor_item = connect_menu.Append(wx.ID_ANY, "停止监控\tCtrl+T", "停止监控语音对话")
        menubar.Append(connect_menu, "连接")
        
        self.SetMenuBar(menubar)
        
        # 绑定菜单事件
        self.Bind(wx.EVT_MENU, self.on_export_conversation, export_item)
        self.Bind(wx.EVT_MENU, self.on_clear_display, clear_item)
        self.Bind(wx.EVT_MENU, self.on_close, exit_item)
        self.Bind(wx.EVT_MENU, self.on_show_raw_data, self.raw_data_item)
        self.Bind(wx.EVT_MENU, self.on_show_stats, self.stats_item)
        self.Bind(wx.EVT_MENU, self.on_connect, connect_item)
        self.Bind(wx.EVT_MENU, self.on_disconnect, disconnect_item)
        self.Bind(wx.EVT_MENU, self.on_start_monitoring, start_monitor_item)
        self.Bind(wx.EVT_MENU, self.on_stop_monitoring, stop_monitor_item)
    
    def create_modern_toolbar(self, parent):
        """创建现代化深色工具栏"""
        toolbar_panel = wx.Panel(parent)
        toolbar_panel.SetBackgroundColour(self.colors['toolbar_bg'])
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 添加左侧间距
        toolbar_sizer.Add((20, 0))
        
        # 连接设置区域
        conn_label = wx.StaticText(toolbar_panel, label="🔗 设备连接:")
        # 使用现代化标签字体
        conn_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM, faceName="Segoe UI")
        conn_label.SetFont(conn_font)
        conn_label.SetForegroundColour(self.colors['text_primary'])
        toolbar_sizer.Add(conn_label, 0, wx.ALL | wx.CENTER, 12)
        
        # 现代化浅色输入框样式
        self.host_text = wx.TextCtrl(toolbar_panel, value="localhost", size=(140, 32), style=wx.BORDER_SIMPLE)
        self.host_text.SetBackgroundColour(wx.Colour(255, 255, 255))  # 纯白背景
        self.host_text.SetForegroundColour(self.colors['text_primary'])
        input_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
        self.host_text.SetFont(input_font)
        toolbar_sizer.Add(self.host_text, 0, wx.ALL | wx.CENTER, 8)
        
        colon_label = wx.StaticText(toolbar_panel, label=":")
        colon_label.SetForegroundColour(self.colors['text_secondary'])
        colon_label.SetFont(input_font)
        toolbar_sizer.Add(colon_label, 0, wx.ALL | wx.CENTER, 4)
        
        self.port_text = wx.TextCtrl(toolbar_panel, value="9222", size=(70, 32), style=wx.BORDER_SIMPLE)
        self.port_text.SetBackgroundColour(wx.Colour(255, 255, 255))  # 纯白背景
        self.port_text.SetForegroundColour(self.colors['text_primary'])
        self.port_text.SetFont(input_font)
        toolbar_sizer.Add(self.port_text, 0, wx.ALL | wx.CENTER, 8)
        
        # 添加分隔符
        toolbar_sizer.Add((20, 0))
        
        # 现代化按钮样式
        btn_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM, faceName="Segoe UI")
        
        # 连接按钮
        self.connect_btn = wx.Button(toolbar_panel, label="🔌 连接", size=(90, 36))
        self.connect_btn.SetBackgroundColour(self.colors['user_bubble'])
        self.connect_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.connect_btn.SetFont(btn_font)
        toolbar_sizer.Add(self.connect_btn, 0, wx.ALL | wx.CENTER, 6)
        
        # 监控按钮
        self.start_btn = wx.Button(toolbar_panel, label="▶️ 开始", size=(90, 36))
        self.start_btn.SetBackgroundColour(self.colors['accent_green'])
        self.start_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.start_btn.SetFont(btn_font)
        self.start_btn.Enable(False)
        toolbar_sizer.Add(self.start_btn, 0, wx.ALL | wx.CENTER, 6)
        
        self.stop_btn = wx.Button(toolbar_panel, label="⏹️ 停止", size=(90, 36))
        self.stop_btn.SetBackgroundColour(self.colors['accent_red'])
        self.stop_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.stop_btn.SetFont(btn_font)
        self.stop_btn.Enable(False)
        toolbar_sizer.Add(self.stop_btn, 0, wx.ALL | wx.CENTER, 6)
        
        toolbar_sizer.AddStretchSpacer()
        
        # 导出按钮
        export_btn = wx.Button(toolbar_panel, label="导出对话", size=(80, 32))
        export_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        export_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        export_btn.SetFont(btn_font)
        toolbar_sizer.Add(export_btn, 0, wx.ALL | wx.CENTER, 5)
        
        # 清空按钮
        clear_btn = wx.Button(toolbar_panel, label="清空", size=(60, 32))
        clear_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        clear_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        clear_btn.SetFont(btn_font)
        toolbar_sizer.Add(clear_btn, 0, wx.ALL | wx.CENTER, 5)
        
        toolbar_panel.SetSizer(toolbar_sizer)
        
        # 绑定事件
        self.Bind(wx.EVT_BUTTON, self.on_connect, self.connect_btn)
        self.Bind(wx.EVT_BUTTON, self.on_start_monitoring, self.start_btn)
        self.Bind(wx.EVT_BUTTON, self.on_stop_monitoring, self.stop_btn)
        self.Bind(wx.EVT_BUTTON, self.on_export_conversation, export_btn)
        self.Bind(wx.EVT_BUTTON, self.on_clear_display, clear_btn)
        
        return toolbar_panel
    
    def create_control_panel(self, parent):
        """创建现代化控制面板"""
        control_panel = wx.Panel(parent)
        control_panel.SetBackgroundColour(self.colors['toolbar_bg'])
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 添加左侧间距
        control_sizer.Add((20, 0))
        
        # 现代化按钮字体
        btn_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM, faceName="Segoe UI")
        
        # 连接设置区域
        conn_label = wx.StaticText(control_panel, label="🔗 设备连接:")
        conn_label.SetFont(btn_font)
        conn_label.SetForegroundColour(self.colors['text_primary'])
        control_sizer.Add(conn_label, 0, wx.ALL | wx.CENTER, 12)
        
        # 现代化浅色输入框样式
        self.host_text = wx.TextCtrl(control_panel, value="localhost", size=(140, 32), style=wx.BORDER_SIMPLE)
        self.host_text.SetBackgroundColour(wx.Colour(255, 255, 255))  # 纯白背景
        self.host_text.SetForegroundColour(self.colors['text_primary'])
        input_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
        self.host_text.SetFont(input_font)
        control_sizer.Add(self.host_text, 0, wx.ALL | wx.CENTER, 8)
        
        colon_label = wx.StaticText(control_panel, label=":")
        colon_label.SetForegroundColour(self.colors['text_secondary'])
        colon_label.SetFont(input_font)
        control_sizer.Add(colon_label, 0, wx.ALL | wx.CENTER, 4)
        
        self.port_text = wx.TextCtrl(control_panel, value="9222", size=(70, 32), style=wx.BORDER_SIMPLE)
        self.port_text.SetBackgroundColour(wx.Colour(255, 255, 255))  # 纯白背景
        self.port_text.SetForegroundColour(self.colors['text_primary'])
        self.port_text.SetFont(input_font)
        control_sizer.Add(self.port_text, 0, wx.ALL | wx.CENTER, 8)
        
        # 添加分隔符
        control_sizer.Add((20, 0))
        
        # 连接按钮
        self.connect_btn = wx.Button(control_panel, label="🔌 连接", size=(90, 36))
        self.connect_btn.SetBackgroundColour(self.colors['user_bubble'])
        self.connect_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.connect_btn.SetFont(btn_font)
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)
        control_sizer.Add(self.connect_btn, 0, wx.ALL | wx.CENTER, 6)
        
        # 监控按钮
        self.start_btn = wx.Button(control_panel, label="▶️ 开始", size=(90, 36))
        self.start_btn.SetBackgroundColour(self.colors['accent_green'])
        self.start_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.start_btn.SetFont(btn_font)
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_monitoring)
        self.start_btn.Enable(False)
        control_sizer.Add(self.start_btn, 0, wx.ALL | wx.CENTER, 6)
        
        self.stop_btn = wx.Button(control_panel, label="⏹️ 停止", size=(90, 36))
        self.stop_btn.SetBackgroundColour(self.colors['accent_red'])
        self.stop_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.stop_btn.SetFont(btn_font)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop_monitoring)
        self.stop_btn.Enable(False)
        control_sizer.Add(self.stop_btn, 0, wx.ALL | wx.CENTER, 6)
        
        control_sizer.AddStretchSpacer()
        
        # 导出按钮
        self.export_btn = wx.Button(control_panel, label="📤 导出对话", size=(120, 36))
        self.export_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        self.export_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.export_btn.SetFont(btn_font)
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_conversation)
        self.export_btn.Enable(False)
        control_sizer.Add(self.export_btn, 0, wx.ALL | wx.CENTER, 5)
        
        # 清空按钮
        self.clear_btn = wx.Button(control_panel, label="🗑️ 清空显示", size=(120, 36))
        self.clear_btn.SetBackgroundColour(wx.Colour(108, 117, 125))
        self.clear_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.clear_btn.SetFont(btn_font)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_display)
        control_sizer.Add(self.clear_btn, 0, wx.ALL | wx.CENTER, 5)
        
        control_panel.SetSizer(control_sizer)
        return control_panel
    
    def center_on_screen(self):
        """窗口居中显示"""
        self.Center()
    
    def update_status(self, status: str):
        """更新状态显示（线程安全）"""
        wx.CallAfter(self._update_status_ui, status)
    
    def _update_status_ui(self, status: str):
        """更新状态显示UI（必须在主线程中调用）"""
        # 根据状态设置不同的颜色
        if "已连接" in status:
            self.status_text.SetForegroundColour(wx.Colour(40, 167, 69))  # 绿色
        elif "监控中" in status:
            self.status_text.SetForegroundColour(wx.Colour(0, 123, 255))  # 蓝色
        elif "错误" in status or "失败" in status:
            self.status_text.SetForegroundColour(wx.Colour(220, 53, 69))  # 红色
        else:
            self.status_text.SetForegroundColour(wx.Colour(108, 117, 125))  # 灰色
        
        self.status_text.SetLabel(status)
    
    def format_message_text(self, text: str, max_width: int = 50) -> str:
        """格式化消息文本，优化段落和换行"""
        if not text:
            return text
        
        # 处理已有的换行符
        paragraphs = text.split('\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                formatted_paragraphs.append('')
                continue
            
            # 对于长段落，进行智能换行
            if len(paragraph) > max_width:
                words = paragraph.split(' ')
                lines = []
                current_line = []
                current_length = 0
                
                for word in words:
                    # 如果单词本身就很长，直接添加
                    if len(word) > max_width:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = []
                            current_length = 0
                        lines.append(word)
                    # 如果添加这个单词会超过最大宽度
                    elif current_length + len(word) + 1 > max_width:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                    else:
                        current_line.append(word)
                        current_length += len(word) + (1 if current_line else 0)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                formatted_paragraphs.extend(lines)
            else:
                formatted_paragraphs.append(paragraph)
        
        return '\n'.join(formatted_paragraphs)

    def append_conversation(self, message: str):
        """添加对话内容（线程安全）"""
        # 注意：对话历史记录现在由display_single_message方法处理
        # 这里只负责UI显示
        wx.CallAfter(self._append_conversation_ui, message)
    
    def _append_conversation_ui(self, message: str):
        """更新对话显示UI（必须在主线程中调用）"""
        # 创建消息容器
        msg_container = wx.Panel(self.chat_content_panel)
        msg_container.SetBackgroundColour(self.colors['chat_bg'])
        container_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 解析消息类型和内容
        is_user = "👤 用户" in message
        
        if is_user:
            # 用户消息 - 右对齐
            container_sizer.AddStretchSpacer(1)  # 左侧弹性空间
            
            # 创建用户消息气泡 - 现代化圆角效果
            bubble_panel = RoundedPanel(msg_container, radius=18, bg_color=self.colors['user_bubble'])
            bubble_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 清理消息文本
            clean_message = message.replace("👤 用户", "").strip()
            if clean_message.startswith("(") and ")" in clean_message:
                clean_message = clean_message.split(")", 1)[1].strip()
            
            # 优化段落格式 - 处理长文本和换行
            formatted_message = self.format_message_text(clean_message, max_width=50)
            
            # 创建消息文本
            msg_text = wx.StaticText(bubble_panel, label=formatted_message)
            # 使用更现代的字体 - 微软雅黑或系统默认无衬线字体
            msg_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
            msg_text.SetFont(msg_font)
            msg_text.SetForegroundColour(wx.Colour(255, 255, 255))  # 保持白色文字（蓝色气泡配白字）
            msg_text.SetBackgroundColour(self.colors['user_bubble'])
            msg_text.Wrap(400)  # 限制宽度
            
            bubble_sizer.Add(msg_text, 0, wx.ALL, 18)  # 增加内边距
            bubble_panel.SetSizer(bubble_sizer)
            
            container_sizer.Add(bubble_panel, 0, wx.ALL, 12)  # 增加外边距
            container_sizer.Add((20, 0))  # 右侧间距
            
        else:
            # 助手消息 - 左对齐
            container_sizer.Add((20, 0))  # 左侧间距
            
            # 创建助手头像区域 - 现代化圆形头像
            avatar_panel = RoundedPanel(msg_container, radius=20, bg_color=self.colors['accent_green'])
            avatar_panel.SetMinSize((40, 40))
            avatar_panel.SetMaxSize((40, 40))
            
            # 添加AI图标
            avatar_sizer = wx.BoxSizer(wx.VERTICAL)
            avatar_text = wx.StaticText(avatar_panel, label="🤖")
            # 使用更大的头像字体
            avatar_font = wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI Emoji")
            avatar_text.SetFont(avatar_font)
            avatar_text.SetBackgroundColour(self.colors['accent_green'])
            avatar_sizer.Add(avatar_text, 1, wx.ALIGN_CENTER | wx.ALL, 8)
            avatar_panel.SetSizer(avatar_sizer)
            
            container_sizer.Add(avatar_panel, 0, wx.ALL | wx.ALIGN_TOP, 12)
            
            # 创建助手消息气泡 - 现代化圆角效果
            bubble_panel = RoundedPanel(msg_container, radius=18, bg_color=self.colors['assistant_bubble'])
            bubble_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # 清理消息文本
            clean_message = message.replace("🤖 助手", "").strip()
            if clean_message.startswith("(") and ")" in clean_message:
                clean_message = clean_message.split(")", 1)[1].strip()
            
            # 优化段落格式 - 处理长文本和换行
            formatted_message = self.format_message_text(clean_message, max_width=60)
            
            # 创建消息文本
            msg_text = wx.StaticText(bubble_panel, label=formatted_message)
            # 使用更现代的字体 - 微软雅黑或系统默认无衬线字体
            msg_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Segoe UI")
            msg_text.SetFont(msg_font)
            msg_text.SetForegroundColour(self.colors['text_primary'])  # 深色文字适配浅色气泡
            msg_text.SetBackgroundColour(self.colors['assistant_bubble'])
            msg_text.Wrap(500)  # 限制宽度
            
            bubble_sizer.Add(msg_text, 0, wx.ALL, 18)  # 增加内边距
            bubble_panel.SetSizer(bubble_sizer)
            
            container_sizer.Add(bubble_panel, 0, wx.ALL, 12)  # 增加外边距
            container_sizer.AddStretchSpacer(1)  # 右侧弹性空间
        
        msg_container.SetSizer(container_sizer)
        
        # 添加到聊天内容面板
        self.chat_content_sizer.Add(msg_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # 添加消息间距
        self.chat_content_sizer.Add((0, 12))
        
        # 刷新布局
        self.chat_content_panel.Layout()
        self.chat_scroll.FitInside()
        
        # 滚动到底部
        self.chat_scroll.Scroll(0, self.chat_scroll.GetVirtualSize()[1])
    
    def append_raw_data(self, message: str):
        """添加原始数据内容（线程安全）"""
        wx.CallAfter(self._append_raw_data_ui, message)
    
    def _append_raw_data_ui(self, message: str):
        """更新原始数据显示UI（必须在主线程中调用）"""
        if hasattr(self, 'raw_data_content'):
            if self.raw_data_content:
                self.raw_data_content += "\n" + message
            else:
                self.raw_data_content = message
        else:
            self.raw_data_content = message
    
    def update_stats(self, stats: Dict):
        """更新统计信息"""
        wx.CallAfter(self._update_stats_ui, stats)
    
    def _update_stats_ui(self, stats: Dict):
        """在主线程中更新统计UI"""
        stats_text = f"用户输入: {stats.get('input_count', 0)} 条\n"
        stats_text += f"助手输出: {stats.get('output_count', 0)} 条\n"
        stats_text += f"总消息数: {stats.get('total_count', 0)} 条"
        self.stats_content = stats_text
    
    def on_connect(self, event):
        """连接按钮事件"""
        if self.connect_btn.GetLabel() == "连接":
            host = self.host_text.GetValue()
            port = int(self.port_text.GetValue())
            
            # 在后台线程中执行连接
            threading.Thread(target=self.connect_to_device, args=(host, port), daemon=True).start()
        else:
            # 断开连接
            self.on_disconnect(event)
    
    def connect_to_device(self, host: str, port: int):
        """连接到设备"""
        try:
            self.update_status("正在连接...")
            
            # 更新监控器配置
            self.monitor = SyncVoiceMonitor(chrome_host=host, chrome_port=port)
            
            # 连接到设备（同步监控器已经包含了连接和检查的逻辑）
            success = self.monitor.connect_to_device()
            
            if success:
                self.update_status("● 已连接 - 语音代理可用")
                wx.CallAfter(self._enable_monitoring_controls, True)
                wx.CallAfter(self._update_connect_button, True)
            else:
                self.update_status("● 连接失败")
                wx.CallAfter(self._enable_monitoring_controls, False)
                
        except Exception as e:
            self.update_status(f"连接错误: {str(e)}")
            wx.CallAfter(self._enable_monitoring_controls, False)
    
    def _enable_monitoring_controls(self, enable: bool):
        """启用/禁用监控控制"""
        self.start_btn.Enable(enable)
    
    def _update_connect_button(self, connected: bool):
        """更新连接按钮状态"""
        if connected:
            self.connect_btn.SetLabel("断开连接")
            self.connect_btn.SetBackgroundColour(wx.Colour(220, 53, 69))
        else:
            self.connect_btn.SetLabel("连接")
            self.connect_btn.SetBackgroundColour(wx.Colour(0, 123, 255))
    
    def on_show_raw_data(self, event):
        """显示原始数据窗口"""
        if self.raw_data_item.IsChecked():
            self.show_raw_data_dialog()
        
    def on_show_stats(self, event):
        """显示统计信息窗口"""
        if self.stats_item.IsChecked():
            self.show_stats_dialog()
    
    def on_disconnect(self, event):
        """断开连接"""
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor = None
            self.update_status("● 已断开连接")
            self._enable_monitoring_controls(False)
            self._update_connect_button(False)
    
    def show_raw_data_dialog(self):
        """显示原始数据对话框"""
        dialog = wx.Dialog(self, title="原始监控数据", size=(800, 600))
        panel = wx.Panel(dialog)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        text_ctrl.SetValue(self.raw_data_content)
        # 使用更现代的等宽字体
        raw_font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Consolas")
        text_ctrl.SetFont(raw_font)
        
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        close_btn = wx.Button(panel, wx.ID_CLOSE, "关闭")
        sizer.Add(close_btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        dialog.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CLOSE), close_btn)
        dialog.ShowModal()
        dialog.Destroy()
        
        # 取消菜单项选中状态
        self.raw_data_item.Check(False)
    
    def show_stats_dialog(self):
        """显示统计信息对话框"""
        dialog = wx.Dialog(self, title="统计信息", size=(400, 300))
        panel = wx.Panel(dialog)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        text_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        text_ctrl.SetValue(self.stats_content)
        
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        close_btn = wx.Button(panel, wx.ID_CLOSE, "关闭")
        sizer.Add(close_btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        dialog.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CLOSE), close_btn)
        dialog.ShowModal()
        dialog.Destroy()
        
        # 取消菜单项选中状态
        self.stats_item.Check(False)
    
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
        
        # 使用集合来跟踪已处理的消息（基于时间戳和内容的哈希）
        processed_messages = set()
        
        # UI更新限流变量
        last_ui_update_time = 0
        ui_update_interval = 2.0  # 最少2秒更新一次UI
        pending_messages = []  # 待处理的消息队列
        
        while self.is_monitoring:
            try:
                # 使用同步方式获取会话历史
                history_data = self.monitor.get_session_history()
                
                if history_data:
                    # 解析数据
                    input_messages, output_messages, session_summary = self.monitor.parse_and_classify_data(history_data)
                    
                    # 合并所有消息并按时间排序
                    all_messages = []
                    
                    for msg in input_messages:
                        all_messages.append(('input', msg))
                    
                    for msg in output_messages:
                        all_messages.append(('output', msg))
                    
                    # 按时间戳排序 - 处理字符串格式的时间戳
                    def get_sort_key(msg_tuple):
                        msg_type, msg = msg_tuple
                        timestamp = msg.timestamp
                        if isinstance(timestamp, str):
                            try:
                                # 尝试解析ISO格式时间戳进行排序
                                if 'T' in timestamp:
                                    timestamp_str = timestamp.replace('Z', '+00:00')
                                    return datetime.fromisoformat(timestamp_str)
                                else:
                                    # 如果不是ISO格式，直接按字符串排序
                                    return timestamp
                            except (ValueError, AttributeError):
                                # 解析失败时使用原始字符串
                                return timestamp
                        else:
                            return timestamp
                    
                    all_messages.sort(key=get_sort_key)
                    
                    # 收集新消息到待处理队列
                    new_messages_found = False
                    for msg_type, msg in all_messages:
                        # 创建消息唯一标识符
                        msg_id = f"{msg.timestamp}_{msg_type}_{hash(msg.content[:100])}"
                        
                        if msg_id not in processed_messages:
                            # 这是新消息，添加到待处理队列
                            pending_messages.append((msg_type, msg))
                            processed_messages.add(msg_id)
                            new_messages_found = True
                    
                    # 检查是否需要更新UI（限流机制）
                    current_time = time.time()
                    should_update_ui = (
                        new_messages_found and 
                        (current_time - last_ui_update_time >= ui_update_interval or len(pending_messages) >= 5)
                    )
                    
                    if should_update_ui and pending_messages:
                        # 批量处理待处理的消息
                        self.display_batch_messages(pending_messages)
                        
                        # 更新统计
                        total_input = len(input_messages)
                        total_output = len(output_messages)
                        self.update_stats({
                            'input_count': total_input,
                            'output_count': total_output,
                            'total_count': total_input + total_output
                        })
                        
                        # 清空待处理队列并更新时间
                        pending_messages.clear()
                        last_ui_update_time = current_time
                
                # 等待一段时间再次检查
                if self.is_monitoring:
                    time.sleep(3)  # 增加到3秒检查一次，减少频率
                    
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                if self.is_monitoring:
                    time.sleep(5)  # 错误时等待更长时间
    

    
    def display_batch_messages(self, messages_batch: List[tuple]):
        """批量显示消息，减少UI更新频率"""
        if not messages_batch:
            return
            
        # 批量构建消息内容
        batch_content = []
        for msg_type, message in messages_batch:
            # 处理时间戳
            if isinstance(message.timestamp, str):
                try:
                    # 尝试解析ISO格式时间戳
                    if 'T' in message.timestamp:
                        timestamp_str = message.timestamp.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(timestamp_str)
                        formatted_time = dt.strftime("%H:%M:%S")
                    else:
                        # 如果不是ISO格式，截取前8位作为时间
                        formatted_time = message.timestamp[:8] if len(message.timestamp) >= 8 else message.timestamp
                except (ValueError, AttributeError):
                    # 解析失败时使用当前时间
                    formatted_time = datetime.now().strftime("%H:%M:%S")
            else:
                # 如果是datetime对象
                formatted_time = message.timestamp.strftime("%H:%M:%S")
            
            # 格式化消息
            if msg_type == 'input':
                formatted_msg = f"[{formatted_time}] 用户: {message.content}"
            else:  # output
                formatted_msg = f"[{formatted_time}] 助手: {message.content}"
            
            batch_content.append(formatted_msg)
            
            # 添加到历史记录
            self.conversation_history.append(formatted_msg)
        
        # 一次性更新UI
        if batch_content:
            batch_text = '\n'.join(batch_content)
            wx.CallAfter(self._append_conversation_ui, batch_text)

    def display_single_message(self, msg_type: str, message: VoiceMessage):
        """显示单条消息"""
        try:
            # 处理时间戳 - message.timestamp 是字符串格式
            if isinstance(message.timestamp, str):
                try:
                    # 尝试解析 ISO 格式时间戳
                    if 'T' in message.timestamp:
                        # ISO 格式: 2024-01-01T10:00:00Z 或 2024-01-01T10:00:00.123Z
                        timestamp_str = message.timestamp.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(timestamp_str)
                        formatted_time = dt.strftime("%H:%M:%S")
                    else:
                        # 如果不是标准ISO格式，直接使用前8个字符作为时间
                        formatted_time = message.timestamp[:8] if len(message.timestamp) >= 8 else message.timestamp
                except (ValueError, AttributeError):
                    # 如果解析失败，使用当前时间
                    formatted_time = datetime.now().strftime("%H:%M:%S")
            else:
                # 如果是datetime对象
                formatted_time = message.timestamp.strftime("%H:%M:%S")
            
            if msg_type == 'input':
                # 用户消息
                formatted_message = f"[{formatted_time}] 用户: {message.content}"
                speaker = "用户"
            else:
                # 助手消息
                formatted_message = f"[{formatted_time}] 助手: {message.content}"
                speaker = "助手"
            
            # 添加到对话历史
            self.conversation_history.append({
                'timestamp': message.timestamp,
                'content': formatted_message,
                'original_message': message.content,
                'speaker': speaker
            })
            
            # 在UI线程中更新显示
            wx.CallAfter(self.append_conversation, formatted_message)
            wx.CallAfter(self.append_raw_data, formatted_message)
            
        except Exception as e:
            logger.error(f"显示单条消息时出错: {e}")

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
            
            # 原始数据格式（左侧）- 简化显示
            raw_msg = f"[{formatted_time}] {msg_type.upper()}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}"
            self.append_raw_data(raw_msg)
            
            # 简洁对话格式（右侧）- 只保留时间戳
            if msg_type == 'input':
                # 用户消息 - 简洁格式
                simple_msg = f"👤 用户 ({formatted_time})\n{msg.content}\n\n"
            else:
                # 助手消息 - 简洁格式
                simple_msg = f"🤖 助手 ({formatted_time})\n{msg.content}\n\n"
            
            self.append_conversation(simple_msg)
    
    def on_export_conversation(self, event):
        """导出对话内容"""
        try:
            # 检查是否有对话内容
            if not self.conversation_history:
                wx.MessageBox("没有对话内容可导出", "提示", wx.OK | wx.ICON_INFORMATION)
                return
            
            # 选择保存位置
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            default_filename = f"conversation_{timestamp}.md"
            
            with wx.FileDialog(self, "保存对话记录",
                             defaultFile=default_filename,
                             wildcard="Markdown files (*.md)|*.md",
                             style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
                
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                # 获取选择的文件路径
                pathname = fileDialog.GetPath()
                
                try:
                    # 转换为Markdown格式
                    markdown_content = self.convert_to_markdown_from_history()
                    
                    # 写入文件
                    with open(pathname, 'w', encoding='utf-8') as file:
                        file.write(markdown_content)
                    
                    wx.MessageBox(f"对话记录已成功导出到:\n{pathname}", "导出成功", wx.OK | wx.ICON_INFORMATION)
                    
                except IOError:
                    wx.MessageBox("保存文件时出错", "错误", wx.OK | wx.ICON_ERROR)
                    
        except Exception as e:
            logger.error(f"导出对话时出错: {e}")
            wx.MessageBox(f"导出失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def convert_to_markdown_from_history(self) -> str:
        """从对话历史记录转换为markdown格式"""
        markdown_lines = []
        
        # 添加标题
        markdown_lines.append("# 语音代理对话记录")
        markdown_lines.append("")
        markdown_lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")
        
        # 遍历对话历史记录
        for entry in self.conversation_history:
            timestamp = entry['timestamp']
            message = entry['raw_message']
            
            # 解析消息类型
            if "👤 用户" in message:
                # 用户消息
                markdown_lines.append(f"**用户** ({timestamp})：")
                markdown_lines.append("")
                
                # 清理消息内容
                clean_message = message.replace("👤 用户", "").strip()
                if clean_message.startswith("(") and ")" in clean_message:
                    clean_message = clean_message.split(")", 1)[1].strip()
                
                # 添加消息内容
                if clean_message.strip():
                    for line in clean_message.split('\n'):
                        if line.strip():
                            markdown_lines.append(f"> {line.strip()}")
                
                markdown_lines.append("")
                
            elif "🤖 助手" in message:
                # 助手消息
                markdown_lines.append(f"**助手** ({timestamp})：")
                markdown_lines.append("")
                
                # 清理消息内容
                clean_message = message.replace("🤖 助手", "").strip()
                if clean_message.startswith("(") and ")" in clean_message:
                    clean_message = clean_message.split(")", 1)[1].strip()
                
                # 添加消息内容
                if clean_message.strip():
                    for line in clean_message.split('\n'):
                        if line.strip():
                            markdown_lines.append(f"> {line.strip()}")
                
                markdown_lines.append("")
        
        return '\n'.join(markdown_lines)
    

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
        # 清空聊天内容
        for child in self.chat_content_panel.GetChildren():
            child.Destroy()
        self.chat_content_sizer.Clear()
        
        # 添加欢迎消息
        self.add_welcome_message()
        
        # 清空数据存储
        self.raw_data_content = ""
        self.stats_content = ""
        
        # 清空对话历史记录
        self.conversation_history = []
    
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