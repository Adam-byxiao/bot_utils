import os
import glob
import subprocess
import wx
from threading import Thread
from wx.lib.pubsub import pub

# 与现有 Video2Audio 工具保持一致的 ffmpeg 路径配置
ffmpeg_path = "D:/software/ffmpeg/bin/ffmpeg.exe"


class AudioResamplerApp(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="音频采样率批量转换工具", size=(900, 650))
        self.parent = parent

        self.panel = wx.Panel(self)
        self.SetMinSize((600, 420))

        self.recent_folders = []
        self.max_recent_folders = 5

        self.worker = None

        pub.subscribe(self.append_log, "log")
        pub.subscribe(self.update_progress, "progress")
        pub.subscribe(self.on_worker_finished, "worker_finished")

        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 输入输出设置
        io_box = wx.StaticBox(self.panel, label="输入/输出设置")
        io_sizer = wx.StaticBoxSizer(io_box, wx.VERTICAL)

        # 输入文件夹
        hbox_in = wx.BoxSizer(wx.HORIZONTAL)
        hbox_in.Add(wx.StaticText(self.panel, label="输入文件夹:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.input_choice = wx.Choice(self.panel, choices=[], size=(420, -1))
        hbox_in.Add(self.input_choice, proportion=1, flag=wx.EXPAND)
        self.browse_in_btn = wx.Button(self.panel, label="浏览...")
        self.browse_in_btn.Bind(wx.EVT_BUTTON, self.on_browse_input)
        hbox_in.Add(self.browse_in_btn, flag=wx.LEFT, border=6)
        self.use_cwd_chk = wx.CheckBox(self.panel, label="使用当前工作目录")
        self.use_cwd_chk.SetValue(True)
        self.use_cwd_chk.Bind(wx.EVT_CHECKBOX, self.on_use_cwd)
        hbox_in.Add(self.use_cwd_chk, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=12)
        io_sizer.Add(hbox_in, flag=wx.EXPAND|wx.ALL, border=6)

        # 输出文件夹
        hbox_out = wx.BoxSizer(wx.HORIZONTAL)
        hbox_out.Add(wx.StaticText(self.panel, label="输出文件夹:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.output_choice = wx.Choice(self.panel, choices=[], size=(420, -1))
        hbox_out.Add(self.output_choice, proportion=1, flag=wx.EXPAND)
        self.browse_out_btn = wx.Button(self.panel, label="浏览...")
        self.browse_out_btn.Bind(wx.EVT_BUTTON, self.on_browse_output)
        hbox_out.Add(self.browse_out_btn, flag=wx.LEFT, border=6)
        self.same_as_input_chk = wx.CheckBox(self.panel, label="与输入相同 (默认)")
        self.same_as_input_chk.SetValue(True)
        self.same_as_input_chk.Bind(wx.EVT_CHECKBOX, self.on_same_as_input)
        hbox_out.Add(self.same_as_input_chk, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=12)
        io_sizer.Add(hbox_out, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=6)

        vbox.Add(io_sizer, flag=wx.EXPAND|wx.ALL, border=10)

        # 参数设置
        param_box = wx.StaticBox(self.panel, label="转换参数")
        param_sizer = wx.StaticBoxSizer(param_box, wx.HORIZONTAL)

        # 采样率
        param_sizer.Add(wx.StaticText(self.panel, label="目标采样率:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=6)
        self.sample_rate_cb = wx.ComboBox(self.panel, choices=[
            "48000", "44100", "32000", "22050", "16000", "11025", "8000"
        ], value="44100", style=wx.CB_READONLY)
        param_sizer.Add(self.sample_rate_cb, flag=wx.RIGHT, border=12)

        # 声道数
        param_sizer.Add(wx.StaticText(self.panel, label="声道数:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=6)
        self.channels_cb = wx.ComboBox(self.panel, choices=[
            "保持不变", "1 (单声道)", "2 (立体声)"
        ], value="保持不变", style=wx.CB_READONLY)
        param_sizer.Add(self.channels_cb, flag=wx.RIGHT, border=12)

        # 递归、覆盖
        self.recursive_chk = wx.CheckBox(self.panel, label="递归处理子文件夹")
        self.recursive_chk.SetValue(True)
        param_sizer.Add(self.recursive_chk, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=12)

        self.overwrite_chk = wx.CheckBox(self.panel, label="覆盖原文件")
        self.overwrite_chk.SetValue(False)
        param_sizer.Add(self.overwrite_chk, flag=wx.ALIGN_CENTER_VERTICAL)

        vbox.Add(param_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 文件类型筛选
        filter_box = wx.StaticBox(self.panel, label="文件类型筛选")
        filter_sizer = wx.StaticBoxSizer(filter_box, wx.HORIZONTAL)
        self.file_types = [
            ("所有音频", "*.wav;*.mp3;*.flac;*.aiff;*.ogg;*.m4a"),
            ("WAV", "*.wav"),
            ("MP3", "*.mp3"),
            ("FLAC", "*.flac"),
            ("AIFF", "*.aiff"),
            ("OGG", "*.ogg"),
        ]
        self.filter_choice = wx.Choice(self.panel, choices=[t[0] for t in self.file_types])
        self.filter_choice.SetSelection(0)
        filter_sizer.Add(self.filter_choice, proportion=1, flag=wx.EXPAND)
        vbox.Add(filter_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self.panel, label="开始转换")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.cancel_btn = wx.Button(self.panel, label="取消")
        self.cancel_btn.Disable()
        btn_sizer.Add(self.start_btn, proportion=1, flag=wx.EXPAND|wx.RIGHT, border=6)
        btn_sizer.Add(self.cancel_btn, proportion=1, flag=wx.EXPAND)
        vbox.Add(btn_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 日志与进度
        log_box = wx.StaticBox(self.panel, label="处理日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        log_sizer.Add(self.log_text, proportion=1, flag=wx.EXPAND)
        vbox.Add(log_sizer, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        self.gauge = wx.Gauge(self.panel, range=100)
        vbox.Add(self.gauge, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        self.panel.SetSizer(vbox)

        # 初始化目录为当前工作目录
        self.add_recent_folder(os.getcwd())
        self.input_choice.SetSelection(0)
        self.output_choice.SetSelection(0)

    def on_use_cwd(self, event):
        if self.use_cwd_chk.GetValue():
            cwd = os.getcwd()
            self.add_recent_folder(cwd)
            self.input_choice.SetStringSelection(cwd)
            if self.same_as_input_chk.GetValue():
                self.output_choice.SetStringSelection(cwd)

    def on_same_as_input(self, event):
        if self.same_as_input_chk.GetValue():
            sel = self.input_choice.GetStringSelection()
            if sel:
                self.output_choice.SetStringSelection(sel)

    def on_browse_input(self, event):
        with wx.DirDialog(self, "选择输入文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder)
                self.input_choice.SetStringSelection(folder)
                if self.same_as_input_chk.GetValue():
                    self.output_choice.SetStringSelection(folder)

    def on_browse_output(self, event):
        with wx.DirDialog(self, "选择输出文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder)
                self.output_choice.SetStringSelection(folder)

    def add_recent_folder(self, folder):
        folder = self.fix_path(folder)
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        if len(self.recent_folders) > self.max_recent_folders:
            self.recent_folders = self.recent_folders[:self.max_recent_folders]
        self.update_folder_choices()

    def update_folder_choices(self):
        self.input_choice.Clear()
        self.output_choice.Clear()
        for folder in self.recent_folders:
            self.input_choice.Append(folder)
            self.output_choice.Append(folder)
        if self.recent_folders:
            self.input_choice.SetSelection(0)
            self.output_choice.SetSelection(0)

    def fix_path(self, path):
        path = path.replace('\\\\', '\\')
        path = os.path.normpath(path)
        return path

    def append_log(self, message):
        wx.CallAfter(self.log_text.AppendText, message + "\n")
        wx.CallAfter(self.log_text.ShowPosition, self.log_text.GetLastPosition())

    def update_progress(self, value):
        wx.CallAfter(self.gauge.SetValue, value)

    def on_start(self, event):
        input_folder = self.input_choice.GetStringSelection()
        output_folder = self.output_choice.GetStringSelection() if not self.same_as_input_chk.GetValue() else input_folder

        if not input_folder or not os.path.isdir(input_folder):
            wx.MessageBox("请选择有效的输入文件夹", "错误", wx.OK | wx.ICON_ERROR)
            return

        if not output_folder:
            output_folder = input_folder

        try:
            sample_rate = int(self.sample_rate_cb.GetValue())
            channels_sel = self.channels_cb.GetValue()
            channels = None
            if channels_sel.startswith("1"):
                channels = 1
            elif channels_sel.startswith("2"):
                channels = 2

            recursive = self.recursive_chk.GetValue()
            overwrite = self.overwrite_chk.GetValue()

            # 参数校验
            if not os.path.exists(ffmpeg_path):
                wx.MessageBox("未找到 ffmpeg，请检查路径配置", "错误", wx.OK | wx.ICON_ERROR)
                return

            os.makedirs(output_folder, exist_ok=True)

            # 获取音频文件列表
            ext_index = self.filter_choice.GetSelection()
            extensions = self.file_types[ext_index][1].split(";")
            audio_files = []
            if recursive:
                for ext in extensions:
                    audio_files.extend(glob.glob(os.path.join(input_folder, "**", ext), recursive=True))
            else:
                for ext in extensions:
                    audio_files.extend(glob.glob(os.path.join(input_folder, ext)))

            if not audio_files:
                wx.MessageBox("未在输入文件夹中找到匹配的音频文件", "提示", wx.OK | wx.ICON_INFORMATION)
                return

            self.start_btn.Disable()
            self.cancel_btn.Enable()
            self.gauge.SetValue(0)
            self.log_text.Clear()
            self.append_log(f"开始采样率转换: 输入={input_folder} 输出={output_folder} 目标采样率={sample_rate}")

            # 启动后台线程
            self.worker = AudioResampleWorker(audio_files, output_folder, sample_rate, channels, overwrite)
            self.worker.start()

        except Exception as e:
            wx.MessageBox(f"参数错误: {e}", "错误", wx.OK | wx.ICON_ERROR)

    def on_worker_finished(self):
        self.start_btn.Enable()
        self.cancel_btn.Disable()
        pub.sendMessage("task_finished", task_name="音频采样率转换")


class AudioResampleWorker(Thread):
    def __init__(self, audio_files, output_folder, sample_rate, channels=None, overwrite=False):
        super().__init__()
        self.audio_files = audio_files
        self.output_folder = output_folder
        self.sample_rate = sample_rate
        self.channels = channels
        self.overwrite = overwrite
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.audio_files)
        for idx, src in enumerate(self.audio_files, start=1):
            if self._stop:
                break

            try:
                rel_path = os.path.relpath(src, start=os.path.commonpath([self.audio_files[0], src])) if os.path.isabs(src) else os.path.basename(src)
            except Exception:
                rel_path = os.path.basename(src)

            base_name = os.path.basename(src)
            name, ext = os.path.splitext(base_name)
            if self.overwrite:
                dst = os.path.join(self.output_folder, f"{name}{ext}")
            else:
                dst = os.path.join(self.output_folder, f"{name}_sr{self.sample_rate}{ext}")

            # ffmpeg 命令
            cmd = [
                ffmpeg_path,
                "-y",  # 覆盖目标文件
                "-i", src,
                "-ar", str(self.sample_rate),
            ]
            if self.channels is not None:
                cmd += ["-ac", str(self.channels)]
            cmd += [dst]

            try:
                pub.sendMessage("log", message=f"[{idx}/{total}] 转换: {src} -> {dst}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                pub.sendMessage("log", message=f"❌ ffmpeg 错误: {e}")
            except Exception as e:
                pub.sendMessage("log", message=f"❌ 处理失败: {src} - {e}")

            progress = int(idx / total * 100)
            pub.sendMessage("progress", value=progress)

        pub.sendMessage("log", message="✅ 采样率转换完成")
        pub.sendMessage("worker_finished")


if __name__ == "__main__":
    app = wx.App(False)
    frame = AudioResamplerApp()
    app.MainLoop()