import wx
import os
import threading
from scipy.io import wavfile
from pesq import pesq
from tabulate import tabulate
import numpy as np
import time

class PESQCalculatorFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='PESQ Score Calculator', size=(900, 700))
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 参考音频文件选择
        ref_box = wx.StaticBox(panel, label="参考音频文件")
        ref_sizer = wx.StaticBoxSizer(ref_box, wx.HORIZONTAL)
        
        self.ref_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.ref_button = wx.Button(panel, label="选择参考文件")
        self.ref_button.Bind(wx.EVT_BUTTON, self.on_select_ref)
        
        ref_sizer.Add(self.ref_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        ref_sizer.Add(self.ref_button, flag=wx.ALL, border=5)
        
        # 目标音频文件/文件夹选择
        target_box = wx.StaticBox(panel, label="目标音频文件/文件夹")
        target_sizer = wx.StaticBoxSizer(target_box, wx.VERTICAL)
        
        # 选择模式
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mode_radio = wx.RadioBox(panel, label="选择模式", choices=["文件夹", "单个文件"], 
                                     majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.mode_radio.SetSelection(0)
        self.mode_radio.Bind(wx.EVT_RADIOBOX, self.on_mode_change)
        mode_sizer.Add(self.mode_radio, flag=wx.ALL, border=5)
        
        # 文件/文件夹选择
        select_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.target_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.target_button = wx.Button(panel, label="选择文件夹")
        self.target_button.Bind(wx.EVT_BUTTON, self.on_select_target)
        
        select_sizer.Add(self.target_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        select_sizer.Add(self.target_button, flag=wx.ALL, border=5)
        
        target_sizer.Add(mode_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        target_sizer.Add(select_sizer, flag=wx.EXPAND | wx.ALL, border=5)
        
        # 带宽选择
        bw_box = wx.StaticBox(panel, label="带宽设置")
        bw_sizer = wx.StaticBoxSizer(bw_box, wx.HORIZONTAL)
        
        self.bw_radio = wx.RadioBox(panel, label="", choices=["窄带 (NB)", "宽带 (WB)"], 
                                   majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.bw_radio.SetSelection(0)  # 默认选择窄带
        
        bw_sizer.Add(self.bw_radio, flag=wx.ALL, border=5)
        
        # 计算按钮
        self.calc_button = wx.Button(panel, label="开始计算PESQ")
        self.calc_button.Bind(wx.EVT_BUTTON, self.on_calculate)
        
        # 进度条
        progress_box = wx.StaticBox(panel, label="计算进度")
        progress_sizer = wx.StaticBoxSizer(progress_box, wx.VERTICAL)
        self.progress = wx.Gauge(panel, range=100, size=(400, 25))
        self.progress_text = wx.StaticText(panel, label="准备就绪")
        progress_sizer.Add(self.progress, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        progress_sizer.Add(self.progress_text, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        
        # 结果显示区域
        result_box = wx.StaticBox(panel, label="计算结果")
        result_sizer = wx.StaticBoxSizer(result_box, wx.VERTICAL)
        
        self.result_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        result_sizer.Add(self.result_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        
        # 按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_button = wx.Button(panel, label="保存结果")
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save_results)
        self.save_button.Disable()
        
        self.clear_button = wx.Button(panel, label="清空结果")
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear_results)
        
        button_sizer.Add(self.save_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.clear_button, flag=wx.ALL, border=5)
        
        # 布局
        vbox.Add(ref_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(target_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(bw_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.calc_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        vbox.Add(progress_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(result_sizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        
        panel.SetSizer(vbox)
        
        # 初始化变量
        self.ref_file = ""
        self.target_paths = []
        self.results = []
        
    def on_mode_change(self, event):
        if self.mode_radio.GetSelection() == 0:  # 文件夹模式
            self.target_button.SetLabel("选择文件夹")
        else:  # 单个文件模式
            self.target_button.SetLabel("选择文件")
        self.target_text.SetValue("")
        self.target_paths = []
        
    def on_select_ref(self, event):
        with wx.FileDialog(self, "选择参考音频文件", wildcard="WAV files (*.wav)|*.wav",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            self.ref_file = fileDialog.GetPath()
            self.ref_text.SetValue(self.ref_file)
            
    def on_select_target(self, event):
        if self.mode_radio.GetSelection() == 0:  # 文件夹模式
            with wx.DirDialog(self, "选择目标文件夹", style=wx.DD_DEFAULT_STYLE) as dirDialog:
                if dirDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                self.target_paths = [dirDialog.GetPath()]
                self.target_text.SetValue(self.target_paths[0])
        else:  # 单个文件模式
            with wx.FileDialog(self, "选择目标音频文件", wildcard="WAV files (*.wav)|*.wav",
                              style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
                
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                self.target_paths = [fileDialog.GetPath()]
                self.target_text.SetValue(self.target_paths[0])
            
    def get_file_list(self, *paths):
        file_list = []
        
        for path in paths:
            if os.path.isdir(path):  
                for item in os.listdir(path):
                    full_path = os.path.join(path, item)
                    if os.path.isfile(full_path) and full_path.lower().endswith('.wav') and ('aligned_' not in os.path.basename(full_path)):
                        file_list.append(full_path)
            elif os.path.isfile(path):  
                file_list.append(path)
        
        return file_list
    
    def pesq_calc(self, ref_file, deg_files, bw="nb"):
        # 读取参考音频文件
        ref_rate, ref_ = wavfile.read(ref_file)
        ref_ = ref_.astype(np.float32) 
        rms_ref = np.sqrt(np.mean(ref_**2))
        results = []
        degs = self.get_file_list(*deg_files)
        
        total_files = len(degs)
        wx.CallAfter(self.progress_text.SetLabel, f"找到 {total_files} 个文件，开始计算...")
        
        for i, deg_file in enumerate(degs):
            try:
                # 更新进度
                progress = int((i / total_files) * 100)
                wx.CallAfter(self.progress.SetValue, progress)
                wx.CallAfter(self.progress_text.SetLabel, f"正在处理: {os.path.basename(deg_file)} ({i+1}/{total_files})")
                
                ref = ref_.copy()
                rate_deg, deg = wavfile.read(deg_file)
                
                # 检查文件是否为空
                if len(ref) == 0 or len(deg) == 0:
                    results.append([deg_file, "Length mismatch", "-"])
                    continue
                
                # 检查采样率是否匹配
                if ref_rate != rate_deg:
                    results.append([deg_file, "Sample rate mismatch", "-"])
                    continue
                
                # 长度对齐
                if len(ref) != len(deg):
                    min_length = min(len(ref), len(deg))
                    ref = ref[len(ref) - min_length:]
                    deg = deg[len(deg) - min_length:]
                
                # 计算PESQ分数
                deg = deg.astype(np.float32) 
                rms_deg = np.sqrt(np.mean(deg**2))
                gain = rms_ref / rms_deg
                
                for j in range(len(deg)):
                    deg[j] = deg[j] * gain
                
                pesq_val = 0
                if bw == 'nb':
                    pesq_val = pesq(ref_rate, ref, deg, 'nb')
                else:
                    pesq_val = pesq(ref_rate, ref, deg, 'wb')
                
                results.append([deg_file, "OK", f"{pesq_val:.2f}"])
                
            except Exception as e:
                results.append([deg_file, f"Error: {e}", "-"])
        
        # 完成进度
        wx.CallAfter(self.progress.SetValue, 100)
        wx.CallAfter(self.progress_text.SetLabel, "计算完成")
        
        # 显示结果
        headers = ["File", "Status", f"PESQ ({bw.upper()})"]
        result_table = tabulate(results, headers=headers, tablefmt="grid")
        wx.CallAfter(self.result_text.SetValue, result_table)
        wx.CallAfter(self.save_button.Enable)
        
        self.results = results
        
    def on_calculate(self, event):
        if not self.ref_file:
            wx.MessageBox("请先选择参考音频文件", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        if not self.target_paths:
            wx.MessageBox("请先选择目标音频文件/文件夹", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        # 禁用按钮
        self.calc_button.Disable()
        self.save_button.Disable()
        self.progress.SetValue(0)
        self.progress_text.SetLabel("准备计算...")
        
        # 获取带宽设置
        bw = "nb" if self.bw_radio.GetSelection() == 0 else "wb"
        
        # 在新线程中执行计算
        thread = threading.Thread(target=self.pesq_calc, args=(self.ref_file, self.target_paths, bw))
        thread.daemon = True
        thread.start()
        
        # 启动定时器检查线程状态
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(100)
        
    def on_timer(self, event):
        # 检查计算是否完成
        if self.progress.GetValue() == 100:
            self.timer.Stop()
            self.calc_button.Enable()
            
    def on_save_results(self, event):
        with wx.FileDialog(self, "保存结果", wildcard="Text files (*.txt)|*.txt",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w', encoding='utf-8') as file:
                    file.write(self.result_text.GetValue())
                wx.MessageBox("结果已保存", "成功", wx.OK | wx.ICON_INFORMATION)
            except IOError:
                wx.MessageBox("保存失败", "错误", wx.OK | wx.ICON_ERROR)
                
    def on_clear_results(self, event):
        self.result_text.SetValue("")
        self.progress.SetValue(0)
        self.progress_text.SetLabel("准备就绪")
        self.save_button.Disable()

def main():
    app = wx.App()
    frame = PESQCalculatorFrame()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main() 