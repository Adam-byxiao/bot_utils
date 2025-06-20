import wx
import wx.lib.plot as plot
import pyaudio
import numpy as np
from threading import Thread
import time
import wave
from datetime import datetime

class AudioPlotWindow(wx.Frame):
    """显示音频时域信号的新窗口"""
    def __init__(self, parent, title="Audio Signal"):
        super(AudioPlotWindow, self).__init__(parent, title=title, size=(800, 400))
        self.panel = wx.Panel(self)
        self.plotCanvas = plot.PlotCanvas(self.panel)
        self.plotCanvas.SetInitialSize(size=(780, 350))
        
        # 设置布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plotCanvas, 1, wx.EXPAND|wx.ALL, 5)
        self.panel.SetSizer(sizer)
        
        # 初始化绘图数据
        self.line_in_data = []
        self.line_out_data = []
        self.time_axis = []
        self.start_marker = None
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def on_close(self, event):
        """处理窗口关闭事件"""
        try:
            if hasattr(self, 'plotCanvas') and self.plotCanvas:
                try:
                    self.plotCanvas.Clear()
                except:
                    pass
        except:
            pass
        
        # 安全销毁窗口
        try:
            if self:
                self.Destroy()
        except:
            pass
        
        # 通知主窗口这个绘图窗口已经关闭
        if hasattr(self, '_parent') and self._parent:
            try:
                if hasattr(self._parent, 'plot_window'):
                    self._parent.plot_window = None
            except:
                pass
            
        # 如果是从事件调用的，跳过默认处理
        if event:
            event.Skip()
    
    def is_alive(self):
        """检查窗口是否仍然存在"""
        try:
            return self and self.GetHandle() and not self.IsBeingDeleted()
        except:
            return False
    
    def update_plot(self, line_in, line_out, sample_rate, start_time):
        """更新绘图数据"""
        if not self.is_alive():
            return False
            
        # 创建时间轴
        length = min(len(line_in), len(line_out))
        self.time_axis = np.arange(0, length) / sample_rate
        
        # 存储数据
        self.line_in_data = line_in[:length]
        self.line_out_data = line_out[:length]
        self.start_marker = start_time
        
        # 绘制图形
        return self.draw_plot()
    
    def draw_plot(self):
        """绘制时域信号图"""
        if not self.is_alive():
            return False
            
        if not self.line_in_data or not self.line_out_data:
            return False
            
        try:
            # 创建曲线
            line_in_curve = plot.PolyLine(
                list(zip(self.time_axis, self.line_in_data)),
                colour='blue',
                width=1,
                legend='Line-In'
            )
            
            line_out_curve = plot.PolyLine(
                list(zip(self.time_axis, self.line_out_data)),
                colour='red',
                width=1,
                legend='Line-Out'
            )
            
            # 创建起始标记线
            if self.start_marker is not None:
                start_line = plot.PolyLine(
                    [(self.start_marker, min(self.line_in_data)), 
                     (self.start_marker, max(self.line_in_data))],
                    colour='green',
                    width=2,
                    legend='Start'
                )
                graphics = plot.PlotGraphics([line_in_curve, line_out_curve, start_line], 
                                            "Audio Signals", "Time (s)", "Amplitude")
            else:
                graphics = plot.PlotGraphics([line_in_curve, line_out_curve], 
                                            "Audio Signals", "Time (s)", "Amplitude")
            
            # 绘制图形
            self.plotCanvas.Draw(graphics, xAxis=(0, max(self.time_axis)))
            return True
        except Exception as e:
            print(f"绘图错误: {e}")
            return False

class DualChannelRecorderGUI(wx.Frame):
    """主界面"""
    def __init__(self):
        super(DualChannelRecorderGUI, self).__init__(
            None, title="双通道音频录制工具", size=(650, 450))
        
        self.p = pyaudio.PyAudio()
        self.is_recording = False
        self.frames = []
        self.line_in_data = []
        self.line_out_data = []
        self.sample_rate = 44100
        self.channels = 2
        self.audio_start_time = None
        self.first_audio_time = None
        
        # 初始化UI
        self.init_ui()
        
        # 音频绘图窗口
        self.plot_window = None
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def init_ui(self):
        """初始化用户界面"""
        panel = wx.Panel(self)
        
        # 创建控件
        self.create_controls(panel)
        
        # 设置布局
        self.setup_layout(panel)
        
        # 绑定事件
        self.bind_events()
        
        # 初始状态
        self.stop_btn.Disable()
        self.plot_btn.Disable()
        self.save_btn.Disable()
        
        # 更新设备列表
        self.update_device_lists()
    
    def create_controls(self, panel):
        """创建界面控件"""
        # 设备选择
        self.input_device_label = wx.StaticText(panel, label="输入设备:")
        self.input_device_choice = wx.Choice(panel, choices=[])
        
        self.output_device_label = wx.StaticText(panel, label="输出设备:")
        self.output_device_choice = wx.Choice(panel, choices=[])
        
        self.refresh_devices_btn = wx.Button(panel, label="刷新设备列表")
        
        # 录制控制
        self.duration_label = wx.StaticText(panel, label="录制时长(秒):")
        self.duration_ctrl = wx.SpinCtrl(panel, value="10", min=1, max=600)
        
        self.record_btn = wx.Button(panel, label="开始录制")
        self.stop_btn = wx.Button(panel, label="停止录制")
        self.plot_btn = wx.Button(panel, label="显示波形图")
        self.save_btn = wx.Button(panel, label="保存录音")
        
        # 状态信息
        self.recording_status = wx.StaticText(panel, label="状态: 准备就绪")
        self.first_audio_label = wx.StaticText(panel, label="首次检测到音频时间: 未检测到")
        
        # 设备信息显示
        self.device_info = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY, 
                                     size=(600, 100))
    
    def setup_layout(self, panel):
        """设置界面布局"""
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 设备选择区域
        device_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "音频设备选择")
        device_grid = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
        device_grid.AddGrowableCol(1)
        
        device_grid.Add(self.input_device_label, 0, wx.ALIGN_CENTER_VERTICAL)
        device_grid.Add(self.input_device_choice, 1, wx.EXPAND)
        device_grid.Add(self.refresh_devices_btn, 0, wx.EXPAND)
        
        device_grid.Add(self.output_device_label, 0, wx.ALIGN_CENTER_VERTICAL)
        device_grid.Add(self.output_device_choice, 1, wx.EXPAND)
        device_grid.Add((0, 0))  # 空占位
        
        device_box.Add(device_grid, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(device_box, 0, wx.EXPAND|wx.ALL, 5)
        
        # 录制控制区域
        control_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "录制控制")
        control_grid = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
        control_grid.AddGrowableCol(1)
        
        control_grid.Add(self.duration_label, 0, wx.ALIGN_CENTER_VERTICAL)
        control_grid.Add(self.duration_ctrl, 0, wx.EXPAND)
        control_grid.Add(self.record_btn, 0, wx.EXPAND)
        control_grid.Add(self.stop_btn, 0, wx.EXPAND)
        
        control_grid.Add((0, 0))  # 空占位
        control_grid.Add((0, 0))  # 空占位
        control_grid.Add(self.plot_btn, 0, wx.EXPAND)
        control_grid.Add(self.save_btn, 0, wx.EXPAND)
        
        control_box.Add(control_grid, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(control_box, 0, wx.EXPAND|wx.ALL, 5)
        
        # 状态信息区域
        status_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "状态信息")
        status_box.Add(self.recording_status, 0, wx.EXPAND|wx.ALL, 5)
        status_box.Add(self.first_audio_label, 0, wx.EXPAND|wx.ALL, 5)
        vbox.Add(status_box, 0, wx.EXPAND|wx.ALL, 5)
        
        # 设备详细信息
        info_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "设备详细信息")
        info_box.Add(self.device_info, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(info_box, 1, wx.EXPAND|wx.ALL, 5)
        
        panel.SetSizer(vbox)
    
    def bind_events(self):
        """绑定事件处理"""
        self.record_btn.Bind(wx.EVT_BUTTON, self.on_record)
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        self.refresh_devices_btn.Bind(wx.EVT_BUTTON, self.update_device_lists)
    
    def update_device_lists(self, event=None):
        """更新设备下拉列表"""
        input_devices = []
        output_devices = []
        device_info = "可用音频设备:\n"
        
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            device_info += f"{i}: {dev['name']} (输入: {dev['maxInputChannels']}, 输出: {dev['maxOutputChannels']})\n"
            
            if dev['maxInputChannels'] > 0:
                input_devices.append(f"{i}: {dev['name']}")
            if dev['maxOutputChannels'] > 0:
                output_devices.append(f"{i}: {dev['name']}")
        
        # 更新下拉菜单
        self.input_device_choice.SetItems(input_devices)
        self.output_device_choice.SetItems(output_devices)
        
        # 默认选择第一个设备
        if input_devices and self.input_device_choice.GetSelection() == wx.NOT_FOUND:
            self.input_device_choice.SetSelection(0)
        if output_devices and self.output_device_choice.GetSelection() == wx.NOT_FOUND:
            self.output_device_choice.SetSelection(0)
        
        # 更新设备信息显示
        self.device_info.SetValue(device_info)
    
    def get_selected_device_index(self, choice):
        """从选择控件中获取设备索引"""
        selection = choice.GetStringSelection()
        if not selection:
            return None
        return int(selection.split(":")[0])
    
    def on_record(self, event):
        """开始录制"""
        if self.is_recording:
            return
            
        # 获取选择的设备
        input_index = self.get_selected_device_index(self.input_device_choice)
        output_index = self.get_selected_device_index(self.output_device_choice)
        
        # 重置数据
        self.frames = []
        self.line_in_data = []
        self.line_out_data = []
        self.first_audio_time = None
        self.audio_start_time = time.time()
        
        # 更新UI
        self.recording_status.SetLabel("状态: 正在录制...")
        self.first_audio_label.SetLabel("首次检测到音频时间: 未检测到")
        self.record_btn.Disable()
        self.stop_btn.Enable()
        self.plot_btn.Disable()
        self.save_btn.Disable()
        
        # 打开音频流
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self.audio_callback,
                input_device_index=input_index
            )
            
            self.is_recording = True
            
            # 启动计时线程
            duration = self.duration_ctrl.GetValue()
            self.recording_thread = Thread(target=self.record_for_duration, args=(duration,))
            self.recording_thread.start()
            
        except Exception as e:
            wx.LogError(f"无法开始录制: {str(e)}")
            self.recording_status.SetLabel("状态: 录制失败")
            self.record_btn.Enable()
            self.stop_btn.Disable()
    
    def update_device_info(self):
        """更新设备信息显示"""
        info = "Available audio devices:\n"
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            info += f"{i}: {dev['name']} (In: {dev['maxInputChannels']}, Out: {dev['maxOutputChannels']})\n"
        self.device_info.SetValue(info)
    
    def find_device_index(self, name_keyword, is_input=True):
        """查找设备索引"""
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if name_keyword.lower() in dev['name'].lower():
                if is_input and dev['maxInputChannels'] > 0:
                    return i
                elif not is_input and dev['maxOutputChannels'] > 0:
                    return i
        return None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数"""
        if self.is_recording:
            # 转换为numpy数组
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # 分离左右声道
            channels = np.reshape(audio_data, (-1, self.channels))
            line_in = channels[:, 0] if self.channels >= 1 else np.zeros(len(audio_data))
            line_out = channels[:, 1] if self.channels >= 2 else np.zeros(len(audio_data))
            
            # 检测有效音频信号
            if self.first_audio_time is None:
                if np.max(np.abs(line_in)) > 1000 or np.max(np.abs(line_out)) > 1000:  # 阈值
                    self.first_audio_time = time.time() - self.audio_start_time
                    wx.CallAfter(self.update_first_audio_label)
            
            # 存储数据
            self.frames.append(audio_data)
            self.line_in_data.extend(line_in)
            self.line_out_data.extend(line_out)
            
            return (in_data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paComplete)
    
    def update_first_audio_label(self):
        """更新首次检测到音频信号的标签"""
        if self.first_audio_time is not None:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.first_audio_label.SetLabel(
                f"First audio signal at: {self.first_audio_time:.3f} seconds (System time: {timestamp})")
    
    def on_record(self, event):
        """开始录制"""
        if self.is_recording:
            return
            
        # 重置数据
        self.frames = []
        self.line_in_data = []
        self.line_out_data = []
        self.first_audio_time = None
        self.audio_start_time = time.time()
        
        # 更新UI
        self.recording_status.SetLabel("Status: Recording...")
        self.first_audio_label.SetLabel("First audio signal at: Not detected")
        self.record_btn.Disable()
        self.stop_btn.Enable()
        self.plot_btn.Disable()
        self.save_btn.Disable()
        
        # 尝试查找line-in和line-out设备
        line_in_index = self.find_device_index("line in", is_input=True)
        line_out_index = self.find_device_index("line out", is_input=True)
        
        if line_in_index is None or line_out_index is None:
            wx.LogWarning("Could not find both line-in and line-out devices. Using default.")
            line_in_index = None
            line_out_index = None
        
        # 打开音频流
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback,
            input_device_index=line_in_index if line_in_index else None
        )
        
        self.is_recording = True
        
        # 启动计时线程
        duration = self.duration_ctrl.GetValue()
        self.recording_thread = Thread(target=self.record_for_duration, args=(duration,))
        self.recording_thread.start()
    
    def record_for_duration(self, duration):
        """录制指定时长"""
        time.sleep(duration)
        wx.CallAfter(self.on_stop, None)
    
    def on_stop(self, event):
        """停止录制"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        
        # 更新UI
        self.recording_status.SetLabel("Status: Recording stopped")
        self.record_btn.Enable()
        self.stop_btn.Disable()
        self.plot_btn.Enable()
        self.save_btn.Enable()
        
        # 更新首次音频信号时间（如果尚未检测到）
        if self.first_audio_time is None:
            self.first_audio_time = time.time() - self.audio_start_time
            wx.CallAfter(self.update_first_audio_label)
    
    def on_plot(self, event):
        """显示音频信号图"""
        if not self.line_in_data or not self.line_out_data:
            wx.LogError("No audio data to plot")
            return
        
        # 如果窗口不存在或已关闭，创建新窗口
        if not hasattr(self, 'plot_window') or not self.is_window_alive(self.plot_window):
            self.plot_window = AudioPlotWindow(self)
            self.plot_window._parent = self  # 设置父窗口引用
            
        if self.plot_window is None:
            self.plot_window = AudioPlotWindow(self)
        
        # 计算起始标记位置（相对时间）
        start_marker = self.first_audio_time if self.first_audio_time is not None else 0
        
        # 更新绘图
        self.plot_window.update_plot(
            self.line_in_data,
            self.line_out_data,
            self.sample_rate,
            start_marker
        )
        
        self.plot_window.Show()
    
    def on_close(self, event):
        """关闭窗口时清理资源"""
        # 停止录音（如果正在录制）
        if hasattr(self, 'is_recording') and self.is_recording:
            self.on_stop(None)

        # 安全关闭绘图窗口
        if hasattr(self, 'plot_window') and self.is_window_alive(self.plot_window):
            try:
                self.plot_window.Close(True)
            except:
                pass
            
        # 终止音频资源
        try:
            self.p.terminate()
        except:
            pass
        
        # 销毁主窗口
        self.Destroy()

    
    def on_save(self, event):
        """保存录音"""
        if not self.frames:
            wx.LogError("No audio data to save")
            return
            
        with wx.FileDialog(self, "Save WAV file", wildcard="WAV files (*.wav)|*.wav",
                          style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as fileDialog:
            
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
                
            pathname = fileDialog.GetPath()
            
            try:
                wf = wave.open(pathname, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                
                # 合并所有帧并写入文件
                audio_data = np.concatenate(self.frames)
                wf.writeframes(audio_data.tobytes())
                wf.close()
                
                wx.LogMessage(f"Recording saved to {pathname}")
            except Exception as e:
                wx.LogError(f"Error saving file: {str(e)}")
    
    def is_window_alive(self, window):
        """安全检查wx窗口是否仍然存在"""
        if not window:
            return False
        try:
            # 两种检查方式结合
            return (isinstance(window, wx.Window) and 
                    wx.Window.FindWindowById(window.GetId()) is not None and
                    not window.IsBeingDeleted())
        except:
            return False

        
    

if __name__ == "__main__":
    app = wx.App(False)
    frame = DualChannelRecorderGUI()
    frame.Show()
    app.MainLoop()
