import os
import wave
import wx
import wx.lib.filebrowsebutton as filebrowse
from threading import Thread
from queue import Queue

class AudioConverterApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="WAV音频通道转换工具", size=(600, 400))
        
        self.queue = Queue()
        self.working = False
        
        self.init_ui()
        self.Centre()
        self.Show()
        
        # 设置定时器检查队列
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(100)
    
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 输入文件夹选择
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.input_dir_picker = filebrowse.DirBrowseButton(
            panel, labelText="选择输入文件夹:", 
            changeCallback=self.on_input_dir_changed
        )
        hbox1.Add(self.input_dir_picker, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 输出文件夹选择
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.output_dir_picker = filebrowse.DirBrowseButton(
            panel, labelText="选择输出文件夹:", 
            changeCallback=self.on_output_dir_changed
        )
        hbox2.Add(self.output_dir_picker, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(hbox2, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 转换按钮
        self.convert_btn = wx.Button(panel, label="开始转换")
        self.convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)
        vbox.Add(self.convert_btn, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)
        
        # 日志输出
        self.log_text = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL
        )
        vbox.Add(self.log_text, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=5)
        
        panel.SetSizer(vbox)
    
    def on_input_dir_changed(self, event):
        self.log(f"输入文件夹设置为: {self.input_dir_picker.GetValue()}")
    
    def on_output_dir_changed(self, event):
        self.log(f"输出文件夹设置为: {self.output_dir_picker.GetValue()}")
    
    def on_convert(self, event):
        input_dir = self.input_dir_picker.GetValue()
        output_dir = self.output_dir_picker.GetValue()
        
        if not input_dir or not output_dir:
            wx.MessageBox("请先选择输入和输出文件夹!", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if input_dir == output_dir:
            wx.MessageBox("输入和输出文件夹不能相同!", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if self.working:
            wx.MessageBox("转换正在进行中，请稍候!", "提示", wx.OK|wx.ICON_INFORMATION)
            return
        
        self.working = True
        self.convert_btn.Disable()
        self.log("开始转换音频文件...")
        
        # 在后台线程中执行转换
        Thread(target=self.convert_audio_files, args=(input_dir, output_dir)).start()
    
    def convert_audio_files(self, input_dir, output_dir):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.queue.put(f"创建输出文件夹: {output_dir}")
            
            wav_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.wav')]
            
            if not wav_files:
                self.queue.put("没有找到WAV文件!")
                return
            
            self.queue.put(f"找到 {len(wav_files)} 个WAV文件")
            
            for filename in wav_files:
                input_path = os.path.join(input_dir, filename)
                # 添加"signal_"前缀到输出文件名
                output_filename = f"signal_{filename}"
                output_path = os.path.join(output_dir, output_filename)
                
                try:
                    with wave.open(input_path, 'rb') as wav_in:
                        params = wav_in.getparams()
                        n_channels = params.nchannels
                        
                        if n_channels == 1:
                            self.queue.put(f"跳过 {filename} (已经是单声道)")
                            continue
                        
                        self.queue.put(f"处理 {filename} (通道数: {n_channels}) -> 输出为 {output_filename}")
                        
                        # 读取所有帧数据
                        frames = wav_in.readframes(params.nframes)
                        
                        # 如果是双声道，提取左声道(通道1)
                        if n_channels == 2:
                            # 将字节数据转换为样本
                            sample_width = params.sampwidth
                            frames = self.extract_channel(frames, n_channels, sample_width, channel=0)
                        
                        # 写入单声道文件
                        with wave.open(output_path, 'wb') as wav_out:
                            out_params = (1, params.sampwidth, params.framerate, 
                                         params.nframes, params.comptype, params.compname)
                            wav_out.setparams(out_params)
                            wav_out.writeframes(frames)
                            
                except Exception as e:
                    self.queue.put(f"处理 {filename} 时出错: {str(e)}")
            
            self.queue.put("转换完成!")
            
        except Exception as e:
            self.queue.put(f"发生错误: {str(e)}")
        finally:
            self.queue.put("DONE")  # 标记工作完成
            self.working = False
    
    def extract_channel(self, frames, n_channels, sample_width, channel):
        """从多声道音频中提取指定通道的数据"""
        # 将字节数据转换为样本列表
        samples = []
        for i in range(0, len(frames), sample_width * n_channels):
            start = i + channel * sample_width
            samples.append(frames[start:start+sample_width])
        
        # 将样本重新组合为字节数据
        return b''.join(samples)
    
    def on_timer(self, event):
        """定时器事件，用于从队列中获取消息并更新UI"""
        while not self.queue.empty():
            msg = self.queue.get()
            if msg == "DONE":
                self.convert_btn.Enable()
            else:
                self.log(msg)
    
    def log(self, message):
        """向日志文本框添加消息"""
        wx.CallAfter(self.log_text.AppendText, message + "\n")

if __name__ == "__main__":
    app = wx.App(False)
    AudioConverterApp()
    app.MainLoop()
