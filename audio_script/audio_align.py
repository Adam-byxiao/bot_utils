import os
import numpy as np
import soundfile as sf
from scipy import signal
import wx
from threading import Thread
from wx.lib.pubsub import pub
import glob

class AudioAlignerApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="音频批量对齐工具", size=(1080, 720))
        
        pub.subscribe(self.append_log, "log")
        pub.subscribe(self.update_progress, "progress")
        pub.subscribe(self.on_worker_finished, "worker_finished")

        self.panel = wx.Panel(self)
        self.SetMinSize((550, 400))
        self.recent_files = []
        self.recent_folders = []
        self.max_recent_items = 5
        
        self.init_ui()
        self.Centre()
        self.Show()
        
        # 订阅日志消息
        pub.subscribe(self.append_log, "log")

    def init_ui(self):
        # 主垂直布局
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 原始音频选择
        original_box = wx.StaticBox(self.panel, label="1. 选择原始参考音频")
        original_sizer = wx.StaticBoxSizer(original_box, wx.HORIZONTAL)
        
        self.original_choice = wx.Choice(self.panel, choices=[], size=(300, -1))
        self.browse_original_btn = wx.Button(self.panel, label="浏览...")
        self.browse_original_btn.Bind(wx.EVT_BUTTON, self.on_browse_original)
        
        original_sizer.Add(self.original_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        original_sizer.Add(self.browse_original_btn, flag=wx.EXPAND)
        
        # 输入文件夹选择
        input_box = wx.StaticBox(self.panel, label="2. 选择包含待对齐音频的文件夹")
        input_sizer = wx.StaticBoxSizer(input_box, wx.HORIZONTAL)
        
        self.input_choice = wx.Choice(self.panel, choices=[], size=(300, -1))
        self.browse_input_btn = wx.Button(self.panel, label="浏览...")
        self.browse_input_btn.Bind(wx.EVT_BUTTON, self.on_browse_input)
        
        input_sizer.Add(self.input_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        input_sizer.Add(self.browse_input_btn, flag=wx.EXPAND)
        
        # 输出文件夹选择
        output_box = wx.StaticBox(self.panel, label="3. 选择输出文件夹")
        output_sizer = wx.StaticBoxSizer(output_box, wx.HORIZONTAL)
        
        self.output_choice = wx.Choice(self.panel, choices=[], size=(300, -1))
        self.browse_output_btn = wx.Button(self.panel, label="浏览...")
        self.browse_output_btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        
        output_sizer.Add(self.output_choice, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        output_sizer.Add(self.browse_output_btn, flag=wx.EXPAND)
        
        # 文件类型筛选
        filter_box = wx.StaticBox(self.panel, label="文件类型筛选")
        filter_sizer = wx.StaticBoxSizer(filter_box, wx.HORIZONTAL)
        
        self.file_types = [
            ("所有音频文件", "*.wav;*.mp3;*.flac;*.aiff;*.ogg"),
            ("WAV文件", "*.wav"),
            ("MP3文件", "*.mp3"),
            ("FLAC文件", "*.flac")
        ]
        self.filter_choice = wx.Choice(self.panel, choices=[t[0] for t in self.file_types])
        self.filter_choice.SetSelection(0)
        
        filter_sizer.Add(self.filter_choice, proportion=1, flag=wx.EXPAND)
        
        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self.panel, label="开始对齐")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.cancel_btn = wx.Button(self.panel, label="取消")
        self.cancel_btn.Disable()
        
        btn_sizer.Add(self.start_btn, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=5)
        btn_sizer.Add(self.cancel_btn, proportion=1, flag=wx.EXPAND)
        
        # 日志输出
        log_box = wx.StaticBox(self.panel, label="处理日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        log_sizer.Add(self.log_text, proportion=1, flag=wx.EXPAND)
        
        # 进度条
        self.gauge = wx.Gauge(self.panel, range=100)
        
        # 添加到主布局
        vbox.Add(original_sizer, flag=wx.EXPAND|wx.ALL, border=10)
        vbox.Add(input_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(output_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(filter_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(btn_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(log_sizer, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(self.gauge, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        self.panel.SetSizer(vbox)
        
        # 加载历史记录
        self.load_recent_items()
    
    def load_recent_items(self):
        """加载最近使用的文件和文件夹"""
        # 这里简单实现，实际应用中可以从配置文件加载
        self.update_choices()
    
    def update_choices(self):
        """更新下拉菜单选项"""
        self.original_choice.SetItems(self.recent_files)
        self.input_choice.SetItems(self.recent_folders)
        self.output_choice.SetItems(self.recent_folders)
        
        if self.recent_files:
            self.original_choice.SetSelection(0)
        if self.recent_folders:
            self.input_choice.SetSelection(0)
            self.output_choice.SetSelection(0)
    
    def add_recent_file(self, filepath):
        """添加最近使用的文件"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        if len(self.recent_files) > self.max_recent_items:
            self.recent_files = self.recent_files[:self.max_recent_items]
        self.update_choices()
    
    def add_recent_folder(self, folder):
        """添加最近使用的文件夹"""
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        if len(self.recent_folders) > self.max_recent_items:
            self.recent_folders = self.recent_folders[:self.max_recent_items]
        self.update_choices()
    
    def on_browse_original(self, event):
        """浏览原始音频文件"""
        wildcard = "|".join([f"{desc} ({ext})|{ext}" for desc, ext in self.file_types])
        with wx.FileDialog(self, "选择原始参考音频", wildcard=wildcard, 
                         style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                filepath = dlg.GetPath()
                self.original_choice.SetStringSelection(filepath)
                self.add_recent_file(filepath)
    
    def on_browse_input(self, event):
        """浏览输入文件夹"""
        with wx.DirDialog(self, "选择包含待对齐音频的文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.input_choice.SetStringSelection(folder)
                self.add_recent_folder(folder)
    
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
    
    def on_start(self, event):
        """开始对齐处理"""
        original_path = self.original_choice.GetStringSelection()
        input_folder = self.input_choice.GetStringSelection()
        output_folder = self.output_choice.GetStringSelection()
        
        if not original_path or not os.path.isfile(original_path):
            wx.MessageBox("请选择有效的原始参考音频文件", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if not input_folder or not os.path.isdir(input_folder):
            wx.MessageBox("请选择有效的输入文件夹", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if not output_folder:
            wx.MessageBox("请选择输出文件夹", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 获取文件列表
        ext_index = self.filter_choice.GetSelection()
        extensions = self.file_types[ext_index][1].split(";")
        audio_files = []
        for ext in extensions:
            audio_files.extend(glob.glob(os.path.join(input_folder, ext)))
        
        if not audio_files:
            wx.MessageBox("输入文件夹中没有找到匹配的音频文件", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        # 禁用按钮，开始处理
        self.start_btn.Disable()
        self.cancel_btn.Enable()
        
        # 在工作线程中处理
        self.worker = AudioAlignerWorker(original_path, audio_files, output_folder)
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
        wx.MessageBox("音频对齐处理完成!", "完成", wx.OK|wx.ICON_INFORMATION)

class AudioAlignerWorker(Thread):
    def __init__(self, original_path, audio_files, output_folder):
        Thread.__init__(self)
        self.original_path = original_path
        self.audio_files = audio_files
        self.output_folder = output_folder
        self._stop = False
        self.daemon = True
    
    def stop(self):
        self._stop = True
    
    def run(self):
        try:
            pub.sendMessage("log", message=f"开始处理 {len(self.audio_files)} 个音频文件...")
            
            # 加载原始音频
            original_audio, sr_orig = sf.read(self.original_path, always_2d=True)
            pub.sendMessage("log", message=f"已加载原始参考音频: {self.original_path}")
            
            total_files = len(self.audio_files)
            for i, input_file in enumerate(self.audio_files):
                if self._stop:
                    break
                
                filename = os.path.basename(input_file)
                pub.sendMessage("log", message=f"\n处理文件 {i+1}/{total_files}: {filename}")
                
                try:
                    # 加载录制音频
                    recorded_audio, sr_rec = sf.read(input_file, always_2d=True)
                    
                    # 检查采样率
                    if sr_orig != sr_rec:
                        pub.sendMessage("log", message=f"警告: 采样率不匹配 ({sr_rec}Hz), 将直接处理")
                    
                    # 找到对齐偏移量
                    offset = self.find_alignment_offset(original_audio, recorded_audio)
                    pub.sendMessage("log", message=f"找到对齐偏移量: {offset} 样本点 ({offset/sr_orig:.3f}秒)")
                    
                    # 创建时间轴平移后的音频
                    if offset >= 0:
                        aligned_audio = recorded_audio[offset:]
                    else:
                        aligned_audio = np.concatenate([
                            np.zeros((-offset, recorded_audio.shape[1]) if recorded_audio.ndim > 1 else np.zeros(-offset),
                            recorded_audio)
                        ])
                    
                    # 保持与原始音频相同的长度
                    aligned_audio = aligned_audio[:len(original_audio)]
                    
                    # 保存结果
                    output_path = os.path.join(self.output_folder, f"aligned_{filename}")
                    sf.write(output_path, aligned_audio, sr_orig)
                    pub.sendMessage("log", message=f"已保存对齐后的音频: {output_path}")
                    
                except Exception as e:
                    pub.sendMessage("log", message=f"处理文件 {filename} 时出错: {str(e)}")
                
                # 更新进度
                progress = int((i + 1) / total_files * 100)
                pub.sendMessage("log", message=f"进度: {progress}%")
                wx.CallAfter(pub.sendMessage, "progress", value=progress)
            
            if not self._stop:
                pub.sendMessage("log", message="\n所有文件处理完成!")
                wx.CallAfter(pub.sendMessage, "worker_finished")
        
        except Exception as e:
            pub.sendMessage("log", message=f"处理过程中发生错误: {str(e)}")
            wx.CallAfter(pub.sendMessage, "worker_finished")
    
    def find_alignment_offset(self, original, recorded):
        """找到录制音频与原始音频的最佳对齐偏移量"""
        # 使用互相关计算对齐位置（多通道处理）
        if original.ndim == 1:
            original = original.reshape(-1, 1)
        if recorded.ndim == 1:
            recorded = recorded.reshape(-1, 1)
        
        # 计算每个通道的互相关并求和
        total_corr = None
        for ch in range(original.shape[1]):
            corr = signal.correlate(recorded[:, ch], original[:, ch], mode='valid', method='fft')
            if total_corr is None:
                total_corr = corr
            else:
                total_corr += corr
        
        best_offset = np.argmax(total_corr)
        return best_offset

if __name__ == "__main__":
    app = wx.App(False)
    frame = AudioAlignerApp()
    app.MainLoop()