import os
import subprocess
import wx
from wx.lib.pubsub import pub

ffmpeg_path = "D:/software/ffmpeg/bin/ffmpeg.exe"


class AudioConverterApp(wx.Frame):
    def __init__(self, parent=None):  # 添加parent参数
        super().__init__(parent, title="MP4 转 WAV 转换器", size=(800, 600))
        self.parent = parent  # 保存主窗口引用
        
        self.panel = wx.Panel(self)
        self.SetMinSize((400, 250))
        
        # 初始化界面
        self.init_ui()
        
        # 存储最近使用的文件夹
        self.recent_folders = []
        self.max_recent_folders = 5
        
    def init_ui(self):
        # 创建垂直布局
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 输入文件夹选择
        input_box = wx.StaticBox(self.panel, label="输入设置")
        input_sizer = wx.StaticBoxSizer(input_box, wx.VERTICAL)
        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.input_label = wx.StaticText(self.panel, label="输入文件夹:")
        hbox1.Add(self.input_label, flag=wx.RIGHT, border=8)
        
        self.input_choice = wx.Choice(self.panel, choices=[])
        hbox1.Add(self.input_choice, proportion=1, flag=wx.EXPAND)
        
        self.browse_btn = wx.Button(self.panel, label="浏览...")
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_input)
        hbox1.Add(self.browse_btn, flag=wx.LEFT, border=5)
        
        input_sizer.Add(hbox1, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 输出文件夹选择
        output_box = wx.StaticBox(self.panel, label="输出设置")
        output_sizer = wx.StaticBoxSizer(output_box, wx.VERTICAL)
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.output_label = wx.StaticText(self.panel, label="输出文件夹:")
        hbox2.Add(self.output_label, flag=wx.RIGHT, border=8)
        
        self.output_choice = wx.Choice(self.panel, choices=[])
        hbox2.Add(self.output_choice, proportion=1, flag=wx.EXPAND)
        
        self.browse_out_btn = wx.Button(self.panel, label="浏览...")
        self.browse_out_btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        hbox2.Add(self.browse_out_btn, flag=wx.LEFT, border=5)
        
        output_sizer.Add(hbox2, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 音频参数设置
        param_box = wx.StaticBox(self.panel, label="音频参数")
        param_sizer = wx.StaticBoxSizer(param_box, wx.HORIZONTAL)
        
        self.sample_rate_label = wx.StaticText(self.panel, label="采样率:")
        param_sizer.Add(self.sample_rate_label, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=5)
        
        self.sample_rate = wx.ComboBox(self.panel, choices=["44100", "48000", "22050", "16000"], value="44100")
        param_sizer.Add(self.sample_rate, flag=wx.RIGHT, border=15)
        
        self.channels_label = wx.StaticText(self.panel, label="声道数:")
        param_sizer.Add(self.channels_label, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=5)
        
        self.channels = wx.ComboBox(self.panel, choices=["1 (单声道)", "2 (立体声)"], value="2 (立体声)")
        param_sizer.Add(self.channels)
        
        # 转换按钮
        self.convert_btn = wx.Button(self.panel, label="开始转换")
        self.convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)
        
        # 日志输出
        self.log = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        
        # 添加到主布局
        vbox.Add(input_sizer, flag=wx.EXPAND|wx.ALL, border=10)
        vbox.Add(output_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(param_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        vbox.Add(self.convert_btn, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=10)
        vbox.Add(self.log, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        self.panel.SetSizer(vbox)
        
        # 初始化最近文件夹
        self.load_recent_folders()
        
    def on_browse_input(self, event):
        with wx.DirDialog(self, "选择输入文件夹", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder, is_input=True)
    
    def on_browse_output(self, event):
        with wx.DirDialog(self, "选择输出文件夹", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder, is_input=False)
    
    def add_recent_folder(self, folder, is_input=True):
        """添加最近使用的文件夹到列表"""
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        
        # 限制最大数量
        if len(self.recent_folders) > self.max_recent_folders:
            self.recent_folders = self.recent_folders[:self.max_recent_folders]
        
        # 更新下拉菜单
        self.update_folder_choices()
        
        # 设置当前选择的文件夹
        if is_input:
            self.input_choice.SetStringSelection(folder)
        else:
            self.output_choice.SetStringSelection(folder)
        
        # 保存到配置文件
        self.save_recent_folders()
    
    def update_folder_choices(self):
        """更新下拉菜单选项"""
        self.input_choice.Clear()
        self.output_choice.Clear()
        
        for folder in self.recent_folders:
            self.input_choice.Append(folder)
            self.output_choice.Append(folder)
        
        if self.recent_folders:
            self.input_choice.SetSelection(0)
            self.output_choice.SetSelection(0)
    
    def load_recent_folders(self):
        """从配置文件加载最近使用的文件夹"""
        # 这里简单实现，实际应用中可以使用配置文件或注册表
        self.recent_folders = []
        self.update_folder_choices()
    
    def save_recent_folders(self):
        """保存最近使用的文件夹到配置文件"""
        # 这里简单实现，实际应用中可以使用配置文件或注册表
        pass
    
    def on_convert(self, event):
        """执行转换操作"""
        input_folder = self.input_choice.GetStringSelection()
        output_folder = self.output_choice.GetStringSelection()
        
        if not input_folder:
            wx.MessageBox("请选择输入文件夹", "错误", wx.OK|wx.ICON_ERROR)
            return
        
        if not output_folder:
            output_folder = input_folder
        
        try:
            sample_rate = int(self.sample_rate.GetValue())
            channels = int(self.channels.GetValue()[0])
            
            self.log.AppendText(f"开始转换: {input_folder} -> {output_folder}\n")
            
            # 确保路径格式正确
            input_folder = self.fix_path(input_folder)
            output_folder = self.fix_path(output_folder)
            
            self.convert_mp4_to_wav(input_folder, output_folder, sample_rate, channels)
            self.log.AppendText("转换完成!\n\n")
            #wx.MessageBox("转换完成!", "完成", wx.OK|wx.ICON_INFORMATION)
            if self.parent:
                pub.sendMessage("task_finished", task_name="视频转音频处理") # 只发送完成信号
        except Exception as e:
            self.log.AppendText(f"错误: {str(e)}\n")
            wx.MessageBox(f"转换出错: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)
    
    def fix_path(self, path):
        """修正路径格式，确保能被系统命令识别"""
        # 替换双斜杠为单斜杠
        # 替换所有双斜杠为单斜杠
        path = path.replace('\\\\', '\\')
        # 处理混合斜杠情况（Windows也接受正斜杠）
        path = path.replace('/', '\\')
        # 规范化路径（处理相对路径、冗余分隔符等）
        path = os.path.normpath(path)
        return path

    
    def convert_mp4_to_wav(self, input_folder, output_folder=None, sample_rate=44100, channels=2):
        """实际的转换函数"""
        if output_folder is None:
            output_folder = input_folder
        else:
            os.makedirs(output_folder, exist_ok=True)
            # 获取文件列表

        # 获取所有支持的输入文件（MP4 和 M4A）
        supported_extensions = ('.mp4', '.m4a')
        input_files = [f for f in os.listdir(input_folder) 
                      if f.lower().endswith(supported_extensions)]
        total_files = len(input_files)

        if total_files == 0:
            message = "未找到支持的音频/视频文件(支持 .mp4 和 .m4a)"
            self.log.AppendText(message + "\n")
            if self.parent:
                pub.sendMessage("output", message=message)
            return

        message = f"开始处理 {total_files} 个文件（MP4/M4A）..."
        self.log.AppendText(message + "\n")
        if self.parent:
            pub.sendMessage("output", message=message)
        
        for i, filename in enumerate(input_files):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + '.wav'
            output_path = os.path.join(output_folder, output_filename)

            # 修正路径格式
            inputpath = self.fix_path(input_path)
            outputpath = self.fix_path(output_path)

            # 构建 FFmpeg 命令（兼容 MP4 和 M4A）
            command = [
                ffmpeg_path,
                '-i', inputpath,
                '-vn',              # 禁用视频流
                '-acodec', 'pcm_s16le',  # WAV 编码
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-y',               # 覆盖输出文件
                outputpath
            ]

            try:
                message = f"正在处理文件 {i+1}/{total_files}: {filename}"
                self.log.AppendText(message + "\n")
                if self.parent:
                    pub.sendMessage("output", message=message)

                # 执行命令
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'  # 处理编码问题
                )

                if process.returncode == 0:
                    message = f"转换成功: {output_filename}"
                else:
                    message = f"转换失败: {filename} (错误: {process.stderr.strip()})"

                self.log.AppendText(message + "\n")
                if self.parent:
                    pub.sendMessage("output", message=message)

                # 更新进度
                progress = int((i + 1) / total_files * 100)
                if self.parent:
                    pub.sendMessage("progress", value=progress)

            except Exception as e:
                message = f"处理文件 {filename} 时发生错误: {str(e)}"
                self.log.AppendText(message + "\n")
                if self.parent:
                    pub.sendMessage("output", message=message)

        # 完成处理
        message = "所有文件处理完成!"
        self.log.AppendText(message + "\n")
        if self.parent:
            pub.sendMessage("output", message=message)
            pub.sendMessage("worker_finished")

if __name__ == "__main__":
    app = wx.App(False)
    frame = AudioConverterApp()
    frame.Show()
    app.MainLoop()