# 作者: Adam
# 邮箱: adam@vibe.us
# 项目主页: https://github.com/Adam-byxiao/bot_utils
import wx
import wx.grid
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import numpy as np
import librosa
from pesq import pesq
from scipy.signal import correlate
from audio_analysis_utils import pesq_score

class UnifiedSpeechQualityApp(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="语音质量分析平台", size=(600, 400))
        self.theme = 'dark'  # 默认深色主题
        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        # 菜单栏
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "退出(&Q)")
        menubar.Append(file_menu, "文件(&F)")

        theme_menu = wx.Menu()
        self.menu_theme_dark = theme_menu.AppendRadioItem(wx.ID_ANY, "深色主题")
        self.menu_theme_light = theme_menu.AppendRadioItem(wx.ID_ANY, "浅色主题")
        menubar.Append(theme_menu, "主题(&T)")
        self.SetMenuBar(menubar)

        # 事件绑定
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_theme_dark, self.menu_theme_dark)
        self.Bind(wx.EVT_MENU, self.on_theme_light, self.menu_theme_light)

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 标题
        title = wx.StaticText(panel, label="语音质量分析平台", style=wx.ALIGN_CENTER)
        font = title.GetFont()
        font.PointSize += 6
        font = font.Bold()
        title.SetFont(font)
        vbox.Add(title, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=30)

        # 两个主入口按钮
        btn_single = wx.Button(panel, label="单一音频文件质量分析", size=(250, 50))
        btn_batch = wx.Button(panel, label="音频文件批量分析", size=(250, 50))
        vbox.Add(btn_single, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)
        vbox.Add(btn_batch, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)

        # 版权/版本
        version = wx.StaticText(panel, label="v1.0  by adam", style=wx.ALIGN_RIGHT)
        vbox.AddStretchSpacer()
        vbox.Add(version, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=10)

        panel.SetSizer(vbox)

        # 事件绑定
        btn_single.Bind(wx.EVT_BUTTON, self.on_single_analysis)
        btn_batch.Bind(wx.EVT_BUTTON, self.on_batch_analysis)

        # 设置默认主题
        self.SetTheme('dark')
        self.menu_theme_dark.Check(True)

    def on_exit(self, event):
        self.Close()

    def on_theme_dark(self, event):
        self.SetTheme('dark')

    def on_theme_light(self, event):
        self.SetTheme('light')

    def SetTheme(self, theme):
        self.theme = theme
        # 主界面始终保持系统默认/浅色背景，不随主题切换
        # 通知所有子窗口切换主题
        if hasattr(self, 'single_frame') and self.single_frame:
            self.single_frame.set_theme(theme)

    def on_single_analysis(self, event):
        self.single_frame = SingleFileAnalysisFrame(self, theme=self.theme)
        self.single_frame.Show()
        self.single_frame.Raise()
        self.single_frame = None

    def on_batch_analysis(self, event):
        dlg = BatchAnalysisDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

class SingleFileAnalysisFrame(wx.Frame):
    def __init__(self, parent, theme='dark'):
        super().__init__(parent, title="单一音频文件质量分析", size=(1100, 800))
        self.theme = theme
        self.last_plot_data = None  # 保存最近一次分析结果
        self.init_menu()  # 先设置菜单栏
        self.panel = wx.Panel(self)  # 再创建panel
        self.left_panel = None  # 后续赋值
        self.right_panel = None
        self.init_ui()    # 再做UI布局
        self.Centre()

    def init_menu(self):
        menubar = wx.MenuBar()
        func_menu = wx.Menu()
        # 预留功能项
        func_menu.Append(wx.ID_ANY, "导入(&I)")
        func_menu.Append(wx.ID_ANY, "导出(&E)")
        func_menu.AppendSeparator()
        func_menu.Append(wx.ID_EXIT, "关闭(&Q)")
        menubar.Append(func_menu, "功能(&F)")

        theme_menu = wx.Menu()
        self.menu_theme_dark = theme_menu.AppendRadioItem(wx.ID_ANY, "深色主题")
        self.menu_theme_light = theme_menu.AppendRadioItem(wx.ID_ANY, "浅色主题")
        menubar.Append(theme_menu, "主题(&T)")
        self.SetMenuBar(menubar)

        # 事件绑定
        self.Bind(wx.EVT_MENU, self.on_close, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_theme_dark, self.menu_theme_dark)
        self.Bind(wx.EVT_MENU, self.on_theme_light, self.menu_theme_light)
        self.menu_theme_dark.Check(self.theme == 'dark')
        self.menu_theme_light.Check(self.theme == 'light')

    def on_close(self, event):
        self.Close()

    def on_theme_dark(self, event):
        self.set_theme('dark')
        self.menu_theme_dark.Check(True)

    def on_theme_light(self, event):
        self.set_theme('light')
        self.menu_theme_light.Check(True)

    def set_panel_bg(self, panel, color):
        panel.SetBackgroundColour(color)
        for child in panel.GetChildren():
            if isinstance(child, wx.Panel):
                self.set_panel_bg(child, color)

    def set_theme(self, theme):
        self.theme = theme
        audition_dark = '#23272A'
        # 只设置右侧panel为深色，主panel和左侧panel始终保持浅色
        if theme == 'dark':
            self.set_panel_bg(self.right_panel, audition_dark)
        else:
            self.set_panel_bg(self.right_panel, wx.NullColour)
        self.right_panel.Refresh()
        # 主题切换时自动渲染当前分析结果
        if self.last_plot_data:
            self.update_plot(*self.last_plot_data)
        else:
            self.init_plot()

    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 左侧参数与结果区
        self.left_panel = wx.Panel(self.panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # 参考音频选择
        ref_box = wx.StaticBox(self.left_panel, label="1. 选择参考音频（纯净语音）")
        ref_sizer = wx.StaticBoxSizer(ref_box, wx.HORIZONTAL)
        self.ref_path = wx.TextCtrl(self.left_panel, style=wx.TE_READONLY)
        self.ref_btn = wx.Button(self.left_panel, label="浏览...")
        ref_sizer.Add(self.ref_path, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        ref_sizer.Add(self.ref_btn, flag=wx.EXPAND)
        left_sizer.Add(ref_sizer, flag=wx.EXPAND|wx.ALL, border=10)

        # 待分析音频选择
        test_box = wx.StaticBox(self.left_panel, label="2. 选择待分析音频")
        test_sizer = wx.StaticBoxSizer(test_box, wx.HORIZONTAL)
        self.test_path = wx.TextCtrl(self.left_panel, style=wx.TE_READONLY)
        self.test_btn = wx.Button(self.left_panel, label="浏览...")
        test_sizer.Add(self.test_path, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        test_sizer.Add(self.test_btn, flag=wx.EXPAND)
        left_sizer.Add(test_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 对齐算法选择
        algo_box = wx.StaticBox(self.left_panel, label="3. 对齐算法")
        algo_sizer = wx.StaticBoxSizer(algo_box, wx.HORIZONTAL)
        self.algo_choice = wx.Choice(self.left_panel, choices=["互相关 (Cross-Correlation)", "DTW (动态时间规整)"])
        self.algo_choice.SetSelection(0)
        algo_sizer.Add(self.algo_choice, proportion=1, flag=wx.EXPAND)
        left_sizer.Add(algo_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self.left_panel, label="开始分析")
        self.clear_btn = wx.Button(self.left_panel, label="清空")
        btn_sizer.Add(self.start_btn, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.clear_btn, proportion=1, flag=wx.EXPAND)
        left_sizer.Add(btn_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 质量指标显示
        metrics_box = wx.StaticBox(self.left_panel, label="质量指标")
        metrics_sizer = wx.StaticBoxSizer(metrics_box, wx.VERTICAL)
        self.metrics_text = wx.TextCtrl(self.left_panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(-1, 120))
        metrics_sizer.Add(self.metrics_text, proportion=1, flag=wx.EXPAND)
        left_sizer.Add(metrics_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 日志输出
        log_box = wx.StaticBox(self.left_panel, label="处理日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log_text = wx.TextCtrl(self.left_panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL, size=(-1, 100))
        log_sizer.Add(self.log_text, proportion=1, flag=wx.EXPAND)
        left_sizer.Add(log_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        self.left_panel.SetSizer(left_sizer)

        # 右侧图表区
        self.right_panel = wx.Panel(self.panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.figure = None
        self.canvas = None
        self.right_panel.SetSizer(right_sizer)

        main_sizer.Add(self.left_panel, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        main_sizer.Add(self.right_panel, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        self.panel.SetSizer(main_sizer)

        # 事件绑定
        self.ref_btn.Bind(wx.EVT_BUTTON, self.on_browse_ref)
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_browse_test)
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)

        self.init_plot()

    def beautify_axes(self, ax, title):
        if self.theme == 'dark':
            ax.set_facecolor('#232323')
            title_color = 'white'
            grid_color = '#444444'
            tick_color = 'white'
            spine_color = '#888888'
        else:
            ax.set_facecolor('#F7F7F7')
            title_color = '#222222'
            grid_color = '#CCCCCC'
            tick_color = '#222222'
            spine_color = '#888888'
        ax.tick_params(axis='x', colors=tick_color)
        ax.tick_params(axis='y', colors=tick_color)
        for spine in ax.spines.values():
            spine.set_color(spine_color)
        ax.set_title(title, color=title_color, fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', color=grid_color, alpha=0.3)

    def draw_beautiful_waveform(self, ax, time, signal, label, color):
        ax.plot(time, signal, color=color, linewidth=2, label=label, zorder=2)
        ax.fill_between(time, signal, color=color, alpha=0.15, zorder=1)
        legend = ax.legend(loc='upper right', facecolor=(0.14,0.14,0.14,0.7) if self.theme=='dark' else (1,1,1,0.7), edgecolor='white', fontsize=10, framealpha=0.7)
        for text in legend.get_texts():
            text.set_color('white' if self.theme=='dark' else '#222222')
        self.beautify_axes(ax, ax.get_title())

    def draw_beautiful_spectrogram(self, ax, signal, sr, title):
        cmap = 'plasma' if self.theme == 'dark' else 'viridis'
        Pxx, freqs, bins, im = ax.specgram(signal, Fs=sr, cmap=cmap)
        self.beautify_axes(ax, title)
        # 色条美化
        cbar = self.figure.colorbar(im, ax=ax, format='%+2.0f dB', pad=0.01)
        if self.theme == 'dark':
            cbar.ax.yaxis.set_tick_params(color='white') 
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            cbar.outline.set_edgecolor('white')
            cbar.ax.set_facecolor('#232323')
        else:
            cbar.ax.yaxis.set_tick_params(color='#222222')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#222222')
            cbar.outline.set_edgecolor('#222222')
            cbar.ax.set_facecolor('#F7F7F7')

    def init_plot(self):
        audition_dark = '#23272A'
        if self.theme == 'dark':
            plt.style.use('dark_background')
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            facecolor = audition_dark
        else:
            plt.style.use('default')
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            facecolor = '#F7F7F7'
        # 销毁旧的canvas和figure
        right_sizer = self.right_panel.GetSizer()
        if self.canvas is not None:
            right_sizer.Detach(self.canvas)
            self.canvas.Destroy()
            self.canvas = None
        self.figure = Figure(figsize=(8, 6), facecolor=facecolor)
        self.canvas = FigureCanvas(self.right_panel, -1, self.figure)
        right_sizer.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        self.ax1 = self.figure.add_subplot(4, 1, 1)
        self.ax2 = self.figure.add_subplot(4, 1, 2)
        self.ax3 = self.figure.add_subplot(4, 1, 3)
        self.ax4 = self.figure.add_subplot(4, 1, 4)
        t = np.linspace(0, 1, 16000)
        demo_signal = np.sin(2 * np.pi * 440 * t) * np.exp(-3 * t)
        self.draw_beautiful_waveform(self.ax1, t, demo_signal, '参考音频', '#00FF66' if self.theme=='dark' else '#007700')
        self.draw_beautiful_waveform(self.ax2, t, demo_signal * 0.7, '待分析音频', '#FFA500' if self.theme=='dark' else '#FF8800')
        self.draw_beautiful_spectrogram(self.ax3, demo_signal, 16000, '参考音频频谱图')
        self.draw_beautiful_spectrogram(self.ax4, demo_signal * 0.7, 16000, '待分析音频频谱图')
        self.figure.tight_layout(rect=[0, 0, 1, 1], pad=1.0)
        self.canvas.draw()

    def on_browse_ref(self, event):
        with wx.FileDialog(self, "选择参考音频文件", wildcard="音频文件 (*.wav;*.mp3;*.flac)|*.wav;*.mp3;*.flac", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.ref_path.SetValue(dlg.GetPath())

    def on_browse_test(self, event):
        with wx.FileDialog(self, "选择待分析音频文件", wildcard="音频文件 (*.wav;*.mp3;*.flac)|*.wav;*.mp3;*.flac", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.test_path.SetValue(dlg.GetPath())

    def on_start(self, event):
        self.metrics_text.SetValue("")
        self.log_text.SetValue("")
        ref_file = self.ref_path.GetValue()
        test_file = self.test_path.GetValue()
        if not os.path.isfile(ref_file):
            self.log_text.AppendText("[错误] 请选择有效的参考音频文件\n")
            return
        if not os.path.isfile(test_file):
            self.log_text.AppendText("[错误] 请选择有效的待分析音频文件\n")
            return
        try:
            method = 'cc' if self.algo_choice.GetSelection() == 0 else 'dtw'
            self.log_text.AppendText(f"分析中...\n")
            result = pesq_score(ref_file, test_file, method=method)
            # 刷新图表
            self.last_plot_data = (
                result['ref_audio'], result['test_audio'], result['sr'],
                os.path.basename(ref_file), os.path.basename(test_file), result
            )
            self.update_plot(*self.last_plot_data)
            # 刷新指标区
            metrics_text = f"待分析文件: {os.path.basename(test_file)}\n"
            metrics_text += f"参考文件: {os.path.basename(ref_file)}\n"
            metrics_text += f"信噪比 (SNR): {result['snr']:.2f} dB\n"
            metrics_text += f"RMS值: {result['rms']:.4f}\n"
            metrics_text += f"对齐偏移量: {result['offset']} 样本点\n"
            if result['pesq'] is not None:
                metrics_text += f"PESQ分数: {result['pesq']:.2f}\n"
            metrics_text += f"音频长度: {len(result['test_audio'])/result['sr']:.2f} 秒"
            self.metrics_text.SetValue(metrics_text)
            self.log_text.AppendText(f"分析完成\n")
        except Exception as e:
            self.log_text.AppendText(f"[错误] 分析失败: {e}\n")
            self.init_plot()
            self.last_plot_data = None

    def on_clear(self, event):
        self.ref_path.SetValue("")
        self.test_path.SetValue("")
        self.metrics_text.SetValue("")
        self.log_text.SetValue("")
        self.last_plot_data = None
        self.init_plot()

    def update_plot(self, ref_audio, test_audio, sr, ref_filename, test_filename, metrics):
        audition_dark = '#23272A'
        if self.theme == 'dark':
            plt.style.use('dark_background')
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            facecolor = audition_dark
        else:
            plt.style.use('default')
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            facecolor = '#F7F7F7'
        right_sizer = self.right_panel.GetSizer()
        if self.canvas is not None:
            right_sizer.Detach(self.canvas)
            self.canvas.Destroy()
            self.canvas = None
        self.figure = Figure(figsize=(8, 6), facecolor=facecolor)
        self.canvas = FigureCanvas(self.right_panel, -1, self.figure)
        right_sizer.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        self.ax1 = self.figure.add_subplot(4, 1, 1)
        self.ax2 = self.figure.add_subplot(4, 1, 2)
        self.ax3 = self.figure.add_subplot(4, 1, 3)
        self.ax4 = self.figure.add_subplot(4, 1, 4)
        time_ref = np.arange(len(ref_audio)) / sr
        time_test = np.arange(len(test_audio)) / sr
        self.draw_beautiful_waveform(self.ax1, time_ref, ref_audio, f"参考音频 - {ref_filename}", '#00FF66' if self.theme=='dark' else '#007700')
        self.draw_beautiful_waveform(self.ax2, time_test, test_audio, f"待分析音频 - {test_filename}", '#FFA500' if self.theme=='dark' else '#FF8800')
        self.draw_beautiful_spectrogram(self.ax3, ref_audio, sr, f"参考音频频谱图 - {ref_filename}")
        self.draw_beautiful_spectrogram(self.ax4, test_audio, sr, f"待分析音频频谱图 - {test_filename}")
        self.figure.tight_layout(rect=[0, 0, 1, 1], pad=1.0)
        self.canvas.draw()

class BatchAnalysisDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="音频文件批量分析", size=(1100, 800))
        self.panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 左侧参数与操作区
        left_panel = wx.Panel(self.panel)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # 参考音频选择（单文件）
        ref_box = wx.StaticBox(left_panel, label="1. 选择参考音频文件")
        ref_sizer = wx.StaticBoxSizer(ref_box, wx.HORIZONTAL)
        self.ref_file_picker = wx.FilePickerCtrl(left_panel, message="选择参考音频文件", wildcard="音频文件 (*.wav;*.mp3;*.flac)|*.wav;*.mp3;*.flac")
        ref_sizer.Add(self.ref_file_picker, 1, wx.EXPAND)
        left_sizer.Add(ref_sizer, 0, wx.EXPAND|wx.ALL, 10)

        # 待测文件夹
        test_box = wx.StaticBox(left_panel, label="2. 选择待分析音频文件夹")
        test_sizer = wx.StaticBoxSizer(test_box, wx.HORIZONTAL)
        self.test_dir_picker = wx.DirPickerCtrl(left_panel, message="选择待分析音频文件夹")
        test_sizer.Add(self.test_dir_picker, 1, wx.EXPAND)
        left_sizer.Add(test_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 输出Excel路径
        out_box = wx.StaticBox(left_panel, label="3. 选择结果导出Excel文件")
        out_sizer = wx.StaticBoxSizer(out_box, wx.HORIZONTAL)
        self.out_file_picker = wx.FilePickerCtrl(left_panel, message="选择导出Excel文件", wildcard="Excel文件 (*.xlsx)|*.xlsx", style=wx.FLP_SAVE|wx.FLP_OVERWRITE_PROMPT)
        out_sizer.Add(self.out_file_picker, 1, wx.EXPAND)
        left_sizer.Add(out_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 分析类型选择
        type_box = wx.StaticBox(left_panel, label="4. 选择分析类型")
        type_sizer = wx.StaticBoxSizer(type_box, wx.VERTICAL)
        self.chk_pesq = wx.CheckBox(left_panel, label="PESQ分数")
        self.chk_snr = wx.CheckBox(left_panel, label="信噪比（SNR）")
        self.chk_rms = wx.CheckBox(left_panel, label="RMS")
        self.chk_offset = wx.CheckBox(left_panel, label="对齐偏移量")
        self.chk_pesq.SetValue(True)
        self.chk_snr.SetValue(True)
        type_sizer.Add(self.chk_pesq, 0, wx.TOP|wx.BOTTOM, 2)
        type_sizer.Add(self.chk_snr, 0, wx.TOP|wx.BOTTOM, 2)
        type_sizer.Add(self.chk_rms, 0, wx.TOP|wx.BOTTOM, 2)
        type_sizer.Add(self.chk_offset, 0, wx.TOP|wx.BOTTOM, 2)
        left_sizer.Add(type_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(left_panel, label="开始分析")
        self.clear_btn = wx.Button(left_panel, label="清空")
        btn_sizer.Add(self.start_btn, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.clear_btn, 1)
        left_sizer.Add(btn_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 进度条
        self.progress = wx.Gauge(left_panel, range=100, style=wx.GA_HORIZONTAL)
        left_sizer.Add(self.progress, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 日志输出
        log_box = wx.StaticBox(left_panel, label="处理日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log_text = wx.TextCtrl(left_panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL, size=(-1, 100))
        log_sizer.Add(self.log_text, 1, wx.EXPAND)
        left_sizer.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        left_panel.SetSizer(left_sizer)
        main_sizer.Add(left_panel, 0, wx.EXPAND|wx.ALL, 5)

        # 右侧结果区
        right_panel = wx.Panel(self.panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # 结果表格
        self.grid = wx.grid.Grid(right_panel)
        self.grid.CreateGrid(0, 6)
        self.grid.SetColLabelValue(0, "文件名")
        self.grid.SetColLabelValue(1, "PESQ")
        self.grid.SetColLabelValue(2, "SNR")
        self.grid.SetColLabelValue(3, "RMS")
        self.grid.SetColLabelValue(4, "偏移量")
        self.grid.SetColLabelValue(5, "备注")
        right_sizer.Add(self.grid, 1, wx.EXPAND|wx.ALL, 10)

        # 底部操作按钮
        btn2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.export_btn = wx.Button(right_panel, label="导出Excel")
        self.hist_btn = wx.Button(right_panel, label="绘制直方图")
        btn2_sizer.Add(self.export_btn, 0, wx.RIGHT, 10)
        btn2_sizer.Add(self.hist_btn, 0)
        right_sizer.Add(btn2_sizer, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 15)

        right_panel.SetSizer(right_sizer)
        main_sizer.Add(right_panel, 1, wx.EXPAND|wx.ALL, 5)

        self.panel.SetSizer(main_sizer)
        self.Centre()

        # 事件绑定
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        self.hist_btn.Bind(wx.EVT_BUTTON, self.on_hist)

    def on_start(self, event):
        import threading, os
        self.log_text.SetValue("")
        self.progress.SetValue(0)
        self.grid.ClearGrid()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows(), True)
        ref_file = self.ref_file_picker.GetPath()
        test_dir = self.test_dir_picker.GetPath()
        if not os.path.isfile(ref_file) or not os.path.isdir(test_dir):
            self.log_text.AppendText("[错误] 请选择有效的参考音频文件和待分析音频文件夹\n")
            return
        # 获取分析类型
        metrics = []
        if self.chk_pesq.GetValue(): metrics.append('pesq')
        if self.chk_snr.GetValue(): metrics.append('snr')
        if self.chk_rms.GetValue(): metrics.append('rms')
        if self.chk_offset.GetValue(): metrics.append('offset')
        if not metrics:
            self.log_text.AppendText("[错误] 请至少选择一个分析类型\n")
            return
        # 文件配对：参考音频为单文件，遍历test_dir下所有音频
        test_files = sorted([f for f in os.listdir(test_dir) if f.lower().endswith(('.wav', '.mp3', '.flac'))])
        pairs = [(ref_file, os.path.join(test_dir, f)) for f in test_files]
        if not pairs:
            self.log_text.AppendText("[错误] 没有找到待分析的音频文件\n")
            return
        self.progress.SetRange(len(pairs))
        self.log_text.AppendText(f"共找到{len(pairs)}个待分析音频文件，开始批量分析...\n")
        threading.Thread(target=self.batch_analyze, args=(pairs, metrics), daemon=True).start()

    def batch_analyze(self, pairs, metrics):
        from audio_analysis_utils import pesq_score
        import os, wx
        for idx, (ref_file, test_file) in enumerate(pairs):
            try:
                result = pesq_score(ref_file, test_file, method='cc')
                row = self.grid.GetNumberRows()
                self.grid.AppendRows(1)
                self.grid.SetCellValue(row, 0, os.path.basename(test_file))
                self.grid.SetCellValue(row, 1, f"{result['pesq']:.2f}" if 'pesq' in metrics and result['pesq'] is not None else "")
                self.grid.SetCellValue(row, 2, f"{result['snr']:.2f}" if 'snr' in metrics and result['snr'] is not None else "")
                self.grid.SetCellValue(row, 3, f"{result['rms']:.4f}" if 'rms' in metrics and result['rms'] is not None else "")
                self.grid.SetCellValue(row, 4, f"{result['offset']}" if 'offset' in metrics and result['offset'] is not None else "")
                self.grid.SetCellValue(row, 5, "")
                wx.CallAfter(self.progress.SetValue, idx+1)
                wx.CallAfter(self.log_text.AppendText, f"{os.path.basename(test_file)} 分析完成\n")
            except Exception as e:
                row = self.grid.GetNumberRows()
                self.grid.AppendRows(1)
                self.grid.SetCellValue(row, 0, os.path.basename(test_file))
                self.grid.SetCellValue(row, 5, f"分析失败: {e}")
                wx.CallAfter(self.log_text.AppendText, f"{os.path.basename(test_file)} 分析失败: {e}\n")
                wx.CallAfter(self.progress.SetValue, idx+1)
        wx.CallAfter(self.log_text.AppendText, "批量分析完成！\n")

    def on_clear(self, event):
        self.ref_file_picker.SetPath("")
        self.test_dir_picker.SetPath("")
        self.out_file_picker.SetPath("")
        self.progress.SetValue(0)
        self.log_text.SetValue("")
        self.grid.ClearGrid()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows(), True)

    def on_export(self, event):
        # TODO: 实现导出Excel
        pass

    def on_hist(self, event):
        import wx
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        # 弹窗选择要绘制的指标
        choices = ["PESQ", "SNR", "RMS", "偏移量"]
        dlg = wx.SingleChoiceDialog(self, "请选择要绘制直方图的指标：", "选择指标", choices)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        metric = dlg.GetStringSelection()
        dlg.Destroy()
        col_map = {"PESQ": 1, "SNR": 2, "RMS": 3, "偏移量": 4}
        col = col_map[metric]
        values = []
        file_names = []
        # 只绘制选中的行
        selected_rows = self.grid.GetSelectedRows()
        if not selected_rows:
            wx.MessageBox("请先在表格中选中要绘制的文件（可多选）", "提示", wx.OK|wx.ICON_INFORMATION)
            return
        for row in selected_rows:
            val = self.grid.GetCellValue(row, col)
            fname = self.grid.GetCellValue(row, 0)
            try:
                v = float(val)
                values.append(v)
                file_names.append(fname)
            except:
                continue
        if not values:
            wx.MessageBox(f"没有可用的{metric}数据", "提示", wx.OK|wx.ICON_INFORMATION)
            return
        # 设置matplotlib支持中文
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        # 创建弹窗
        hist_dlg = wx.Dialog(self, title=f"{metric} 结果柱状图", size=(max(600, 60*len(values)), 450))
        panel = wx.Panel(hist_dlg)
        vbox = wx.BoxSizer(wx.VERTICAL)
        fig, ax = plt.subplots(figsize=(max(6, 0.6*len(values)), 4))
        bars = ax.bar(file_names, values, color='#0077FF', alpha=0.8)
        ax.set_title(f"{metric} 结果柱状图", fontsize=14)
        ax.set_xlabel("文件名")
        ax.set_ylabel(metric)
        ax.set_xticks(range(len(file_names)))
        ax.set_xticklabels(file_names, rotation=45, ha='right', fontsize=9)
        fig.tight_layout()
        canvas = FigureCanvas(panel, -1, fig)
        vbox.Add(canvas, 1, wx.EXPAND|wx.ALL, 10)
        panel.SetSizer(vbox)
        hist_dlg.Centre()
        def on_close(evt):
            plt.close(fig)
            evt.Skip()
        hist_dlg.Bind(wx.EVT_CLOSE, on_close)
        hist_dlg.ShowModal()
        hist_dlg.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    frame = UnifiedSpeechQualityApp()
    app.MainLoop() 