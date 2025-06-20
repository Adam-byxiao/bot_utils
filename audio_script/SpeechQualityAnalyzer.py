import os
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import wx
from threading import Thread
from wx.lib.pubsub import pub
import glob
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import librosa
from dtw import dtw

# 设置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def setup_chinese_font():
    """设置中文字体支持"""
    import platform
    import matplotlib.font_manager as fm
    
    # 根据操作系统设置合适的中文字体
    system = platform.system()
    
    if system == 'Windows':
        # Windows系统字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi']
    elif system == 'Darwin':  # macOS
        # macOS系统字体
        chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti']
    else:  # Linux
        # Linux系统字体
        chinese_fonts = ['WenQuanYi Micro Hei', 'DejaVu Sans', 'Liberation Sans']
    
    # 检查可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
            break
    
    plt.rcParams['axes.unicode_minus'] = False

# 初始化中文字体
setup_chinese_font()

class SpeechQualityAnalyzerApp(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="语音质量分析工具", size=(1200, 800))
        self.parent = parent
        
        pub.subscribe(self.append_log, "log")
        pub.subscribe(self.update_progress, "progress")
        pub.subscribe(self.on_worker_finished, "worker_finished")
        pub.subscribe(self.update_plot, "update_plot")
        pub.subscribe(self.add_result, "add_result")

        self.panel = wx.Panel(self)
        self.SetMinSize((800, 600))
        self.recent_files = []
        self.recent_folders = []
        self.max_recent_items = 5
        
        # 为每个选择控件维护独立的最近使用列表
        self.recent_ref_files = []  # 参考音频文件
        self.recent_test_items = []  # 待分析项目（文件或文件夹）
        self.recent_output_folders = []  # 输出文件夹
        
        # 分析结果存储
        self.analysis_results = []
        self.current_result = None
        
        self.init_ui()
        self.Centre()
        self.Show()
        
        # 订阅日志消息
        pub.subscribe(self.append_log, "log")

    def init_ui(self):
        # 主水平布局
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧控制面板
        left_panel = wx.Panel(self.panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 参考音频选择
        ref_box = wx.StaticBox(left_panel, label="1. 选择参考音频（纯净语音）")
        ref_sizer = wx.StaticBoxSizer(ref_box, wx.HORIZONTAL)
        
        self.ref_choice = wx.Choice(left_panel, choices=[], size=(350, -1))
        self.ref_choice.SetToolTip("选择参考音频文件")
        self.ref_choice.Bind(wx.EVT_CHOICE, self.on_ref_choice_change)
        self.browse_ref_btn = wx.Button(left_panel, label="浏览...")
        self.browse_ref_btn.Bind(wx.EVT_BUTTON, self.on_browse_ref)
        
        ref_sizer.Add(self.ref_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        ref_sizer.Add(self.browse_ref_btn, flag=wx.EXPAND)
        
        # 待分析音频选择
        test_box = wx.StaticBox(left_panel, label="2. 选择待分析音频文件或文件夹")
        test_sizer = wx.StaticBoxSizer(test_box, wx.HORIZONTAL)
        
        self.test_choice = wx.Choice(left_panel, choices=[], size=(350, -1))
        self.test_choice.SetToolTip("选择待分析的音频文件或包含音频文件的文件夹")
        self.test_choice.Bind(wx.EVT_CHOICE, self.on_test_choice_change)
        self.browse_test_btn = wx.Button(left_panel, label="浏览...")
        self.browse_test_btn.Bind(wx.EVT_BUTTON, self.on_browse_test)
        
        test_sizer.Add(self.test_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        test_sizer.Add(self.browse_test_btn, flag=wx.EXPAND)
        
        # 输出文件夹选择
        output_box = wx.StaticBox(left_panel, label="3. 选择输出文件夹（可选）")
        output_sizer = wx.StaticBoxSizer(output_box, wx.HORIZONTAL)
        
        self.output_choice = wx.Choice(left_panel, choices=[], size=(350, -1))
        self.output_choice.SetToolTip("选择输出文件夹，用于保存对齐后的音频文件")
        self.output_choice.Bind(wx.EVT_CHOICE, self.on_output_choice_change)
        self.browse_output_btn = wx.Button(left_panel, label="浏览...")
        self.browse_output_btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        
        output_sizer.Add(self.output_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        output_sizer.Add(self.browse_output_btn, flag=wx.EXPAND)
        
        # 分析参数设置
        param_box = wx.StaticBox(left_panel, label="分析参数")
        param_sizer = wx.StaticBoxSizer(param_box, wx.VERTICAL)
        
        # 对齐算法选择
        algo_sizer = wx.BoxSizer(wx.HORIZONTAL)
        algo_sizer.Add(wx.StaticText(left_panel, label="对齐算法:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self.algo_choice = wx.Choice(left_panel, choices=["互相关 (Cross-Correlation)", "DTW (Dynamic Time Warping)"])
        self.algo_choice.SetSelection(0)
        algo_sizer.Add(self.algo_choice, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        
        # 文件类型筛选
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filter_sizer.Add(wx.StaticText(left_panel, label="文件类型:"), flag=wx.ALIGN_CENTER_VERTICAL)
        self.file_types = [
            ("所有音频文件", "*.wav;*.mp3;*.flac;*.aiff;*.ogg"),
            ("WAV文件", "*.wav"),
            ("MP3文件", "*.mp3"),
            ("FLAC文件", "*.flac")
        ]
        self.filter_choice = wx.Choice(left_panel, choices=[t[0] for t in self.file_types])
        self.filter_choice.SetSelection(0)
        filter_sizer.Add(self.filter_choice, proportion=1, flag=wx.EXPAND|wx.LEFT, border=5)
        
        param_sizer.Add(algo_sizer, flag=wx.EXPAND|wx.BOTTOM, border=5)
        param_sizer.Add(filter_sizer, flag=wx.EXPAND)
        
        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(left_panel, label="开始分析")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.cancel_btn = wx.Button(left_panel, label="取消")
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.cancel_btn.Disable()
        
        btn_sizer.Add(self.start_btn, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.cancel_btn, proportion=1, flag=wx.EXPAND)
        
        # 质量指标显示
        metrics_box = wx.StaticBox(left_panel, label="质量指标")
        metrics_sizer = wx.StaticBoxSizer(metrics_box, wx.VERTICAL)
        
        self.metrics_text = wx.TextCtrl(left_panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(-1, 150))
        metrics_sizer.Add(self.metrics_text, proportion=1, flag=wx.EXPAND)
        
        # 日志输出
        log_box = wx.StaticBox(left_panel, label="处理日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(left_panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL, size=(-1, 120))
        log_sizer.Add(self.log_text, proportion=1, flag=wx.EXPAND)
        
        # 进度条
        self.gauge = wx.Gauge(left_panel, range=100)
        
        # 添加到左侧布局
        left_sizer.Add(ref_sizer, flag=wx.EXPAND|wx.ALL, border=10)
        left_sizer.Add(test_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(output_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(param_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(btn_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(metrics_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(log_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        left_sizer.Add(self.gauge, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        left_panel.SetSizer(left_sizer)
        
        # 右侧可视化面板
        right_panel = wx.Panel(self.panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(right_panel, -1, self.figure)
        
        # 文件列表
        file_box = wx.StaticBox(right_panel, label="分析文件列表")
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        self.file_list = wx.ListBox(right_panel, size=(-1, 100))
        self.file_list.Bind(wx.EVT_LISTBOX, self.on_file_selected)
        file_sizer.Add(self.file_list, proportion=1, flag=wx.EXPAND)
        
        right_sizer.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        right_sizer.Add(file_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        right_panel.SetSizer(right_sizer)
        
        # 设置主布局
        main_sizer.Add(left_panel, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        main_sizer.Add(right_panel, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        
        self.panel.SetSizer(main_sizer)
        
        # 加载历史记录
        self.load_recent_items()
        
        # 初始化图表
        self.init_plot()

    def init_plot(self):
        """初始化matplotlib图表"""
        # 确保中文字体设置
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.figure.clear()
        self.ax1 = self.figure.add_subplot(4, 1, 1)
        self.ax2 = self.figure.add_subplot(4, 1, 2)
        self.ax3 = self.figure.add_subplot(4, 1, 3)
        self.ax4 = self.figure.add_subplot(4, 1, 4)
        
        self.ax1.set_title("参考音频波形")
        self.ax2.set_title("待分析音频波形")
        self.ax3.set_title("参考音频频谱图")
        self.ax4.set_title("待分析音频频谱图")
        
        self.figure.tight_layout()
        self.canvas.draw()

    def load_recent_items(self):
        """加载最近使用的文件和文件夹"""
        self.update_choices()
    
    def update_choices(self):
        """更新下拉菜单选项"""
        # 保存当前选择
        ref_selection = self.ref_choice.GetSelection()
        test_selection = self.test_choice.GetSelection()
        output_selection = self.output_choice.GetSelection()
        
        # 使用智能路径显示
        ref_display_items = [self.smart_path_display(path) for path in self.recent_ref_files]
        test_display_items = [self.smart_path_display(path) for path in self.recent_test_items]
        output_display_items = [self.smart_path_display(path) for path in self.recent_output_folders]
        
        # 更新选项
        self.ref_choice.SetItems(ref_display_items)
        self.test_choice.SetItems(test_display_items)
        self.output_choice.SetItems(output_display_items)
        
        # 恢复选择（如果选项仍然存在）
        if self.recent_ref_files and ref_selection >= 0 and ref_selection < len(self.recent_ref_files):
            self.ref_choice.SetSelection(ref_selection)
        elif self.recent_ref_files:
            self.ref_choice.SetSelection(0)
            
        if (self.recent_ref_files or self.recent_test_items) and test_selection >= 0 and test_selection < len(self.recent_test_items):
            self.test_choice.SetSelection(test_selection)
        elif self.recent_ref_files or self.recent_test_items:
            self.test_choice.SetSelection(0)
            
        if self.recent_output_folders and output_selection >= 0 and output_selection < len(self.recent_output_folders):
            self.output_choice.SetSelection(output_selection)
        elif self.recent_output_folders:
            self.output_choice.SetSelection(0)
    
    def add_recent_file(self, filepath):
        """添加最近使用的文件"""
        if filepath in self.recent_ref_files:
            self.recent_ref_files.remove(filepath)
        self.recent_ref_files.insert(0, filepath)
        if len(self.recent_ref_files) > self.max_recent_items:
            self.recent_ref_files = self.recent_ref_files[:self.max_recent_items]
        self.update_choices()
    
    def add_recent_folder(self, folder):
        """添加最近使用的文件夹"""
        if folder in self.recent_output_folders:
            self.recent_output_folders.remove(folder)
        self.recent_output_folders.insert(0, folder)
        if len(self.recent_output_folders) > self.max_recent_items:
            self.recent_output_folders = self.recent_output_folders[:self.max_recent_items]
        self.update_choices()
    
    def add_recent_test_item(self, item):
        """添加最近使用的待分析项目（文件或文件夹）"""
        if item in self.recent_test_items:
            self.recent_test_items.remove(item)
        self.recent_test_items.insert(0, item)
        if len(self.recent_test_items) > self.max_recent_items:
            self.recent_test_items = self.recent_test_items[:self.max_recent_items]
        self.update_choices()
    
    def on_browse_ref(self, event):
        """浏览参考音频文件"""
        wildcard = "|".join([f"{desc} ({ext})|{ext}" for desc, ext in self.file_types])
        with wx.FileDialog(self, "选择参考音频文件", wildcard=wildcard, 
                         style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                filepath = dlg.GetPath()
                self.ref_choice.SetStringSelection(filepath)
                self.add_recent_file(filepath)
    
    def on_browse_test(self, event):
        """浏览待分析音频文件或文件夹"""
        # 先尝试选择文件
        wildcard = "|".join([f"{desc} ({ext})|{ext}" for desc, ext in self.file_types])
        with wx.FileDialog(self, "选择待分析音频文件", wildcard=wildcard, 
                         style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                filepath = dlg.GetPath()
                self.test_choice.SetStringSelection(filepath)
                self.add_recent_test_item(filepath)
                return
        
        # 如果取消文件选择，尝试选择文件夹
        with wx.DirDialog(self, "选择包含待分析音频的文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.test_choice.SetStringSelection(folder)
                self.add_recent_test_item(folder)
    
    def on_browse_output(self, event):
        """浏览输出文件夹"""
        with wx.DirDialog(self, "选择输出文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.output_choice.SetStringSelection(folder)
                self.add_recent_folder(folder)
    
    def append_log(self, message):
        """添加日志消息"""
        wx.CallAfter(self.log_text.AppendText, message + "\n")
        wx.CallAfter(self.log_text.ShowPosition, self.log_text.GetLastPosition())
    
    def update_progress(self, value):
        """更新进度条"""
        wx.CallAfter(self.gauge.SetValue, value)
    
    def update_plot(self, ref_audio, test_audio, sr, ref_filename, test_filename, metrics):
        """更新图表显示"""
        wx.CallAfter(self._update_plot, ref_audio, test_audio, sr, ref_filename, test_filename, metrics)
    
    def _update_plot(self, ref_audio, test_audio, sr, ref_filename, test_filename, metrics):
        """实际更新图表的函数"""
        # 确保中文字体设置
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.figure.clear()
        
        # 创建子图
        self.ax1 = self.figure.add_subplot(4, 1, 1)
        self.ax2 = self.figure.add_subplot(4, 1, 2)
        self.ax3 = self.figure.add_subplot(4, 1, 3)
        self.ax4 = self.figure.add_subplot(4, 1, 4)
        
        # 时间轴
        time_ref = np.arange(len(ref_audio)) / sr
        time_test = np.arange(len(test_audio)) / sr
        
        # 绘制波形
        self.ax1.plot(time_ref, ref_audio, label="参考音频")
        self.ax1.set_title(f"参考音频波形 - {ref_filename}")
        self.ax1.legend()
        self.ax1.grid(True)
        
        self.ax2.plot(time_test, test_audio, label="待分析音频", color='orange')
        self.ax2.set_title(f"待分析音频波形 - {test_filename} - SNR: {metrics['snr']:.2f} dB")
        self.ax2.legend()
        self.ax2.grid(True)
        
        # 绘制频谱图
        self.ax3.specgram(ref_audio, Fs=sr, cmap='viridis')
        self.ax3.set_title(f"参考音频频谱图 - {ref_filename}")
        
        self.ax4.specgram(test_audio, Fs=sr, cmap='plasma')
        self.ax4.set_title(f"待分析音频频谱图 - {test_filename} - RMS: {metrics['rms']:.4f}")
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        # 更新指标显示
        metrics_text = f"待分析文件: {test_filename}\n"
        metrics_text += f"参考文件: {ref_filename}\n"
        metrics_text += f"信噪比 (SNR): {metrics['snr']:.2f} dB\n"
        metrics_text += f"RMS值: {metrics['rms']:.4f}\n"
        metrics_text += f"对齐偏移量: {metrics['offset']} 样本点\n"
        metrics_text += f"音频长度: {len(test_audio)/sr:.2f} 秒"
        
        wx.CallAfter(self.metrics_text.SetValue, metrics_text)
    
    def on_file_selected(self, event):
        """文件列表选择事件"""
        selection = self.file_list.GetSelection()
        if selection >= 0 and selection < len(self.analysis_results):
            self.current_result = self.analysis_results[selection]
            # 更新图表显示
            self._update_plot(
                self.current_result['ref_audio'],
                self.current_result['test_audio'],
                self.current_result['sr'],
                self.current_result['ref_filename'],
                self.current_result['test_filename'],
                self.current_result['metrics']
            )
    
    def on_start(self, event):
        """开始分析处理"""
        ref_path = self.get_ref_path()
        test_path = self.get_test_path()
        output_folder = self.get_output_path()
        
        if not ref_path or not os.path.isfile(ref_path):
            wx.MessageBox("请选择有效的参考音频文件", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if not test_path:
            wx.MessageBox("请选择待分析的音频文件或文件夹", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        # 确定分析文件列表
        if os.path.isfile(test_path):
            audio_files = [test_path]
        elif os.path.isdir(test_path):
            # 获取文件夹中的音频文件
            ext_index = self.filter_choice.GetSelection()
            extensions = self.file_types[ext_index][1].split(";")
            audio_files = []
            for ext in extensions:
                audio_files.extend(glob.glob(os.path.join(test_path, ext)))
            
            if not audio_files:
                wx.MessageBox("输入文件夹中没有找到匹配的音频文件", "错误", wx.OK|wx.ICON_ERROR)
                return
        else:
            wx.MessageBox("请选择有效的文件或文件夹", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        # 创建输出文件夹
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
        
        # 获取对齐算法
        algo = "cc" if self.algo_choice.GetSelection() == 0 else "dtw"
        
        # 禁用按钮，开始处理
        self.start_btn.Disable()
        self.cancel_btn.Enable()
        
        # 清空之前的结果
        self.analysis_results = []
        self.file_list.Clear()
        
        # 在工作线程中处理
        self.worker = SpeechQualityWorker(ref_path, audio_files, output_folder, algo, self.parent)
        self.worker.start()
    
    def on_cancel(self, event):
        """取消处理"""
        if hasattr(self, 'worker') and self.worker.is_alive():
            self.worker.stop()
            self.append_log("用户取消处理...")
        
        self.start_btn.Enable()
        self.cancel_btn.Disable()
    
    def on_worker_finished(self):
        """工作线程完成"""
        wx.CallAfter(self.start_btn.Enable)
        wx.CallAfter(self.cancel_btn.Disable)
        wx.CallAfter(self.gauge.SetValue, 0)
        wx.MessageBox("语音质量分析完成!", "完成", wx.OK|wx.ICON_INFORMATION)

    def add_result(self, result):
        """添加分析结果"""
        wx.CallAfter(self._add_result, result)
    
    def _add_result(self, result):
        """实际添加分析结果的函数"""
        self.analysis_results.append(result)
        self.file_list.Append(result['test_filename'])
        self.file_list.SetSelection(len(self.analysis_results) - 1)

    def smart_path_display(self, path, max_length=50):
        """智能显示路径，对长路径进行截断"""
        if len(path) <= max_length:
            return path
        
        # 分割路径
        parts = path.split(os.sep)
        if len(parts) <= 2:
            return path
        
        # 保留文件名和父目录
        filename = parts[-1]
        parent_dir = parts[-2]
        
        # 计算可用长度
        available_length = max_length - len(filename) - len(parent_dir) - 5  # 5 for "..."
        
        if available_length <= 0:
            # 如果连文件名都太长，直接截断
            return "..." + filename[-(max_length-3):]
        
        # 构建显示路径
        display_path = "..."
        for part in parts[:-2]:
            if len(display_path) + len(part) + 1 <= available_length:
                display_path += os.sep + part
            else:
                break
        
        display_path += os.sep + parent_dir + os.sep + filename
        return display_path

    def get_ref_path(self):
        """获取参考音频的完整路径"""
        selection = self.ref_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_ref_files):
            return self.recent_ref_files[selection]
        return self.ref_choice.GetStringSelection()
    
    def get_test_path(self):
        """获取待分析项目的完整路径"""
        selection = self.test_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_test_items):
            return self.recent_test_items[selection]
        return self.test_choice.GetStringSelection()
    
    def get_output_path(self):
        """获取输出文件夹的完整路径"""
        selection = self.output_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_output_folders):
            return self.recent_output_folders[selection]
        return self.output_choice.GetStringSelection()

    def on_output_choice_change(self, event):
        """输出文件夹选择变化事件"""
        selection = self.output_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_output_folders):
            full_path = self.recent_output_folders[selection]
            self.output_choice.SetToolTip(f"完整路径: {full_path}")
    
    def on_ref_choice_change(self, event):
        """参考音频选择变化事件"""
        selection = self.ref_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_ref_files):
            full_path = self.recent_ref_files[selection]
            self.ref_choice.SetToolTip(f"完整路径: {full_path}")
    
    def on_test_choice_change(self, event):
        """待分析项目选择变化事件"""
        selection = self.test_choice.GetSelection()
        if selection >= 0 and selection < len(self.recent_test_items):
            full_path = self.recent_test_items[selection]
            self.test_choice.SetToolTip(f"完整路径: {full_path}")

class SpeechQualityWorker(Thread):
    def __init__(self, ref_path, audio_files, output_folder, algo, parent=None):
        Thread.__init__(self)
        self.ref_path = ref_path
        self.audio_files = audio_files
        self.output_folder = output_folder
        self.algo = algo
        self.parent = parent
        self._stop = False
        self.daemon = True
    
    def stop(self):
        self._stop = True
    
    def run(self):
        try:
            message = f"开始分析 {len(self.audio_files)} 个音频文件..."
            pub.sendMessage("log", message=message)
            if self.parent:
                pub.sendMessage("output", message=message)
            
            # 加载参考音频
            ref_audio, sr_ref = librosa.load(self.ref_path, sr=None)
            pub.sendMessage("log", message=f"已加载参考音频: {self.ref_path} (采样率: {sr_ref}Hz)")
            
            total_files = len(self.audio_files)
            for i, test_file in enumerate(self.audio_files):
                if self._stop:
                    break
                
                filename = os.path.basename(test_file)
                pub.sendMessage("log", message=f"\n分析文件 {i+1}/{total_files}: {filename}")
                
                try:
                    # 加载待分析音频
                    test_audio, sr_test = librosa.load(test_file, sr=sr_ref)
                    
                    # 检查采样率
                    if sr_ref != sr_test:
                        pub.sendMessage("log", message=f"警告: 采样率不匹配 ({sr_test}Hz), 已重采样到 {sr_ref}Hz")
                    
                    # 对齐音频
                    aligned_audio = self.align_audio(ref_audio, test_audio, self.algo)
                    pub.sendMessage("log", message=f"音频对齐完成")
                    
                    # 计算质量指标
                    metrics = self.calculate_metrics(ref_audio, aligned_audio, sr_ref)
                    pub.sendMessage("log", message=f"SNR: {metrics['snr']:.2f} dB, RMS: {metrics['rms']:.4f}")
                    
                    # 保存结果
                    result = {
                        'ref_filename': os.path.basename(self.ref_path),
                        'test_filename': filename,
                        'ref_audio': ref_audio,
                        'test_audio': aligned_audio,
                        'sr': sr_ref,
                        'metrics': metrics
                    }
                    
                    # 发送更新信号
                    pub.sendMessage("update_plot", ref_audio=ref_audio, test_audio=aligned_audio, 
                                  sr=sr_ref, ref_filename=os.path.basename(self.ref_path), test_filename=filename, metrics=metrics)
                    
                    # 发送添加结果信号
                    pub.sendMessage("add_result", result=result)
                    
                    # 保存到输出文件夹
                    if self.output_folder:
                        output_path = os.path.join(self.output_folder, f"aligned_{filename}")
                        sf.write(output_path, aligned_audio, sr_ref)
                        pub.sendMessage("log", message=f"已保存对齐音频: {output_path}")
                    
                except Exception as e:
                    pub.sendMessage("log", message=f"处理文件 {filename} 时出错: {str(e)}")
                
                # 更新进度
                progress = int((i + 1) / total_files * 100)
                pub.sendMessage("progress", value=progress)
            
            if not self._stop:
                pub.sendMessage("log", message="\n所有文件分析完成!")
                wx.CallAfter(pub.sendMessage, "worker_finished")
        
        except Exception as e:
            pub.sendMessage("log", message=f"分析过程中发生错误: {str(e)}")
            wx.CallAfter(pub.sendMessage, "worker_finished")

    def align_audio(self, ref_audio, test_audio, algo):
        """对齐音频"""
        if algo == "cc":
            # 互相关对齐
            corr = np.correlate(test_audio, ref_audio, mode="valid")
            offset = np.argmax(corr)
        else:
            # DTW对齐
            ref_mfcc = librosa.feature.mfcc(y=ref_audio, sr=16000)
            test_mfcc = librosa.feature.mfcc(y=test_audio, sr=16000)
            alignment = dtw(test_mfcc.T, ref_mfcc.T)
            offset = alignment.index1[0]
        
        # 对齐音频
        aligned_audio = test_audio[offset:offset + len(ref_audio)]
        
        # 确保长度匹配
        if len(aligned_audio) < len(ref_audio):
            padding = len(ref_audio) - len(aligned_audio)
            aligned_audio = np.concatenate([aligned_audio, np.zeros(padding)])
        
        return aligned_audio[:len(ref_audio)]

    def calculate_metrics(self, ref_audio, test_audio, sr):
        """计算质量指标"""
        # 计算RMS
        rms = np.sqrt(np.mean(np.square(test_audio)))
        
        # 计算SNR
        signal_rms = np.sqrt(np.mean(np.square(ref_audio)))
        total_rms = np.sqrt(np.mean(np.square(test_audio)))
        noise_rms = np.sqrt(total_rms**2 - signal_rms**2)
        snr = 20 * np.log10(signal_rms / noise_rms) if noise_rms > 0 else float('inf')
        
        # 计算对齐偏移量（简化）
        corr = np.correlate(test_audio, ref_audio, mode="valid")
        offset = np.argmax(corr)
        
        return {
            'snr': snr,
            'rms': rms,
            'offset': offset
        }

if __name__ == "__main__":
    app = wx.App(False)
    frame = SpeechQualityAnalyzerApp()
    app.MainLoop() 