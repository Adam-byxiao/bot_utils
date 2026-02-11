#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS (Keyword Spotting) GUI 界面
基于wxPython的可视化界面，用于监控和分析语音唤醒词识别
"""

import wx
import wx.lib.scrolledpanel as scrolled
import threading
import time
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
import sys

# 导入KWS计算模块
try:
    from KWS_calculate import KWSCalculator, KWSRecord
except ImportError:
    # 尝试从绝对路径导入
    import os
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    try:
        from KWS_calculate import KWSCalculator, KWSRecord
    except ImportError as e:
        print(f"警告: 无法导入KWS_calculate模块: {e}")
        print("请确保KWS_calculate.py文件在当前目录或Python路径中")
        # 创建空的占位类以避免后续错误
        class KWSCalculator:
            def __init__(self, *args, **kwargs):
                raise ImportError("KWSCalculator模块导入失败")
        
        class KWSRecord:
            def __init__(self, *args, **kwargs):
                raise ImportError("KWSRecord模块导入失败")

class TestConnectionDialog(wx.Dialog):
    """测试连接对话框"""
    
    def __init__(self, parent):
        super().__init__(parent, title="测试连接", size=(450, 350))
        
        self.test_result = None
        self.is_closing = False  # 标志对话框是否正在关闭
        self.init_ui()
        self.Center()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def init_ui(self):
        """初始化UI"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 连接信息输入区域
        conn_box = wx.StaticBox(self, label="连接信息")
        conn_sizer = wx.StaticBoxSizer(conn_box, wx.VERTICAL)
        
        # 输入字段
        input_grid = wx.FlexGridSizer(3, 2, 10, 10)
        input_grid.AddGrowableCol(1)
        
        input_grid.Add(wx.StaticText(self, label="IP地址:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.ip_text = wx.TextCtrl(self, size=(200, -1))
        input_grid.Add(self.ip_text, 1, wx.EXPAND)
        
        input_grid.Add(wx.StaticText(self, label="用户名:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.username_text = wx.TextCtrl(self, size=(200, -1))
        input_grid.Add(self.username_text, 1, wx.EXPAND)
        
        input_grid.Add(wx.StaticText(self, label="密码:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD, size=(200, -1))
        input_grid.Add(self.password_text, 1, wx.EXPAND)
        
        conn_sizer.Add(input_grid, 0, wx.ALL|wx.EXPAND, 10)
        main_sizer.Add(conn_sizer, 0, wx.ALL|wx.EXPAND, 10)
        
        # 测试按钮
        test_btn = wx.Button(self, label="开始测试连接")
        test_btn.Bind(wx.EVT_BUTTON, self.on_test)
        main_sizer.Add(test_btn, 0, wx.ALL|wx.CENTER, 10)
        
        # 结果显示区域
        result_box = wx.StaticBox(self, label="测试结果")
        result_sizer = wx.StaticBoxSizer(result_box, wx.VERTICAL)
        
        self.result_text = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(400, 120))
        self.result_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        result_sizer.Add(self.result_text, 1, wx.ALL|wx.EXPAND, 5)
        
        main_sizer.Add(result_sizer, 1, wx.ALL|wx.EXPAND, 10)
        
        # 按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(self, wx.ID_OK, "确定")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "取消")
        
        button_sizer.Add(ok_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALL|wx.CENTER, 10)
        
        self.SetSizer(main_sizer)
        
        # 初始化结果显示
        self.result_text.SetValue("点击'开始测试连接'按钮进行连接测试...")
    
    def set_connection_info(self, host: str, username: str, password: str):
        """设置连接信息"""
        self.ip_text.SetValue(host)
        self.username_text.SetValue(username)
        self.password_text.SetValue(password)
    
    def get_connection_info(self):
        """获取连接信息"""
        return (
            self.ip_text.GetValue().strip(),
            self.username_text.GetValue().strip(),
            self.password_text.GetValue()
        )
    
    def on_test(self, event):
        """执行连接测试"""
        host = self.ip_text.GetValue().strip()
        username = self.username_text.GetValue().strip()
        password = self.password_text.GetValue()
        
        if not all([host, username, password]):
            self.result_text.SetValue("错误: 请填写完整的连接信息")
            return
        
        # 显示测试开始
        self.result_text.SetValue("正在测试连接...\n")
        wx.SafeYield()  # 刷新界面
        
        # 在后台线程中执行测试
        test_thread = threading.Thread(target=self._test_connection_worker, 
                                     args=(host, username, password))
        test_thread.daemon = True
        test_thread.start()
    
    def _test_connection_worker(self, host: str, username: str, password: str):
        """连接测试工作线程"""
        try:
            # 创建KWS计算器进行测试
            test_calculator = KWSCalculator(host, username, password)
            
            # 记录开始时间
            start_time = time.time()
            
            # 尝试连接
            wx.CallAfter(self._update_result, "正在连接SSH服务器...\n")
            
            if test_calculator.connect():
                connect_time = time.time() - start_time
                wx.CallAfter(self._update_result, f"✓ SSH连接成功 (耗时: {connect_time:.2f}秒)\n")
                
                # 测试命令执行
                wx.CallAfter(self._update_result, "正在测试命令执行...\n")
                
                try:
                    # 执行测试命令
                    stdin, stdout, stderr = test_calculator.ssh_client.exec_command("echo 'KWS连接测试'", timeout=10)
                    output = stdout.read().decode('utf-8').strip()
                    
                    if output == "KWS连接测试":
                        wx.CallAfter(self._update_result, "✓ 命令执行成功\n")
                        
                        # 测试日志文件访问
                        wx.CallAfter(self._update_result, "正在测试日志文件访问...\n")
                        
                        stdin, stdout, stderr = test_calculator.ssh_client.exec_command(
                            "ls -la /var/log/vibe-ai/vibe-ai.LATEST", timeout=10)
                        output = stdout.read().decode('utf-8').strip()
                        error = stderr.read().decode('utf-8').strip()
                        
                        if output and not error:
                            wx.CallAfter(self._update_result, "✓ 日志文件访问正常\n")
                            wx.CallAfter(self._update_result, f"日志文件信息: {output}\n")
                        else:
                            wx.CallAfter(self._update_result, f"⚠ 日志文件访问异常: {error}\n")
                        
                        # 测试完成
                        total_time = time.time() - start_time
                        wx.CallAfter(self._update_result, f"\n✓ 连接测试完成 (总耗时: {total_time:.2f}秒)\n")
                        wx.CallAfter(self._update_result, "设备连接正常，可以开始监控。")
                        
                    else:
                        wx.CallAfter(self._update_result, f"✗ 命令执行失败，输出异常: {output}\n")
                        
                except Exception as cmd_error:
                    wx.CallAfter(self._update_result, f"✗ 命令执行失败: {str(cmd_error)}\n")
                
                # 断开连接
                test_calculator.disconnect()
                
            else:
                wx.CallAfter(self._update_result, "✗ SSH连接失败\n")
                wx.CallAfter(self._update_result, "请检查:\n")
                wx.CallAfter(self._update_result, "1. IP地址是否正确\n")
                wx.CallAfter(self._update_result, "2. 用户名和密码是否正确\n")
                wx.CallAfter(self._update_result, "3. SSH服务是否正常运行\n")
                wx.CallAfter(self._update_result, "4. 网络连接是否正常\n")
                
        except Exception as e:
            wx.CallAfter(self._update_result, f"✗ 测试过程中发生错误: {str(e)}\n")
    
    def _update_result(self, message: str):
        """更新结果显示（线程安全）"""
        try:
            # 检查对话框是否正在关闭或控件是否仍然存在
            if (not self.is_closing and 
                hasattr(self, 'result_text') and 
                self.result_text and 
                not self.result_text.IsBeingDeleted()):
                self.result_text.AppendText(message)
        except (RuntimeError, AttributeError):
            # 如果控件已被删除或不存在，静默忽略
            pass
    
    def on_close(self, event):
        """处理对话框关闭事件"""
        self.is_closing = True  # 设置关闭标志
        event.Skip()  # 继续默认的关闭处理

class KWSStatsPanel(wx.Panel):
    """统计面板"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()
        self.reset_stats()
    
    def init_ui(self):
        """初始化UI"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title = wx.StaticText(self, label="实时统计")
        title_font = title.GetFont()
        title_font.SetPointSize(12)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL|wx.CENTER, 5)
        
        # 创建提示词的统计区域
        self.phrase_stats = {}
        phrases = ["hey_vibe"]  # 仅使用hey_vibe唤醒词
        
        for phrase in phrases:
            # 创建分组框
            group_box = wx.StaticBox(self, label=f"提示词: {phrase}")
            group_sizer = wx.StaticBoxSizer(group_box, wx.VERTICAL)
            
            # 统计信息
            stats_grid = wx.FlexGridSizer(4, 2, 5, 10)
            
            # 总次数
            stats_grid.Add(wx.StaticText(self, label="总识别次数:"), 0, wx.ALIGN_CENTER_VERTICAL)
            total_label = wx.StaticText(self, label="0")
            stats_grid.Add(total_label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            # 触发次数
            stats_grid.Add(wx.StaticText(self, label="成功触发次数:"), 0, wx.ALIGN_CENTER_VERTICAL)
            triggered_label = wx.StaticText(self, label="0")
            stats_grid.Add(triggered_label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            # 触发率
            stats_grid.Add(wx.StaticText(self, label="触发率:"), 0, wx.ALIGN_CENTER_VERTICAL)
            rate_label = wx.StaticText(self, label="0.00%")
            stats_grid.Add(rate_label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            # 平均分数
            stats_grid.Add(wx.StaticText(self, label="平均分数:"), 0, wx.ALIGN_CENTER_VERTICAL)
            avg_score_label = wx.StaticText(self, label="0.0000")
            stats_grid.Add(avg_score_label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            group_sizer.Add(stats_grid, 0, wx.ALL|wx.EXPAND, 5)
            main_sizer.Add(group_sizer, 0, wx.ALL|wx.EXPAND, 5)
            
            # 保存标签引用
            self.phrase_stats[phrase] = {
                'total': total_label,
                'triggered': triggered_label,
                'rate': rate_label,
                'avg_score': avg_score_label
            }
        
        self.SetSizer(main_sizer)
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats_data = {}
        for phrase in self.phrase_stats.keys():
            self.stats_data[phrase] = {
                'total': 0,
                'triggered': 0,
                'scores': []
            }
        self.update_display()
    
    def update_stats(self, phrase: str, score: float, triggered: bool):
        """更新统计数据"""
        if phrase not in self.stats_data:
            self.stats_data[phrase] = {
                'total': 0,
                'triggered': 0,
                'scores': []
            }
        
        self.stats_data[phrase]['total'] += 1
        self.stats_data[phrase]['scores'].append(score)
        if triggered:
            self.stats_data[phrase]['triggered'] += 1
        
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        for phrase, labels in self.phrase_stats.items():
            if phrase in self.stats_data:
                data = self.stats_data[phrase]
                
                # 更新总次数
                labels['total'].SetLabel(str(data['total']))
                
                # 更新触发次数
                labels['triggered'].SetLabel(str(data['triggered']))
                
                # 更新触发率
                if data['total'] > 0:
                    rate = (data['triggered'] / data['total']) * 100
                    labels['rate'].SetLabel(f"{rate:.2f}%")
                else:
                    labels['rate'].SetLabel("0.00%")
                
                # 更新平均分数
                if data['scores']:
                    avg_score = sum(data['scores']) / len(data['scores'])
                    labels['avg_score'].SetLabel(f"{avg_score:.4f}")
                else:
                    labels['avg_score'].SetLabel("0.0000")

class KWSOutputPanel(scrolled.ScrolledPanel):
    """输出面板"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()
        self.debug_mode = False
    
    def init_ui(self):
        """初始化UI"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题和模式选择
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        title = wx.StaticText(self, label="输出日志")
        title_font = title.GetFont()
        title_font.SetPointSize(12)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        header_sizer.Add(title, 1, wx.ALIGN_CENTER_VERTICAL)
        
        # 模式选择
        mode_choices = ["Standard", "Debug"]
        self.mode_choice = wx.Choice(self, choices=mode_choices)
        self.mode_choice.SetSelection(0)
        self.mode_choice.Bind(wx.EVT_CHOICE, self.on_mode_change)
        header_sizer.Add(wx.StaticText(self, label="模式:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        header_sizer.Add(self.mode_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(header_sizer, 0, wx.ALL|wx.EXPAND, 5)
        
        # 输出文本框
        self.output_text = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)
        self.output_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(self.output_text, 1, wx.ALL|wx.EXPAND, 5)
        
        # 清空按钮
        clear_btn = wx.Button(self, label="清空日志")
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        main_sizer.Add(clear_btn, 0, wx.ALL|wx.CENTER, 5)
        
        self.SetSizer(main_sizer)
        self.SetupScrolling()
    
    def on_mode_change(self, event):
        """模式改变事件"""
        self.debug_mode = (self.mode_choice.GetSelection() == 1)
        self.append_log(f"切换到 {'Debug' if self.debug_mode else 'Standard'} 模式")
    
    def on_clear(self, event):
        """清空日志"""
        self.output_text.Clear()
    
    def append_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        wx.CallAfter(self._append_text, log_message)
    
    def _append_text(self, text: str):
        """线程安全的文本添加"""
        self.output_text.AppendText(text)
        # 自动滚动到底部
        self.output_text.SetInsertionPointEnd()

class KWSMainFrame(wx.Frame):
    """主窗口"""
    
    def __init__(self):
        super().__init__(None, title="KWS 语音唤醒词监控工具", size=(1000, 700))
        
        self.kws_calculator = None
        self.monitoring_thread = None
        self.is_monitoring = False
        self.records = []
        
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        """初始化UI"""
        # 创建主面板
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧面板
        left_panel = wx.Panel(main_panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 登录区域
        login_box = wx.StaticBox(left_panel, label="设备连接")
        login_sizer = wx.StaticBoxSizer(login_box, wx.VERTICAL)
        
        # 连接信息输入
        conn_grid = wx.FlexGridSizer(3, 2, 5, 10)
        conn_grid.AddGrowableCol(1)
        
        conn_grid.Add(wx.StaticText(left_panel, label="IP地址:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.ip_text = wx.TextCtrl(left_panel, value="192.168.1.100")
        conn_grid.Add(self.ip_text, 1, wx.EXPAND)
        
        conn_grid.Add(wx.StaticText(left_panel, label="用户名:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.username_text = wx.TextCtrl(left_panel, value="root")
        conn_grid.Add(self.username_text, 1, wx.EXPAND)
        
        conn_grid.Add(wx.StaticText(left_panel, label="密码:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.password_text = wx.TextCtrl(left_panel, style=wx.TE_PASSWORD, value="test0000")
        conn_grid.Add(self.password_text, 1, wx.EXPAND)
        
        login_sizer.Add(conn_grid, 0, wx.ALL|wx.EXPAND, 5)
        left_sizer.Add(login_sizer, 0, wx.ALL|wx.EXPAND, 5)
        
        # 统计区域
        self.stats_panel = KWSStatsPanel(left_panel)
        left_sizer.Add(self.stats_panel, 1, wx.ALL|wx.EXPAND, 5)
        
        # 控制按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.start_btn = wx.Button(left_panel, label="开始监控")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        button_sizer.Add(self.start_btn, 1, wx.ALL|wx.EXPAND, 5)
        
        self.stop_btn = wx.Button(left_panel, label="停止监控")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.stop_btn.Enable(False)
        button_sizer.Add(self.stop_btn, 1, wx.ALL|wx.EXPAND, 5)
        
        self.export_btn = wx.Button(left_panel, label="导出数据")
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        button_sizer.Add(self.export_btn, 1, wx.ALL|wx.EXPAND, 5)
        
        left_sizer.Add(button_sizer, 0, wx.ALL|wx.EXPAND, 5)
        
        left_panel.SetSizer(left_sizer)
        main_sizer.Add(left_panel, 1, wx.ALL|wx.EXPAND, 5)
        
        # 右侧输出面板
        self.output_panel = KWSOutputPanel(main_panel)
        main_sizer.Add(self.output_panel, 1, wx.ALL|wx.EXPAND, 5)
        
        main_panel.SetSizer(main_sizer)
        
        # 状态栏
        self.CreateStatusBar()
        self.SetStatusText("就绪")
        
        # 菜单栏
        self.create_menu()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, "打开配置\tCtrl+O")
        file_menu.Append(wx.ID_SAVE, "保存配置\tCtrl+S")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "退出\tCtrl+Q")
        
        # 工具菜单
        tools_menu = wx.Menu()
        self.clear_stats_id = wx.NewId()
        self.test_connection_id = wx.NewId()
        tools_menu.Append(self.clear_stats_id, "清空统计\tCtrl+R")
        tools_menu.Append(self.test_connection_id, "测试连接\tCtrl+T")
        
        # 帮助菜单
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "关于")
        
        menubar.Append(file_menu, "文件")
        menubar.Append(tools_menu, "工具")
        menubar.Append(help_menu, "帮助")
        
        self.SetMenuBar(menubar)
        
        # 绑定事件
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_clear_stats, id=self.clear_stats_id)
        self.Bind(wx.EVT_MENU, self.on_test_connection, id=self.test_connection_id)
    
    def on_start(self, event):
        """开始监控"""
        # 获取连接信息
        host = self.ip_text.GetValue().strip()
        username = self.username_text.GetValue().strip()
        password = self.password_text.GetValue()
        
        if not all([host, username, password]):
            wx.MessageBox("请填写完整的连接信息", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        # 创建KWS计算器
        try:
            self.kws_calculator = KWSCalculator(host, username, password)
            
            # 尝试连接
            self.output_panel.append_log("正在连接设备...")
            self.SetStatusText("连接中...")
            
            if not self.kws_calculator.connect():
                wx.MessageBox("连接失败，请检查网络和认证信息", "连接错误", wx.OK | wx.ICON_ERROR)
                self.SetStatusText("连接失败")
                return
            
            self.output_panel.append_log("连接成功，开始监控...")
            self.SetStatusText("监控中...")
            
            # 重置统计
            self.stats_panel.reset_stats()
            self.records.clear()
            
            # 启动监控线程
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitoring_worker)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            # 更新按钮状态
            self.start_btn.Enable(False)
            self.stop_btn.Enable(True)
            
            if not self.output_panel.debug_mode:
                self.output_panel.append_log("Standard模式: 将显示识别次数和最终统计")
            else:
                self.output_panel.append_log("Debug模式: 将显示详细的识别信息")
            
        except Exception as e:
            wx.MessageBox(f"启动监控失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            self.SetStatusText("启动失败")
    
    def on_stop(self, event):
        """停止监控"""
        self.is_monitoring = False
        
        if self.kws_calculator:
            self.kws_calculator.stop_monitoring()
            self.kws_calculator.disconnect()
        
        self.output_panel.append_log("监控已停止")
        self.SetStatusText("已停止")
        
        # 更新按钮状态
        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)
        
        # 显示最终统计
        self.show_final_stats()
    
    def on_export(self, event):
        """导出数据"""
        if not self.records:
            wx.MessageBox("没有数据可导出", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        
        # 选择保存位置
        with wx.FileDialog(self, "保存数据文件",
                          defaultFile=f"kws_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                          wildcard="CSV files (*.csv)|*.csv",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
            
            try:
                self.export_to_csv(pathname)
                wx.MessageBox(f"数据已导出到: {pathname}", "导出成功", wx.OK | wx.ICON_INFORMATION)
                self.output_panel.append_log(f"数据已导出到: {pathname}")
            except Exception as e:
                wx.MessageBox(f"导出失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def export_to_csv(self, filepath: str):
        """导出数据到CSV文件"""
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['时间戳', '提示词', '分数', '是否触发', '开始时间', '结束时间', '原始日志'])
            
            for record in self.records:
                writer.writerow([
                    record.timestamp,
                    record.phrase,
                    record.score,
                    '是' if record.triggered else '否',
                    record.begin_time,
                    record.end_time,
                    record.raw_log
                ])
    
    def monitoring_worker(self):
        """监控工作线程"""
        try:
            # 保存原始方法
            original_process_line = self.kws_calculator._process_log_line
            original_update_trigger = self.kws_calculator._update_trigger_status
            
            # 记录已处理的记录数量
            processed_kws_count = 0
            processed_triggered_count = 0
            processed_untriggered_count = 0
            
            def gui_process_line(line):
                nonlocal processed_kws_count, processed_triggered_count, processed_untriggered_count
                
                # 添加调试信息
                if self.output_panel.debug_mode:
                    wx.CallAfter(self.output_panel.append_log, f"处理日志行: {line.strip()}")
                
                # 调用原始处理方法
                original_process_line(line)
                
                # 检查是否有新的KWS识别记录
                current_kws_count = len(self.kws_calculator.records)
                if current_kws_count > processed_kws_count:
                    # 处理新增的KWS识别记录
                    for i in range(processed_kws_count, current_kws_count):
                        record = self.kws_calculator.records[i]
                        
                        # 只处理hey_vibe的记录，hello_vibe不添加到显示列表
                        if record.phrase != "hello_vibe":
                            self.records.append(record)
                            wx.CallAfter(self.output_panel.append_log,
                                       f"第 {len(self.records)} 次识别: {record.phrase}, 分数: {record.score:.4f}")
                        
                        if self.output_panel.debug_mode and record.phrase != "hello_vibe":
                            wx.CallAfter(self.output_panel.append_log,
                                       f"详细: 时间={record.timestamp}, begin={record.begin_time}, end={record.end_time}")
                    
                    processed_kws_count = current_kws_count
            
            def gui_update_trigger(phrase, triggered, timestamp, detailed_record=None):
                nonlocal processed_triggered_count, processed_untriggered_count
                
                # 调用原始方法
                original_update_trigger(phrase, triggered, timestamp, detailed_record)
                
                # 检查触发记录和未触发记录的变化
                current_triggered = len(self.kws_calculator.triggered_records)
                current_untriggered = len(self.kws_calculator.untriggered_records)
                
                # 处理新的触发记录
                if current_triggered > processed_triggered_count:
                    for i in range(processed_triggered_count, current_triggered):
                        record = self.kws_calculator.triggered_records[i]
                        
                        # 只处理hey_vibe的记录，hello_vibe不添加到显示列表
                        if record.phrase != "hello_vibe" and record not in self.records:
                            self.records.append(record)
                            wx.CallAfter(self.output_panel.append_log,
                                       f"第 {len(self.records)} 次识别: {record.phrase}, 分数: {record.score:.4f}")
                        
                        # 更新统计
                        wx.CallAfter(self.stats_panel.update_stats, 
                                   record.phrase, 
                                   record.score, 
                                   True)
                        
                        # 过滤掉hello_vibe的状态更新
                        if phrase != "hello_vibe":
                            wx.CallAfter(self.output_panel.append_log,
                                       f"状态更新: {phrase} - 触发")
                    
                    processed_triggered_count = current_triggered
                
                # 处理新的未触发记录
                if current_untriggered > processed_untriggered_count:
                    for i in range(processed_untriggered_count, current_untriggered):
                        record = self.kws_calculator.untriggered_records[i]
                        
                        # 只处理hey_vibe的记录，hello_vibe不添加到显示列表
                        if record.phrase != "hello_vibe" and record not in self.records:
                            self.records.append(record)
                            wx.CallAfter(self.output_panel.append_log,
                                       f"第 {len(self.records)} 次识别: {record.phrase}, 分数: {record.score:.4f}")
                        
                        # 更新统计
                        wx.CallAfter(self.stats_panel.update_stats, 
                                   record.phrase, 
                                   record.score, 
                                   False)
                        
                        # 过滤掉hello_vibe的状态更新
                        if phrase != "hello_vibe":
                            wx.CallAfter(self.output_panel.append_log,
                                       f"状态更新: {phrase} - 未触发")
                    
                    processed_untriggered_count = current_untriggered
            
            # 替换处理方法
            self.kws_calculator._process_log_line = gui_process_line
            self.kws_calculator._update_trigger_status = gui_update_trigger
            
            # 开始监控
            wx.CallAfter(self.output_panel.append_log, "开始监控日志...")
            
            # 显示连接时间戳信息
            if hasattr(self.kws_calculator, 'connection_start_time') and self.kws_calculator.connection_start_time:
                start_time_str = self.kws_calculator.connection_start_time.isoformat() + 'Z'
                wx.CallAfter(self.output_panel.append_log, f"连接时间戳: {start_time_str}")
                wx.CallAfter(self.output_panel.append_log, "注意: 将忽略连接前的历史记录")
            
            self.kws_calculator.start_monitoring()
            
        except Exception as e:
            wx.CallAfter(self.output_panel.append_log, f"监控错误: {str(e)}")
            wx.CallAfter(self.SetStatusText, "监控错误")
        finally:
            # 恢复原始方法
            if 'original_process_line' in locals():
                self.kws_calculator._process_log_line = original_process_line
            if 'original_update_trigger' in locals():
                self.kws_calculator._update_trigger_status = original_update_trigger
    
    def show_final_stats(self):
        """显示最终统计"""
        total_records = len(self.records)
        if total_records == 0:
            self.output_panel.append_log("没有识别记录")
            return
        
        triggered_count = sum(1 for r in self.records if r.triggered)
        trigger_rate = (triggered_count / total_records) * 100
        
        self.output_panel.append_log("=" * 50)
        self.output_panel.append_log("最终统计结果:")
        self.output_panel.append_log(f"总识别次数: {total_records}")
        self.output_panel.append_log(f"成功触发次数: {triggered_count}")
        self.output_panel.append_log(f"触发率: {trigger_rate:.2f}%")
        
        # 按提示词分组统计
        phrase_stats = {}
        for record in self.records:
            if record.phrase not in phrase_stats:
                phrase_stats[record.phrase] = {'total': 0, 'triggered': 0, 'scores': []}
            phrase_stats[record.phrase]['total'] += 1
            phrase_stats[record.phrase]['scores'].append(record.score)
            if record.triggered:
                phrase_stats[record.phrase]['triggered'] += 1
        
        for phrase, stats in phrase_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores'])
            phrase_rate = (stats['triggered'] / stats['total']) * 100
            self.output_panel.append_log(f"{phrase}: {stats['total']}次, 触发{stats['triggered']}次 "
                                       f"({phrase_rate:.2f}%), 平均分数: {avg_score:.4f}")
        
        self.output_panel.append_log("=" * 50)
    
    def on_exit(self, event):
        """退出程序"""
        if self.is_monitoring:
            if wx.MessageBox("监控正在进行中，确定要退出吗？", "确认退出", 
                           wx.YES_NO | wx.ICON_QUESTION) == wx.NO:
                return
            self.on_stop(None)
        
        self.Close()
    
    def on_clear_stats(self, event):
        """清空统计数据"""
        if self.is_monitoring:
            wx.MessageBox("监控正在进行中，无法清空统计", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 确认对话框
        if wx.MessageBox("确定要清空所有统计数据吗？", "确认清空", 
                        wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.stats_panel.reset_stats()
            self.records.clear()
            self.output_panel.append_log("统计数据已清空")
            self.SetStatusText("统计已清空")
    
    def on_test_connection(self, event):
        """测试连接"""
        # 创建测试连接对话框
        dialog = TestConnectionDialog(self)
        
        # 从主界面获取当前连接信息
        dialog.set_connection_info(
            self.ip_text.GetValue().strip(),
            self.username_text.GetValue().strip(),
            self.password_text.GetValue()
        )
        
        if dialog.ShowModal() == wx.ID_OK:
            # 如果用户在对话框中修改了连接信息，更新主界面
            host, username, password = dialog.get_connection_info()
            self.ip_text.SetValue(host)
            self.username_text.SetValue(username)
            self.password_text.SetValue(password)
        
        dialog.Destroy()
    
    def on_about(self, event):
        """关于对话框"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("KWS 语音唤醒词监控工具")
        info.SetVersion("1.0.0")
        info.SetDescription("基于SSH连接的实时语音唤醒词识别监控和分析工具")
        info.SetCopyright("(C) 2025")
        info.AddDeveloper("Bot Utils Team")
        
        wx.adv.AboutBox(info)

class KWSApp(wx.App):
    """应用程序类"""
    
    def OnInit(self):
        frame = KWSMainFrame()
        frame.Show()
        return True

def main():
    """主函数"""
    app = KWSApp()
    app.MainLoop()

if __name__ == "__main__":
    main()