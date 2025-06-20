import os
import numpy as np
import soundfile as sf
from pystoi import stoi
import matplotlib.pyplot as plt
import wx
import wx.grid
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from threading import Thread
from wx.lib.pubsub import pub

class STOIAnalyzerApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="语音清晰度分析工具", size=(1000, 700))
        
        self.panel = wx.Panel(self)
        self.results = []
        self.reference_audio = None
        self.reference_fs = None
        self.reference_path = None
        self.init_ui()
        self.Centre()
        self.Show()
        
        # 订阅消息
        pub.subscribe(self.update_log, "log")
        pub.subscribe(self.update_result, "result")

    def init_ui(self):
        # 主布局
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 文件选择区域
        file_box = wx.StaticBox(self.panel, label="文件选择")
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        # 文件夹选择
        folder_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.folder_path = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        folder_btn = wx.Button(self.panel, label="选择测试文件夹...")
        folder_btn.Bind(wx.EVT_BUTTON, self.on_select_folder)
        folder_sizer.Add(self.folder_path, 1, wx.EXPAND|wx.RIGHT, 5)
        folder_sizer.Add(folder_btn, 0)
        
        # 基准音频选择
        ref_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ref_sizer.Add(wx.StaticText(self.panel, label="基准音频:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.ref_path = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        ref_btn = wx.Button(self.panel, label="选择基准文件...")
        ref_btn.Bind(wx.EVT_BUTTON, self.on_select_reference)
        ref_sizer.Add(self.ref_path, 1, wx.EXPAND|wx.RIGHT, 5)
        ref_sizer.Add(ref_btn, 0)
        
        # 文件列表
        self.file_list = wx.ListCtrl(
            self.panel, 
            style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.BORDER_SUNKEN
        )
        self.file_list.InsertColumn(0, "文件名", width=200)
        self.file_list.InsertColumn(1, "路径", width=400)
        
        # 添加多选功能
        self.file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_file_select)
        self.file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_file_select)
        
        file_sizer.Add(folder_sizer, 0, wx.EXPAND|wx.ALL, 5)
        file_sizer.Add(ref_sizer, 0, wx.EXPAND|wx.ALL, 5)
        file_sizer.Add(self.file_list, 1, wx.EXPAND|wx.ALL, 5)
        
        # 分析控制区域
        ctrl_box = wx.StaticBox(self.panel, label="分析控制")
        ctrl_sizer = wx.StaticBoxSizer(ctrl_box, wx.HORIZONTAL)
        
        analyze_btn = wx.Button(self.panel, label="分析选定文件")
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze)
        
        clear_btn = wx.Button(self.panel, label="清除结果")
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        
        plot_btn = wx.Button(self.panel, label="显示图表")
        plot_btn.Bind(wx.EVT_BUTTON, self.on_show_plot)
        
        ctrl_sizer.Add(analyze_btn, 0, wx.RIGHT, 10)
        ctrl_sizer.Add(clear_btn, 0, wx.RIGHT, 10)
        ctrl_sizer.Add(plot_btn, 0)
        
        # 结果显示区域
        result_box = wx.StaticBox(self.panel, label="分析结果")
        result_sizer = wx.StaticBoxSizer(result_box, wx.VERTICAL)
        
        self.result_grid = wx.grid.Grid(self.panel)
        self.result_grid.CreateGrid(0, 3)
        self.result_grid.SetColLabelValue(0, "文件名")
        self.result_grid.SetColLabelValue(1, "STOI分数")
        self.result_grid.SetColLabelValue(2, "清晰度评价")
        self.result_grid.AutoSizeColumns()
        
        result_sizer.Add(self.result_grid, 1, wx.EXPAND|wx.ALL, 5)
        
        # 日志区域
        log_box = wx.StaticBox(self.panel, label="日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(
            self.panel, 
            style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL
        )
        log_sizer.Add(self.log_text, 1, wx.EXPAND|wx.ALL, 5)
        
        # 组装主布局
        vbox.Add(file_sizer, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(ctrl_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        vbox.Add(result_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        vbox.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        
        self.panel.SetSizer(vbox)

    def on_select_folder(self, event):
        with wx.DirDialog(self, "选择包含测试音频的文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.folder_path.SetValue(folder)
                self.load_files(folder)

    def on_select_reference(self, event):
        with wx.FileDialog(self, "选择基准音频文件", wildcard="音频文件 (*.wav;*.mp3;*.flac)|*.wav;*.mp3;*.flac") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.ref_path.SetValue(path)
                try:
                    self.reference_audio, self.reference_fs = sf.read(path)
                    if self.reference_audio.ndim > 1:
                        self.reference_audio = np.mean(self.reference_audio, axis=1)
                    self.reference_path = path
                    pub.sendMessage("log", message=f"已设置基准音频: {os.path.basename(path)}")
                except Exception as e:
                    pub.sendMessage("log", message=f"加载基准音频失败: {str(e)}")
                    self.reference_audio = None
                    self.reference_fs = None
                    self.reference_path = None

    def load_files(self, folder):
        self.file_list.DeleteAllItems()
        audio_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.wav', '.mp3', '.flac')):
                    audio_files.append((file, os.path.join(root, file)))
        
        for idx, (name, path) in enumerate(audio_files):
            self.file_list.InsertItem(idx, name)
            self.file_list.SetItem(idx, 1, path)
        
        pub.sendMessage("log", message=f"已加载 {len(audio_files)} 个测试音频文件")

    def on_file_select(self, event):
        selected = []
        item = -1
        while True:
            item = self.file_list.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item == -1:
                break
            selected.append(self.file_list.GetItem(item, 1).GetText())
        
        pub.sendMessage("log", message=f"已选择 {len(selected)} 个测试文件")

    def on_analyze(self, event):
        if self.reference_audio is None:
            wx.MessageBox("请先选择基准音频文件", "错误", wx.OK|wx.ICON_ERROR)
            return
            
        selected_files = []
        item = -1
        while True:
            item = self.file_list.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item == -1:
                break
            selected_files.append(self.file_list.GetItem(item, 1).GetText())
        
        if not selected_files:
            wx.MessageBox("请先选择要分析的测试文件", "提示", wx.OK|wx.ICON_INFORMATION)
            return
        
        # 在工作线程中执行分析
        worker = AnalysisWorker(selected_files, self.reference_audio, self.reference_fs)
        worker.start()

    def on_clear(self, event):
        self.result_grid.ClearGrid()
        if self.result_grid.GetNumberRows() > 0:
            self.result_grid.DeleteRows(0, self.result_grid.GetNumberRows())
        self.results = []
        pub.sendMessage("log", message="已清除所有分析结果")

    def on_show_plot(self, event):
        if not self.results:
            wx.MessageBox("没有可显示的分析结果", "提示", wx.OK|wx.ICON_INFORMATION)
            return
        
        # 在新窗口中显示图表
        plot_frame = wx.Frame(self, title="清晰度分析结果图表", size=(800, 600))
        panel = wx.Panel(plot_frame)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建matplotlib图形
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        # 准备数据
        df = pd.DataFrame(self.results)
        files = [os.path.basename(f) for f in df['file']]
        scores = df['score']
        
        # 绘制直方图
        ax.bar(files, scores, color='skyblue')
        ax.set_title(f'语音清晰度(STOI)分析结果 (基准: {os.path.basename(self.reference_path)})')
        ax.set_xlabel('测试音频文件')
        ax.set_ylabel('STOI分数')
        ax.set_ylim(0, 1)
        ax.tick_params(axis='x', rotation=45)
        fig.tight_layout()
        
        # 将图形嵌入到wxPython
        canvas = FigureCanvas(panel, -1, fig)
        sizer.Add(canvas, 1, wx.EXPAND|wx.ALL, 5)
        panel.SetSizer(sizer)
        
        plot_frame.Show()

    def update_log(self, message):
        self.log_text.AppendText(f"{message}\n")

    def update_result(self, result):
        row = self.result_grid.GetNumberRows()
        self.result_grid.AppendRows(1)
        
        self.result_grid.SetCellValue(row, 0, os.path.basename(result['file']))
        self.result_grid.SetCellValue(row, 1, f"{result['score']:.4f}")
        self.result_grid.SetCellValue(row, 2, self.get_quality_label(result['score']))
        
        self.results.append(result)
        self.result_grid.AutoSizeColumns()

    def get_quality_label(self, score):
        if score >= 0.75:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.45:
            return "一般"
        else:
            return "较差"

class AnalysisWorker(Thread):
    def __init__(self, file_list, reference_audio, reference_fs):
        Thread.__init__(self)
        self.file_list = file_list
        self.reference_audio = reference_audio
        self.reference_fs = reference_fs
        self.daemon = True

    def run(self):
        pub.sendMessage("log", message=f"开始分析 {len(self.file_list)} 个文件...")
        
        for file in self.file_list:
            try:
                # 读取音频文件
                audio, fs = sf.read(file)
                
                # 如果是立体声，转换为单声道
                if audio.ndim > 1:
                    audio = np.mean(audio, axis=1)
                
                # 确保采样率一致
                if fs != self.reference_fs:
                    pub.sendMessage("log", message=f"警告: {os.path.basename(file)} 采样率({fs}Hz)与基准音频({self.reference_fs}Hz)不一致")
                
                # 计算STOI分数
                score = stoi(self.reference_audio, audio, self.reference_fs, extended=False)
                
                pub.sendMessage("result", result={
                    'file': file,
                    'score': score
                })
                
                pub.sendMessage("log", message=f"分析完成: {os.path.basename(file)} - STOI: {score:.4f}")
            
            except Exception as e:
                pub.sendMessage("log", message=f"分析文件 {file} 时出错: {str(e)}")
        
        pub.sendMessage("log", message="所有文件分析完成")

if __name__ == "__main__":
    app = wx.App(False)
    frame = STOIAnalyzerApp()
    app.MainLoop()
