#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KWS错误分析工具 - GUI界面
基于wxPython的图形用户界面，提供文件选择和分析功能
"""

import wx
import os
import sys
import threading
import time
from datetime import datetime
from kws_error_analyzer import KWSErrorAnalyzer

class KWSErrorAnalysisFrame(wx.Frame):
    """KWS错误分析主窗口"""
    
    def __init__(self):
        super().__init__(None, title="KWS测试错误分析工具", size=(800, 600))
        
        # 初始化变量
        self.tts_file_path = ""
        self.kws_file_path = ""
        self.analyzer = None
        
        # 创建界面
        self.create_ui()
        
        # 居中显示
        self.Center()
    
    def create_ui(self):
        """创建用户界面"""
        # 创建主面板
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title_label = wx.StaticText(main_panel, label="KWS测试错误分析工具")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_label.SetFont(title_font)
        main_sizer.Add(title_label, 0, wx.ALL | wx.CENTER, 10)
        
        # 文件选择区域
        file_box = wx.StaticBox(main_panel, label="文件选择")
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        # TTS文件选择
        tts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tts_label = wx.StaticText(main_panel, label="TTS播放记录文件 (JSON):")
        tts_sizer.Add(tts_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.tts_path_text = wx.TextCtrl(main_panel, style=wx.TE_READONLY)
        tts_sizer.Add(self.tts_path_text, 1, wx.ALL | wx.EXPAND, 5)
        
        self.tts_browse_btn = wx.Button(main_panel, label="浏览...")
        self.tts_browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_tts)
        tts_sizer.Add(self.tts_browse_btn, 0, wx.ALL, 5)
        
        file_sizer.Add(tts_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # KWS文件选择
        kws_sizer = wx.BoxSizer(wx.HORIZONTAL)
        kws_label = wx.StaticText(main_panel, label="KWS识别结果文件 (CSV):")
        kws_sizer.Add(kws_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.kws_path_text = wx.TextCtrl(main_panel, style=wx.TE_READONLY)
        kws_sizer.Add(self.kws_path_text, 1, wx.ALL | wx.EXPAND, 5)
        
        self.kws_browse_btn = wx.Button(main_panel, label="浏览...")
        self.kws_browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_kws)
        kws_sizer.Add(self.kws_browse_btn, 0, wx.ALL, 5)
        
        file_sizer.Add(kws_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # 自动查找按钮
        auto_find_btn = wx.Button(main_panel, label="自动查找最新文件")
        auto_find_btn.Bind(wx.EVT_BUTTON, self.on_auto_find)
        file_sizer.Add(auto_find_btn, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 分析控制区域
        control_box = wx.StaticBox(main_panel, label="分析控制")
        control_sizer = wx.StaticBoxSizer(control_box, wx.VERTICAL)
        
        # 分析按钮
        self.analyze_btn = wx.Button(main_panel, label="开始分析")
        self.analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze)
        self.analyze_btn.Enable(False)
        control_sizer.Add(self.analyze_btn, 0, wx.ALL | wx.CENTER, 10)
        
        # 进度条
        self.progress_gauge = wx.Gauge(main_panel, range=100)
        control_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.ALL, 5)
        
        # 状态标签
        self.status_label = wx.StaticText(main_panel, label="请选择TTS和KWS文件")
        control_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(control_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 结果显示区域
        result_box = wx.StaticBox(main_panel, label="分析结果")
        result_sizer = wx.StaticBoxSizer(result_box, wx.VERTICAL)
        
        # 结果文本框
        self.result_text = wx.TextCtrl(main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        result_sizer.Add(self.result_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # 结果按钮区域
        result_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.clear_btn = wx.Button(main_panel, label="清空结果")
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_result)
        result_btn_sizer.Add(self.clear_btn, 0, wx.ALL, 5)
        
        self.save_btn = wx.Button(main_panel, label="保存结果")
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_result)
        self.save_btn.Enable(False)
        result_btn_sizer.Add(self.save_btn, 0, wx.ALL, 5)
        
        self.open_folder_btn = wx.Button(main_panel, label="打开结果文件夹")
        self.open_folder_btn.Bind(wx.EVT_BUTTON, self.on_open_folder)
        result_btn_sizer.Add(self.open_folder_btn, 0, wx.ALL, 5)
        
        result_sizer.Add(result_btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(result_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # 设置主面板布局
        main_panel.SetSizer(main_sizer)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建状态栏
        self.CreateStatusBar()
        self.SetStatusText("就绪")
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        
        open_tts_item = file_menu.Append(wx.ID_ANY, "打开TTS文件\tCtrl+T", "选择TTS播放记录文件")
        self.Bind(wx.EVT_MENU, self.on_browse_tts, open_tts_item)
        
        open_kws_item = file_menu.Append(wx.ID_ANY, "打开KWS文件\tCtrl+K", "选择KWS识别结果文件")
        self.Bind(wx.EVT_MENU, self.on_browse_kws, open_kws_item)
        
        file_menu.AppendSeparator()
        
        exit_item = file_menu.Append(wx.ID_EXIT, "退出\tCtrl+Q", "退出程序")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        
        menubar.Append(file_menu, "文件")
        
        # 帮助菜单
        help_menu = wx.Menu()
        
        about_item = help_menu.Append(wx.ID_ABOUT, "关于", "关于KWS错误分析工具")
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        menubar.Append(help_menu, "帮助")
        
        self.SetMenuBar(menubar)
    
    def on_browse_tts(self, event):
        """浏览TTS文件"""
        wildcard = "JSON文件 (*.json)|*.json|所有文件 (*.*)|*.*"
        dialog = wx.FileDialog(self, "选择TTS播放记录文件", wildcard=wildcard, style=wx.FD_OPEN)
        
        if dialog.ShowModal() == wx.ID_OK:
            self.tts_file_path = dialog.GetPath()
            self.tts_path_text.SetValue(self.tts_file_path)
            self.check_files_ready()
        
        dialog.Destroy()
    
    def on_browse_kws(self, event):
        """浏览KWS文件"""
        wildcard = "CSV文件 (*.csv)|*.csv|所有文件 (*.*)|*.*"
        dialog = wx.FileDialog(self, "选择KWS识别结果文件", wildcard=wildcard, style=wx.FD_OPEN)
        
        if dialog.ShowModal() == wx.ID_OK:
            self.kws_file_path = dialog.GetPath()
            self.kws_path_text.SetValue(self.kws_file_path)
            self.check_files_ready()
        
        dialog.Destroy()
    
    def on_auto_find(self, event):
        """自动查找最新文件"""
        try:
            # 查找TTS JSON文件
            tts_pattern = os.path.join("..", "realtime_parse_info_*.json")
            import glob
            tts_files = glob.glob(tts_pattern)
            
            # 查找KWS CSV文件
            kws_pattern = os.path.join("kws_output", "kws_data_*.csv")
            kws_files = glob.glob(kws_pattern)
            
            if not tts_files:
                wx.MessageBox("未找到TTS记录文件 (realtime_parse_info_*.json)", "文件未找到", wx.OK | wx.ICON_WARNING)
                return
            
            if not kws_files:
                wx.MessageBox("未找到KWS记录文件 (kws_output/kws_data_*.csv)", "文件未找到", wx.OK | wx.ICON_WARNING)
                return
            
            # 选择最新的文件
            latest_tts = max(tts_files, key=os.path.getmtime)
            latest_kws = max(kws_files, key=os.path.getmtime)
            
            self.tts_file_path = os.path.abspath(latest_tts)
            self.kws_file_path = os.path.abspath(latest_kws)
            
            self.tts_path_text.SetValue(self.tts_file_path)
            self.kws_path_text.SetValue(self.kws_file_path)
            
            self.check_files_ready()
            
            self.append_result(f"自动找到文件:\nTTS: {os.path.basename(self.tts_file_path)}\nKWS: {os.path.basename(self.kws_file_path)}\n")
            
        except Exception as e:
            wx.MessageBox(f"自动查找文件失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def check_files_ready(self):
        """检查文件是否准备就绪"""
        if self.tts_file_path and self.kws_file_path:
            if os.path.exists(self.tts_file_path) and os.path.exists(self.kws_file_path):
                self.analyze_btn.Enable(True)
                self.status_label.SetLabel("文件已选择，可以开始分析")
                self.SetStatusText("文件已准备就绪")
            else:
                self.analyze_btn.Enable(False)
                self.status_label.SetLabel("文件路径无效")
                self.SetStatusText("文件路径无效")
        else:
            self.analyze_btn.Enable(False)
            self.status_label.SetLabel("请选择TTS和KWS文件")
            self.SetStatusText("等待文件选择")
    
    def on_analyze(self, event):
        """开始分析"""
        if not self.tts_file_path or not self.kws_file_path:
            wx.MessageBox("请先选择TTS和KWS文件", "文件未选择", wx.OK | wx.ICON_WARNING)
            return
        
        # 禁用分析按钮
        self.analyze_btn.Enable(False)
        self.status_label.SetLabel("正在分析...")
        self.SetStatusText("分析进行中...")
        
        # 清空结果
        self.result_text.Clear()
        
        # 在后台线程中执行分析
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()
    
    def run_analysis(self):
        """在后台线程中运行分析"""
        try:
            # 更新进度
            wx.CallAfter(self.update_progress, 10, "初始化分析器...")
            
            # 创建分析器
            self.analyzer = KWSErrorAnalyzer()
            
            # 加载TTS记录
            wx.CallAfter(self.update_progress, 30, "加载TTS记录...")
            wx.CallAfter(self.append_result, "正在加载TTS记录文件...\n")
            
            if not self.analyzer.load_tts_records(self.tts_file_path):
                wx.CallAfter(self.analysis_error, "加载TTS记录文件失败")
                return
            
            wx.CallAfter(self.append_result, f"成功加载TTS记录: {len(self.analyzer.tts_records)} 条\n")
            
            # 加载KWS记录
            wx.CallAfter(self.update_progress, 50, "加载KWS记录...")
            wx.CallAfter(self.append_result, "正在加载KWS记录文件...\n")
            
            if not self.analyzer.load_kws_records(self.kws_file_path):
                wx.CallAfter(self.analysis_error, "加载KWS记录文件失败")
                return
            
            wx.CallAfter(self.append_result, f"成功加载KWS记录: {len(self.analyzer.kws_records)} 条\n")
            
            # 执行分析
            wx.CallAfter(self.update_progress, 70, "执行错误分析...")
            wx.CallAfter(self.append_result, "正在执行错误分析...\n")
            
            error_records = self.analyzer.analyze_records()
            
            # 保存结果
            wx.CallAfter(self.update_progress, 90, "保存分析结果...")
            output_file = self.analyzer.save_error_analysis()
            
            # 完成分析
            wx.CallAfter(self.update_progress, 100, "分析完成")
            wx.CallAfter(self.analysis_complete, output_file, error_records)
            
        except Exception as e:
            wx.CallAfter(self.analysis_error, f"分析过程中出错: {str(e)}")
    
    def update_progress(self, value, status):
        """更新进度条和状态"""
        self.progress_gauge.SetValue(value)
        self.status_label.SetLabel(status)
        self.SetStatusText(status)
    
    def append_result(self, text):
        """追加结果文本"""
        self.result_text.AppendText(text)
    
    def analysis_complete(self, output_file, error_records):
        """分析完成"""
        # 显示摘要
        summary = f"\n{'='*50}\n"
        summary += "KWS测试错误分析摘要\n"
        summary += f"{'='*50}\n"
        summary += f"TTS记录总数: {len(self.analyzer.tts_records)}\n"
        summary += f"KWS记录总数: {len(self.analyzer.kws_records)}\n"
        summary += f"发现错误记录: {len(error_records)}\n"
        
        if error_records:
            error_types = {}
            for record in error_records:
                error_type = record['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            summary += "错误类型统计:\n"
            for error_type, count in error_types.items():
                summary += f"  {error_type}: {count} 条\n"
        
        summary += f"{'='*50}\n"
        
        if output_file:
            summary += f"分析结果已保存到: {output_file}\n"
        
        self.append_result(summary)
        
        # 重置控件状态
        self.analyze_btn.Enable(True)
        self.save_btn.Enable(True)
        self.progress_gauge.SetValue(0)
        self.status_label.SetLabel("分析完成")
        self.SetStatusText("分析完成")
        
        # 显示完成对话框
        if error_records:
            message = f"分析完成！发现 {len(error_records)} 条错误记录。\n\n结果已保存到:\n{output_file}"
            wx.MessageBox(message, "分析完成", wx.OK | wx.ICON_INFORMATION)
        else:
            message = f"分析完成！未发现错误记录，测试结果良好。\n\n结果已保存到:\n{output_file}"
            wx.MessageBox(message, "分析完成", wx.OK | wx.ICON_INFORMATION)
    
    def analysis_error(self, error_msg):
        """分析出错"""
        self.append_result(f"错误: {error_msg}\n")
        self.analyze_btn.Enable(True)
        self.progress_gauge.SetValue(0)
        self.status_label.SetLabel("分析失败")
        self.SetStatusText("分析失败")
        
        wx.MessageBox(error_msg, "分析错误", wx.OK | wx.ICON_ERROR)
    
    def on_clear_result(self, event):
        """清空结果"""
        self.result_text.Clear()
        self.save_btn.Enable(False)
    
    def on_save_result(self, event):
        """保存结果"""
        if not self.result_text.GetValue():
            wx.MessageBox("没有结果可保存", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        
        wildcard = "文本文件 (*.txt)|*.txt|所有文件 (*.*)|*.*"
        dialog = wx.FileDialog(self, "保存分析结果", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dialog.ShowModal() == wx.ID_OK:
            try:
                with open(dialog.GetPath(), 'w', encoding='utf-8') as f:
                    f.write(self.result_text.GetValue())
                wx.MessageBox("结果已保存", "保存成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"保存失败: {str(e)}", "保存错误", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()
    
    def on_open_folder(self, event):
        """打开结果文件夹"""
        try:
            current_dir = os.getcwd()
            os.startfile(current_dir)
        except Exception as e:
            wx.MessageBox(f"打开文件夹失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_exit(self, event):
        """退出程序"""
        self.Close()
    
    def on_about(self, event):
        """关于对话框"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("KWS测试错误分析工具")
        info.SetVersion("1.0")
        info.SetDescription("用于分析TTS播放记录与KWS识别结果的对应关系，自动检测错误识别情况。")
        info.SetCopyright("(C) 2025")
        info.AddDeveloper("AI Assistant")
        
        wx.adv.AboutBox(info)


class KWSErrorAnalysisApp(wx.App):
    """应用程序类"""
    
    def OnInit(self):
        frame = KWSErrorAnalysisFrame()
        frame.Show()
        return True


def main():
    """主函数"""
    app = KWSErrorAnalysisApp()
    app.MainLoop()


if __name__ == "__main__":
    main()