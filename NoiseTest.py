import os
import wx
import camera_script.CheckNoise as CheckNoise 
import camera_script.ColorNoise as ColorNoise 

class ImageFileBrowser(wx.Frame):
    def __init__(self):
        super().__init__(None, title="图像测试工具", size=(800, 700))  # 增大窗口尺寸
        self.image_files = []  # 存储完整路径
        self.selected_method = "随机噪声"
        self.current_folder = ""
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        
        # 主垂直布局
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 第一区域：文件选择
        file_box = wx.StaticBox(panel, label="文件选择")
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)
        
        # 文件夹选择行
        folder_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_open = wx.Button(panel, label="选择图像文件夹...")
        self.btn_open.Bind(wx.EVT_BUTTON, self.on_open_folder)
        folder_sizer.Add(self.btn_open, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        file_sizer.Add(folder_sizer, flag=wx.EXPAND)
        
        # 文件列表显示
        self.file_list = wx.ListBox(panel, style=wx.LB_EXTENDED)
        file_sizer.Add(self.file_list, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        
        main_sizer.Add(file_sizer, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        
        # 第二区域：测试设置
        test_box = wx.StaticBox(panel, label="测试设置")
        test_sizer = wx.StaticBoxSizer(test_box, wx.VERTICAL)
        
        # 测试方法选择行
        method_sizer = wx.BoxSizer(wx.HORIZONTAL)
        method_sizer.Add(wx.StaticText(panel, label="测试方法:"), 
                      flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, border=5)
        
        self.method_choices = ["随机噪声", "色彩噪声"]
        self.cmb_method = wx.ComboBox(panel, choices=self.method_choices, style=wx.CB_READONLY)
        self.cmb_method.SetSelection(0)
        self.cmb_method.Bind(wx.EVT_COMBOBOX, self.on_method_change)
        method_sizer.Add(self.cmb_method, proportion=1, flag=wx.EXPAND)
        
        test_sizer.Add(method_sizer, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 测试按钮行
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_test = wx.Button(panel, label="开始测试", size=(120, -1))
        self.btn_test.Bind(wx.EVT_BUTTON, self.on_start_test)
        btn_sizer.Add(self.btn_test, flag=wx.ALIGN_CENTER)
        test_sizer.Add(btn_sizer, flag=wx.EXPAND|wx.TOP, border=10)
        
        main_sizer.Add(test_sizer, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        # 第三区域：测试结果
        result_box = wx.StaticBox(panel, label="测试结果")
        result_sizer = wx.StaticBoxSizer(result_box, wx.VERTICAL)
        
        # 结果文本框
        self.result_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        self.result_text.SetMinSize((-1, 200))  # 设置最小高度
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.result_text.SetFont(font)  # 使用等宽字体方便对齐
        
        # 添加复制按钮
        btn_copy = wx.Button(panel, label="复制结果")
        btn_copy.Bind(wx.EVT_BUTTON, self.on_copy_result)
        
        result_sizer.Add(self.result_text, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        result_sizer.Add(btn_copy, proportion=0, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=5)
        
        main_sizer.Add(result_sizer, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        # 状态栏
        self.CreateStatusBar()
        self.SetStatusText("就绪")
        
        panel.SetSizer(main_sizer)
    
    def on_open_folder(self, event):
        dlg = wx.DirDialog(self, "选择包含图像的文件夹", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.current_folder = dlg.GetPath()
            self.load_image_files(self.current_folder)
            self.SetStatusText(f"已加载 {len(self.image_files)} 个图像文件")
        dlg.Destroy()
    
    def load_image_files(self, folder_path):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        self.image_files = []
        
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in valid_extensions):
                full_path = os.path.join(folder_path, filename)
                self.image_files.append(full_path)
        
        display_names = [os.path.basename(f) for f in self.image_files]
        self.file_list.Set(display_names)

    def on_method_change(self, event):
        self.selected_method = self.cmb_method.GetValue()
        self.SetStatusText(f"当前测试方法: {self.selected_method}")
    
    def on_start_test(self, event):
        if not self.image_files:
            wx.MessageBox("请先选择包含图像的文件夹！", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        selected_indices = self.file_list.GetSelections()
        if not selected_indices:
            wx.MessageBox("请至少选择一个图像文件！", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        selected_files = [self.image_files[i] for i in selected_indices]
        
        # 清空之前的结果
        self.result_text.Clear()
        self.append_result("=== 测试开始 ===")
        self.append_result(f"测试方法: {self.selected_method}")
        self.append_result(f"测试文件: {len(selected_files)}个")
        
        try:
            if self.selected_method == "随机噪声":
                results = CheckNoise.analyze_image_noise(selected_files, n_frame=len(selected_files))
                self.append_result("\n===== 噪声测试结果 =====")
                self.append_result(f"随机噪声均值: {results['random_noise_mean']:.2f} ADU")
                self.append_result(f"随机噪声标准差: {results['random_noise_std']:.2f} ADU")
                
            elif self.selected_method == "色彩噪声":
                # 这里添加色彩噪声测试代码
                results = ColorNoise.analyze_chromatic_noise(selected_files, color_space="YUV", roi_size=512, n_frames=len(selected_files))
                #output(results)
                print("===== 色彩噪声分析结果 =====")
                
                self.append_result("\n===== 色彩噪声分析结果 =====")
                for ch, stats in results['noise_stats'].items():
                    self.append_result(f"[{ch}通道] 噪声均值: {stats['noise_mean']:.2f}, SNR: {stats['SNR']:.1f} dB")
                
            self.append_result("\n=== 测试完成 ===")
            self.SetStatusText("测试完成")
            
        except Exception as e:
            self.append_result(f"\n!!! 测试出错: {str(e)}")
            self.SetStatusText("测试出错")
    
    def append_result(self, text):
        """向结果文本框添加文本"""
        self.result_text.AppendText(text + "\n")
        self.result_text.ShowPosition(self.result_text.GetLastPosition())
    
    def on_copy_result(self, event):
        """复制结果到剪贴板"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.result_text.GetValue()))
            wx.TheClipboard.Close()
            self.SetStatusText("结果已复制到剪贴板")

if __name__ == "__main__":
    app = wx.App(False)
    frame = ImageFileBrowser()
    frame.Show()
    app.MainLoop()
