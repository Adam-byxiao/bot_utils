import os
import glob
import subprocess
import wx
from threading import Thread
from wx.lib.pubsub import pub

# 复用与其它工具相同的 ffmpeg 路径
ffmpeg_path = "D:/software/ffmpeg/bin/ffmpeg.exe"


class AudioGenderSplitterApp(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="男女声拆分工具", size=(900, 650))
        self.parent = parent

        self.panel = wx.Panel(self)
        self.SetMinSize((600, 420))

        self.recent_folders = []
        self.max_recent_folders = 6
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
        self.input_choice = wx.Choice(self.panel, choices=[], size=(360, -1))
        hbox_in.Add(self.input_choice, proportion=1, flag=wx.EXPAND)
        self.browse_in_btn = wx.Button(self.panel, label="浏览...")
        self.browse_in_btn.Bind(wx.EVT_BUTTON, self.on_browse_input)
        hbox_in.Add(self.browse_in_btn, flag=wx.LEFT, border=6)
        self.use_cwd_chk = wx.CheckBox(self.panel, label="使用当前工作目录")
        self.use_cwd_chk.SetValue(True)
        self.use_cwd_chk.Bind(wx.EVT_CHECKBOX, self.on_use_cwd)
        hbox_in.Add(self.use_cwd_chk, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=12)
        io_sizer.Add(hbox_in, flag=wx.EXPAND|wx.ALL, border=6)

        # 男声输出文件夹
        hbox_male = wx.BoxSizer(wx.HORIZONTAL)
        hbox_male.Add(wx.StaticText(self.panel, label="男声输出文件夹:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.male_choice = wx.Choice(self.panel, choices=[], size=(360, -1))
        hbox_male.Add(self.male_choice, proportion=1, flag=wx.EXPAND)
        self.browse_male_btn = wx.Button(self.panel, label="浏览...")
        self.browse_male_btn.Bind(wx.EVT_BUTTON, self.on_browse_male)
        hbox_male.Add(self.browse_male_btn, flag=wx.LEFT, border=6)
        io_sizer.Add(hbox_male, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=6)

        # 女声输出文件夹
        hbox_female = wx.BoxSizer(wx.HORIZONTAL)
        hbox_female.Add(wx.StaticText(self.panel, label="女声输出文件夹:"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=8)
        self.female_choice = wx.Choice(self.panel, choices=[], size=(360, -1))
        hbox_female.Add(self.female_choice, proportion=1, flag=wx.EXPAND)
        self.browse_female_btn = wx.Button(self.panel, label="浏览...")
        self.browse_female_btn.Bind(wx.EVT_BUTTON, self.on_browse_female)
        hbox_female.Add(self.browse_female_btn, flag=wx.LEFT, border=6)
        io_sizer.Add(hbox_female, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=6)

        vbox.Add(io_sizer, flag=wx.EXPAND|wx.ALL, border=10)

        # 参数设置
        param_box = wx.StaticBox(self.panel, label="拆分参数")
        param_sizer = wx.StaticBoxSizer(param_box, wx.HORIZONTAL)

        # 固定拆分时间显示（9.8秒）
        param_sizer.Add(wx.StaticText(self.panel, label="拆分时间点(秒):"), flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=6)
        self.split_time_text = wx.TextCtrl(self.panel, value="9.8", style=wx.TE_READONLY, size=(80, -1))
        param_sizer.Add(self.split_time_text, flag=wx.RIGHT, border=20)

        # 递归与覆盖选项
        self.recursive_chk = wx.CheckBox(self.panel, label="递归处理子文件夹")
        self.recursive_chk.SetValue(True)
        param_sizer.Add(self.recursive_chk, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=12)

        self.overwrite_chk = wx.CheckBox(self.panel, label="覆盖同名输出文件")
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
            ("M4A", "*.m4a"),
        ]
        self.filter_choice = wx.Choice(self.panel, choices=[t[0] for t in self.file_types])
        self.filter_choice.SetSelection(0)
        filter_sizer.Add(self.filter_choice, proportion=1, flag=wx.EXPAND)
        vbox.Add(filter_sizer, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        # 操作按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self.panel, label="开始拆分")
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
        cwd = os.getcwd()
        self.add_recent_folder(cwd)
        self.input_choice.SetSelection(0)
        self.male_choice.SetSelection(0)
        self.female_choice.SetSelection(0)

    def on_use_cwd(self, event):
        if self.use_cwd_chk.GetValue():
            cwd = os.getcwd()
            self.add_recent_folder(cwd)
            self.input_choice.SetStringSelection(cwd)

    def on_browse_input(self, event):
        with wx.DirDialog(self, "选择输入文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder)
                self.input_choice.SetStringSelection(folder)

    def on_browse_male(self, event):
        with wx.DirDialog(self, "选择男声输出文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder)
                self.male_choice.SetStringSelection(folder)

    def on_browse_female(self, event):
        with wx.DirDialog(self, "选择女声输出文件夹") as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                self.add_recent_folder(folder)
                self.female_choice.SetStringSelection(folder)

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
        self.male_choice.Clear()
        self.female_choice.Clear()
        for folder in self.recent_folders:
            self.input_choice.Append(folder)
            self.male_choice.Append(folder)
            self.female_choice.Append(folder)
        if self.recent_folders:
            self.input_choice.SetSelection(0)
            self.male_choice.SetSelection(0)
            self.female_choice.SetSelection(0)

    def fix_path(self, path):
        path = path.replace('\\\\', '\\')
        return os.path.normpath(path)

    def append_log(self, message):
        wx.CallAfter(self.log_text.AppendText, message + "\n")
        wx.CallAfter(self.log_text.ShowPosition, self.log_text.GetLastPosition())

    def update_progress(self, value):
        wx.CallAfter(self.gauge.SetValue, value)

    def on_start(self, event):
        input_folder = self.input_choice.GetStringSelection()
        male_folder = self.male_choice.GetStringSelection()
        female_folder = self.female_choice.GetStringSelection()

        if not input_folder or not os.path.isdir(input_folder):
            wx.MessageBox("请选择有效的输入文件夹", "错误", wx.OK | wx.ICON_ERROR)
            return
        if not male_folder:
            wx.MessageBox("请选择男声输出文件夹", "错误", wx.OK | wx.ICON_ERROR)
            return
        if not female_folder:
            wx.MessageBox("请选择女声输出文件夹", "错误", wx.OK | wx.ICON_ERROR)
            return

        try:
            # 固定拆分时间 9.8 秒
            split_time = 9.8
            recursive = self.recursive_chk.GetValue()
            overwrite = self.overwrite_chk.GetValue()

            if not os.path.exists(ffmpeg_path):
                wx.MessageBox("未找到 ffmpeg，请检查路径配置", "错误", wx.OK | wx.ICON_ERROR)
                return

            os.makedirs(male_folder, exist_ok=True)
            os.makedirs(female_folder, exist_ok=True)

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
            self.append_log(f"开始拆分: 输入={input_folder} 男声输出={male_folder} 女声输出={female_folder} 拆分时间=9.8秒")

            # 启动后台线程
            self.worker = AudioGenderSplitWorker(audio_files, male_folder, female_folder, split_time, overwrite)
            self.worker.start()

        except Exception as e:
            wx.MessageBox(f"参数错误: {e}", "错误", wx.OK | wx.ICON_ERROR)

    def on_worker_finished(self):
        self.start_btn.Enable()
        self.cancel_btn.Disable()
        pub.sendMessage("task_finished", task_name="男女声拆分处理")


class AudioGenderSplitWorker(Thread):
    def __init__(self, audio_files, male_folder, female_folder, split_time, overwrite=False):
        super().__init__()
        self.audio_files = audio_files
        self.male_folder = male_folder
        self.female_folder = female_folder
        self.split_time = split_time
        self.overwrite = overwrite
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.audio_files)
        for idx, src in enumerate(self.audio_files, start=1):
            if self._stop:
                break

            base = os.path.basename(src)
            name, ext = os.path.splitext(base)

            male_dst = os.path.join(self.male_folder, f"{name}_male{ext}")
            female_dst = os.path.join(self.female_folder, f"{name}_female{ext}")

            # 构造 ffmpeg 命令：男声 0-9.8s
            ff_overwrite_flag = "-y" if self.overwrite else "-n"
            cmd_male = [
                ffmpeg_path,
                ff_overwrite_flag,
                "-i", src,
                "-t", str(self.split_time),
                "-vn",
                "-acodec", "copy",
                male_dst,
            ]

            # 女声 9.8s 到结尾
            cmd_female = [
                ffmpeg_path,
                ff_overwrite_flag,
                "-i", src,
                "-ss", str(self.split_time),
                "-vn",
                "-acodec", "copy",
                female_dst,
            ]

            try:
                if not self.overwrite and os.path.exists(male_dst):
                    pub.sendMessage("log", message=f"[{idx}/{total}] 跳过男声(文件已存在): {male_dst}")
                else:
                    pub.sendMessage("log", message=f"[{idx}/{total}] 男声: {src} -> {male_dst}")
                    subprocess.run(cmd_male, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                # 回退到 WAV 重编码
                male_dst = os.path.join(self.male_folder, f"{name}_male.wav")
                fallback_male = [ffmpeg_path, "-y", "-i", src, "-t", str(self.split_time), "-vn", "-c:a", "pcm_s16le", male_dst]
                pub.sendMessage("log", message=f"⚠️ 男声音频复制失败，回退重编码到 WAV: {male_dst}")
                try:
                    subprocess.run(fallback_male, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as e2:
                    pub.sendMessage("log", message=f"❌ 男声处理失败: {src} - {e2}")

            try:
                if not self.overwrite and os.path.exists(female_dst):
                    pub.sendMessage("log", message=f"[{idx}/{total}] 跳过女声(文件已存在): {female_dst}")
                else:
                    pub.sendMessage("log", message=f"[{idx}/{total}] 女声: {src} -> {female_dst}")
                    subprocess.run(cmd_female, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                # 回退到 WAV 重编码
                female_dst = os.path.join(self.female_folder, f"{name}_female.wav")
                fallback_female = [ffmpeg_path, "-y", "-i", src, "-ss", str(self.split_time), "-vn", "-c:a", "pcm_s16le", female_dst]
                pub.sendMessage("log", message=f"⚠️ 女声音频复制失败，回退重编码到 WAV: {female_dst}")
                try:
                    subprocess.run(fallback_female, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as e2:
                    pub.sendMessage("log", message=f"❌ 女声处理失败: {src} - {e2}")

            progress = int(idx / total * 100)
            pub.sendMessage("progress", value=progress)

        pub.sendMessage("log", message="✅ 男女声拆分完成")
        pub.sendMessage("worker_finished")


if __name__ == "__main__":
    app = wx.App(False)
    frame = AudioGenderSplitterApp()
    app.MainLoop()