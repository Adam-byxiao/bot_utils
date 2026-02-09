import wx
import os
import sys
import webbrowser
from wx.adv import AboutDialogInfo, AboutBox
from wx.lib.pubsub import pub
from audio_script.AudioAligner import AudioAlignerApp
from audio_script.Video2Audio import AudioConverterApp
from audio_script.AudioResampler import AudioResamplerApp
from audio_script.AudioGenderSplitter import AudioGenderSplitterApp
import time  # 添加标准库导入

class AudioToolsMainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="音频处理工具箱", size=(900, 700))
        
        self.panel = wx.Panel(self)
        self.SetMinSize((800, 600))
        self.init_ui()
        
        # 设置订阅，接收子窗口的输出信息
        pub.subscribe(self.update_output, "output")
        pub.subscribe(self.log, "log")
        pub.subscribe(self.update_progress, "progress")
        pub.subscribe(self.on_worker_finished, "worker_finished")
        pub.subscribe(self.on_task_finished, "task_finished")
        
        # 设置图标
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))
        
        self._last_notify_time = 0  # 初始化时间戳
        
        self.Centre()
        self.Show()
    
    def init_ui(self):
        # 主垂直布局
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 标题和描述
        title = wx.StaticText(self.panel, label="音频处理工具箱", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        desc = wx.StaticText(self.panel, label="选择需要使用的音频处理功能：", style=wx.ALIGN_CENTER)
        
        # 功能按钮
        btn_sizer = wx.GridSizer(2, 2, 20, 20)
        
        # 视频转音频按钮
        self.convert_btn = wx.Button(self.panel, label="视频转音频工具")
        self.convert_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.convert_btn.SetToolTip("将MP4视频文件转换为WAV音频文件")
        self.convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)
        
        # 音频对齐按钮
        self.align_btn = wx.Button(self.panel, label="音频对齐工具")
        self.align_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.align_btn.SetToolTip("将录制音频与参考音频对齐")
        self.align_btn.Bind(wx.EVT_BUTTON, self.on_align)

        # 采样率转换按钮
        self.resample_btn = wx.Button(self.panel, label="采样率转换工具")
        self.resample_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.resample_btn.SetToolTip("批量将当前/指定文件夹下的音频采样率转换为常见值")
        self.resample_btn.Bind(wx.EVT_BUTTON, self.on_resample)
        
        # 男女声拆分按钮
        self.gender_btn = wx.Button(self.panel, label="男女声拆分工具")
        self.gender_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.gender_btn.SetToolTip("在9.8秒处截断并分别输出男声与女声")
        self.gender_btn.Bind(wx.EVT_BUTTON, self.on_gender)
        
        # 添加按钮到网格
        btn_sizer.Add(self.convert_btn, 0, wx.EXPAND)
        btn_sizer.Add(self.align_btn, 0, wx.EXPAND)
        btn_sizer.Add(self.resample_btn, 0, wx.EXPAND)
        btn_sizer.Add(self.gender_btn, 0, wx.EXPAND)
        
        # 功能描述区域
        desc_box = wx.StaticBox(self.panel, label="功能描述")
        desc_sizer = wx.StaticBoxSizer(desc_box, wx.VERTICAL)
        
        self.desc_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
        self.desc_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.desc_text.SetValue(
            "1. 视频转音频工具：\n"
            "   - 将MP4视频文件转换为WAV音频格式\n"
            "   - 支持自定义采样率和声道数\n"
            "   - 批量处理整个文件夹中的视频文件\n\n"
            "2. 音频对齐工具：\n"
            "   - 将录制音频与参考音频时间对齐\n"
            "   - 自动检测最佳对齐位置\n"
            "   - 支持多种音频格式(WAV, MP3, FLAC等)\n"
            "   - 批量处理文件夹中的音频文件\n\n"
            "3. 采样率转换工具：\n"
            "   - 批量将音频采样率转换为常用采样率(48000/44100/32000/22050/16000/11025/8000)\n"
            "   - 支持选择声道(单声道/立体声)或保持原样\n"
            "   - 支持递归处理子文件夹与是否覆盖原文件\n\n"
            "4. 男女声拆分工具：\n"
            "   - 将音频在9.8秒处截断拆分为男声与女声\n"
            "   - 支持递归处理与覆盖选项\n"
            "   - 输出分别保存至自选的男女声文件夹"
        )
        
        desc_sizer.Add(self.desc_text, 1, wx.EXPAND|wx.ALL, 5)
        
        # 输出区域
        output_box = wx.StaticBox(self.panel, label="处理结果输出")
        output_sizer = wx.StaticBoxSizer(output_box, wx.VERTICAL)
        
        self.output_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        self.output_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        output_sizer.Add(self.output_text, 1, wx.EXPAND|wx.ALL, 5)
        
        # 日志区域
        log_box = wx.StaticBox(self.panel, label="操作日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        self.log_text.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        log_sizer.Add(self.log_text, 1, wx.EXPAND|wx.ALL, 5)

        self.gauge = wx.Gauge(self.panel, range=100, size=(-1, 25))
        
        # 底部按钮
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        clear_btn = wx.Button(self.panel, label="清空输出")
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        help_btn = wx.Button(self.panel, label="帮助")
        help_btn.Bind(wx.EVT_BUTTON, self.on_help)
        about_btn = wx.Button(self.panel, label="关于")
        about_btn.Bind(wx.EVT_BUTTON, self.on_about)
        exit_btn = wx.Button(self.panel, label="退出")
        exit_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        test_btn = wx.Button(self.panel, label="测试进度")
        test_btn.Bind(wx.EVT_BUTTON, self.on_test_progress)
        
        
        bottom_sizer.Add(clear_btn, 0, wx.RIGHT, 10)
        bottom_sizer.Add(help_btn, 0, wx.RIGHT, 10)
        bottom_sizer.Add(about_btn, 0, wx.RIGHT, 10)
        bottom_sizer.Add(exit_btn, 0)
        
        # 添加到主布局
        vbox.Add(title, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 15)
        vbox.Add(desc, 0, wx.ALIGN_CENTER|wx.BOTTOM, 10)
        vbox.Add(btn_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 50)
        vbox.Add(desc_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        vbox.Add(output_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        vbox.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        vbox.Add(bottom_sizer, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 10)
        vbox.Add(test_btn, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        vbox.Add(self.gauge, 0, wx.EXPAND|wx.ALL, 10)
        
        self.panel.SetSizer(vbox)
        
        # 初始化日志
        self.log("音频处理工具箱已启动")
    
    def log(self, message):
        """添加日志消息"""
        wx.CallAfter(self.log_text.AppendText, f"{message}\n")
        wx.CallAfter(self.log_text.ShowPosition, self.log_text.GetLastPosition())
    
    def update_output(self, message):
        """更新输出结果"""
        wx.CallAfter(self.output_text.AppendText, f"{message}\n")
        #wx.CallAfter(self.output_text.ShowPosition, self.output_text.GetLastPosition())

    def update_progress(self, value):
        wx.CallAfter(self.gauge.SetValue, value)

    def on_worker_finished(self):
        """工作线程完成时的统一处理"""
        wx.CallAfter(self.gauge.SetValue, 0)

        #wx.MessageBox("处理完成", "信息", wx.OK|wx.ICON_INFORMATION)
    
    def on_task_finished(self, task_name=None):
        """通用任务完成处理"""
        # 更新进度条
        if hasattr(self, 'gauge'):
            wx.CallAfter(self.gauge.SetValue, 0)
        
        # 在日志中添加记录
        log_msg = f"任务完成: {task_name if task_name else '未知任务'}"
        wx.CallAfter(self.log_text.AppendText, log_msg + "\n")
        
        current_time = time.time()

        # 显示通知（避免重复）
        if current_time - self._last_notify_time > 2:  # 2秒内不重复提示
            wx.CallAfter(
                wx.MessageBox,
                "一个后台任务已完成",
                "提示",
                wx.OK|wx.ICON_INFORMATION
            )
            self._last_notify_time = current_time
    
    
    def on_clear(self, event):
        """清空输出"""
        self.output_text.Clear()
        self.log("已清空输出结果")
    
    def on_convert(self, event):
        """打开视频转音频工具"""
        try:
            self.log("打开视频转音频工具...")
            converter = AudioConverterApp(self)  # 传递主窗口引用
            converter.Show()
        except Exception as e:
            self.log(f"打开视频转音频工具失败: {str(e)}")
            wx.MessageBox(f"无法打开视频转音频工具: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)
    
    def on_align(self, event):
        """打开音频对齐工具"""
        try:  
            self.log("打开音频对齐工具...")
            aligner = AudioAlignerApp(self)  # 传递主窗口引用
            aligner.Show()
        except Exception as e:
            self.log(f"打开音频对齐工具失败: {str(e)}")
            wx.MessageBox(f"无法打开音频对齐工具: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)

    def on_resample(self, event):
        """打开采样率转换工具"""
        try:
            self.log("打开采样率转换工具...")
            resampler = AudioResamplerApp(self)
            resampler.Show()
        except Exception as e:
            self.log(f"打开采样率转换工具失败: {str(e)}")
            wx.MessageBox(f"无法打开采样率转换工具: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)

    def on_gender(self, event):
        """打开男女声拆分工具"""
        try:
            self.log("打开男女声拆分工具...")
            splitter = AudioGenderSplitterApp(self)
            splitter.Show()
        except Exception as e:
            self.log(f"打开男女声拆分工具失败: {str(e)}")
            wx.MessageBox(f"无法打开男女声拆分工具: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)
    
    def on_help(self, event):
        """打开帮助文档"""
        self.log("打开帮助文档...")
        try:
            webbrowser.open("https://github.com/Adam-byxiao/bot_utils")
        except:
            wx.MessageBox("无法打开帮助链接，请检查网络连接", "错误", wx.OK|wx.ICON_ERROR)
    
    def on_about(self, event):
        """显示关于对话框"""
        info = AboutDialogInfo()
        info.SetName("音频处理工具箱")
        info.SetVersion("1.0")
        info.SetDescription("一个集成了视频转音频和音频对齐功能的工具集\n\n"
                          "所有处理结果将显示在主窗口的输出框中")
        info.SetCopyright("(C) 2025")
        info.SetWebSite("https://github.com/Adam-byxiao/bot_utils")
        info.AddDeveloper("Adam Xiao")
        
        AboutBox(info)
    def on_test_progress(self, event):
        """测试进度更新"""
        import threading
        threading.Thread(target=self.simulate_progress).start()
    
    def simulate_progress(self):
        """模拟耗时任务进度"""
        for i in range(101):
            wx.CallAfter(self.update_progress, i)
            wx.MilliSleep(50)  # 模拟耗时
    
    def update_progress(self, value):
        """安全更新进度"""
        if hasattr(self, 'gauge'):
            self.gauge.SetValue(value)
        else:
            wx.LogError("gauge控件不存在!")

if __name__ == "__main__":
    app = wx.App(False)
    
    # 设置高DPI支持
    if hasattr(wx, 'EnableAutoHighDPIScaling'):
        wx.EnableAutoHighDPIScaling(True)
    
    frame = AudioToolsMainFrame()
    app.MainLoop()
