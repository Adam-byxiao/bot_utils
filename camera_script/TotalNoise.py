import cv2
import numpy as np
import os
import time
import wx
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文显示
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class ImageNoiseAnalyzer:
    def __init__(self):
        self.results = {}
        self.roi = None  # 存储ROI坐标(x,y,w,h)
        
    def set_roi(self, roi):
        """手动设置ROI区域"""
        self.roi = roi
        
    def analyze_noise(self, image_path):
        """
        分析图像噪声特性
        :param image_path: 图像路径
        :return: 噪声分析结果字典
        """
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")
            
        # 转换为灰度图用于基础分析
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检查是否设置了ROI
        if self.roi is None:
            raise ValueError("未设置ROI区域，请先选择24色卡区域")
            
        x, y, w, h = self.roi
        dark_patch = gray[y:y+h, x:x+w]
        
        # 计算噪声指标
        self.results = {
            'image_size': img.shape,
            'roi': self.roi,
            'random_noise_mean': float(np.mean(dark_patch)),
            'random_noise_std': float(np.std(dark_patch)),
            'dynamic_range': self._calc_dynamic_range(gray),
            'color_noise': self._analyze_color_noise(img),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return self.results
    
    def _calc_dynamic_range(self, gray_img):
        """
        计算动态范围
        """
        dark_std = self.results.get('random_noise_std', 1)
        saturated = np.percentile(gray_img, 99.9)
        return 20 * np.log10(saturated / (dark_std + 1e-6))
    
    def _analyze_color_noise(self, color_img):
        """
        分析各颜色通道噪声特性
        """
        x, y, w, h = self.roi
        channels = cv2.split(color_img)
        color_results = {}
        
        for i, ch in enumerate(['B', 'G', 'R']):
            patch = channels[i][y:y+h, x:x+w]
            color_results[ch] = {
                'mean': float(np.mean(patch)),
                'std': float(np.std(patch)),
                'snr': 20 * np.log10(np.mean(patch)/(np.std(patch)+1e-6))
            }
            
        return color_results
    
    def generate_report(self):
        """
        生成测试报告文本
        """
        if not self.results:
            return "未生成测试结果"
            
        report = f"""=== 图像噪声测试报告 ===
测试时间: {self.results['timestamp']}
图像尺寸: {self.results['image_size']}
ROI区域: {self.results['roi']}

--- 基础噪声 ---
均值: {self.results['random_noise_mean']:.2f}
标准差: {self.results['random_noise_std']:.2f}
动态范围: {self.results['dynamic_range']:.2f} dB

--- 色彩噪声 ---"""
        
        for ch, vals in self.results['color_noise'].items():
            report += f"""
{ch}通道:
  均值: {vals['mean']:.2f}
  标准差: {vals['std']:.2f}
  信噪比: {vals['snr']:.2f} dB"""
        
        return report




class ROISelectorDialog(wx.Dialog):
    def __init__(self, parent, image_path):
        super().__init__(parent, title="选择24色卡区域", size=(1080, 720))
        self.image_path = image_path
        self.roi = None
        self.dragging = False
        self.start_pos = None
        self.current_pos = None
        
        # 加载图像
        self.img = cv2.imread(image_path)
        if self.img is None:
            wx.MessageBox("无法加载图像", "错误", wx.OK|wx.ICON_ERROR)
            self.Destroy()
            return
        
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.height, self.width = self.img.shape[:2]
        
        # 创建UI
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 图像显示区域
        self.figure = plt.figure(figsize=(10, 8))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 关键修改：设置图像显示参数
        self.ax.imshow(self.img, aspect='auto')
        self.ax.set_title("请用鼠标框选24色卡区域")
        self.ax.axis('off')  # 关闭坐标轴
        self.figure.tight_layout()  # 自动调整布局
        
        self.canvas.draw()
        
        # 绑定鼠标事件
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.canvas.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.canvas.Bind(wx.EVT_MOTION, self.on_mouse_move)
        
        # 确认按钮
        btn_sizer = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(panel, wx.ID_OK, label="确定")
        btn_ok.SetDefault()
        btn_sizer.AddButton(btn_ok)
        
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, label="取消")
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(btn_sizer, proportion=0, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        # 初始化坐标转换参数
        self._init_coord_transform()
        
    def _init_coord_transform(self):
        """初始化坐标转换参数"""
        # 获取图像在画布中的实际显示区域
        self.canvas.draw()
        self.bbox = self.ax.get_window_extent().transformed(
            self.figure.dpi_scale_trans.inverted())
        
        # 计算缩放比例
        img_aspect = self.width / self.height
        canvas_aspect = self.bbox.width / self.bbox.height
        
        if img_aspect > canvas_aspect:
            # 宽度受限
            self.scale = self.bbox.width / self.width
            self.offset_x = 0
            self.offset_y = (self.bbox.height - self.height * self.scale) / 2
        else:
            # 高度受限
            self.scale = self.bbox.height / self.height
            self.offset_x = (self.bbox.width - self.width * self.scale) / 2
            self.offset_y = 0
            
    def on_mouse_down(self, event):
        x, y = event.GetPosition()
        img_x, img_y = self._convert_coords(x, y)
        self.start_pos = (img_x, img_y)
        self.dragging = True
        
    def on_mouse_up(self, event):
        if self.dragging:
            x, y = event.GetPosition()
            img_x, img_y = self._convert_coords(x, y)
            self.current_pos = (img_x, img_y)
            self.dragging = False
            self.draw_roi()
            
    def on_mouse_move(self, event):
        if self.dragging:
            x, y = event.GetPosition()
            img_x, img_y = self._convert_coords(x, y)
            self.current_pos = (img_x, img_y)
            self.draw_roi()
            
    def _convert_coords(self, x, y):
        """将窗口坐标转换为图像坐标"""
        # 转换为相对于画布的坐标
        x_canvas = x / self.canvas.GetSize().width * self.bbox.width
        y_canvas = y / self.canvas.GetSize().height * self.bbox.height
        
        # 转换为图像坐标
        img_x = (x_canvas - self.offset_x) / self.scale
        img_y = (y_canvas - self.offset_y) / self.scale
        
        # 限制在图像范围内
        img_x = max(0, min(int(img_x), self.width-1))
        img_y = max(0, min(int(img_y), self.height-1))
        
        return img_x, img_y
    
    def draw_roi(self):
        """绘制当前ROI选择框"""
        if self.start_pos and self.current_pos:
            self.ax.clear()
            self.ax.imshow(self.img, aspect='auto')
            self.ax.axis('off')
            
            x1, y1 = self.start_pos
            x2, y2 = self.current_pos
            width, height = abs(x2-x1), abs(y2-y1)
            
            # 确保ROI有效
            if width > 10 and height > 10:
                self.roi = (min(x1,x2), min(y1,y2), width, height)
                rect = plt.Rectangle((self.roi[0], self.roi[1]), 
                                    self.roi[2], self.roi[3],
                                    fill=False, edgecolor='red', linewidth=2)
                self.ax.add_patch(rect)
                self.ax.set_title(f"已选择区域: {self.roi}")
            
            self.canvas.draw()

class NoiseTestApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="图像噪声测试工具", size=(1000, 800))
        self.image_path = None
        self.analyzer = ImageNoiseAnalyzer()
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        
        # 主布局
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 文件选择区域
        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_open = wx.Button(panel, label="选择图像")
        btn_open.Bind(wx.EVT_BUTTON, self.on_open_image)
        file_sizer.Add(btn_open, flag=wx.ALL, border=5)
        
        self.lbl_file = wx.StaticText(panel, label="未选择图像")
        file_sizer.Add(self.lbl_file, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        
        main_sizer.Add(file_sizer, flag=wx.EXPAND)
        
        # 图像显示区域
        self.figure = plt.figure(figsize=(10, 6))
        self.canvas = FigureCanvas(panel, -1, self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.axis('off')
        self.ax.set_title("图像预览")
        self.figure.tight_layout()
        
        main_sizer.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        
        # 控制按钮区域
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_select_roi = wx.Button(panel, label="选择24色卡区域")
        btn_select_roi.Bind(wx.EVT_BUTTON, self.on_select_roi)
        btn_sizer.Add(btn_select_roi, flag=wx.ALL, border=5)
        
        btn_analyze = wx.Button(panel, label="分析噪声")
        btn_analyze.Bind(wx.EVT_BUTTON, self.on_analyze)
        btn_sizer.Add(btn_analyze, flag=wx.ALL, border=5)
        
        btn_save = wx.Button(panel, label="保存报告")
        btn_save.Bind(wx.EVT_BUTTON, self.on_save_report)
        btn_sizer.Add(btn_save, flag=wx.ALL, border=5)
        
        main_sizer.Add(btn_sizer, flag=wx.ALIGN_CENTER)
        
        # 结果显示区域
        self.txt_result = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2)
        self.txt_result.SetMinSize((-1, 200))
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.txt_result.SetFont(font)
        
        main_sizer.Add(self.txt_result, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        
        panel.SetSizer(main_sizer)
        
        # 状态栏
        self.CreateStatusBar()
        self.SetStatusText("就绪")
        
    def on_open_image(self, event):
        wildcard = "图像文件 (*.jpg;*.png;*.bmp)|*.jpg;*.jpeg;*.png;*.bmp"
        dlg = wx.FileDialog(self, "选择测试图像", wildcard=wildcard, style=wx.FD_OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.image_path = dlg.GetPath()
            self.lbl_file.SetLabel(os.path.basename(self.image_path))
            self.display_image()
            
        dlg.Destroy()
        
    def display_image(self):
        """显示当前图像"""
        if self.image_path:
            img = cv2.imread(self.image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            self.ax.clear()
            self.ax.imshow(img, aspect='auto')
            self.ax.axis('off')
            self.ax.set_title("图像预览")
            
            if hasattr(self.analyzer, 'roi') and self.analyzer.roi:
                x, y, w, h = self.analyzer.roi
                rect = plt.Rectangle((x, y), w, h, fill=False, edgecolor='red', linewidth=2)
                self.ax.add_patch(rect)
            
            self.figure.tight_layout()
            self.canvas.draw()
        
    def on_select_roi(self, event):
        if not self.image_path:
            wx.MessageBox("请先选择图像", "错误", wx.OK|wx.ICON_ERROR)
            return
            
        dlg = ROISelectorDialog(self, self.image_path)
        result = dlg.ShowModal()
        
        if result == wx.ID_OK:
            self.analyzer.set_roi(dlg.roi)
            self.display_image()
            self.SetStatusText(f"已设置ROI区域: {dlg.roi}")
            
        dlg.Destroy()
        
    def on_analyze(self, event):
        if not self.image_path:
            wx.MessageBox("请先选择图像", "错误", wx.OK|wx.ICON_ERROR)
            return
            
        if not hasattr(self.analyzer, 'roi') or not self.analyzer.roi:
            wx.MessageBox("请先选择24色卡区域", "错误", wx.OK|wx.ICON_ERROR)
            return
            
        try:
            self.analyzer.analyze_noise(self.image_path)
            report = self.analyzer.generate_report()
            self.txt_result.SetValue(report)
            self.SetStatusText("分析完成")
            
            # 显示分析结果可视化
            self.show_analysis_results()
            
        except Exception as e:
            wx.MessageBox(f"分析出错: {str(e)}", "错误", wx.OK|wx.ICON_ERROR)
            
    def show_analysis_results(self):
        """显示分析结果图表"""
        results = self.analyzer.results
        if not results:
            return
            
        fig = plt.figure(figsize=(12, 5))
        
        # 噪声分布图
        ax1 = fig.add_subplot(121)
        img = cv2.imread(self.image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        x, y, w, h = self.analyzer.roi
        patch = gray[y:y+h, x:x+w]
        
        ax1.hist(patch.ravel(), 256, [0,256])
        ax1.set_title('噪声分布直方图')
        ax1.set_xlabel('像素值')
        ax1.set_ylabel('频数')
        
        # 各通道噪声比较
        ax2 = fig.add_subplot(122)
        color_data = results['color_noise']
        channels = list(color_data.keys())
        stds = [color_data[ch]['std'] for ch in channels]
        
        ax2.bar(channels, stds, color=['blue','green','red'])
        ax2.set_title('各通道噪声比较')
        ax2.set_ylabel('噪声标准差')
        
        plt.tight_layout()
        plt.show()
        
    def on_save_report(self, event):
        if not hasattr(self.analyzer, 'results') or not self.analyzer.results:
            wx.MessageBox("没有可保存的结果", "提示", wx.OK|wx.ICON_INFORMATION)
            return
            
        dlg = wx.FileDialog(self, "保存报告", wildcard="文本文件 (*.txt)|*.txt",
                          style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.txt_result.GetValue())
            self.SetStatusText(f"报告已保存到: {path}")
            
        dlg.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    frame = NoiseTestApp()
    frame.Show()
    app.MainLoop()

