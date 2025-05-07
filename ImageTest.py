import wx
import os
import ColorSaturation
import SNR
import SFR



class ImageViewerFrame(wx.Frame):
    def __init__(self, parent, title):
        super(ImageViewerFrame, self).__init__(parent, title=title, size=(300, 200))

        self.funcs = ["空间频率响应", "色彩饱和度", "信噪比", "横向色差", "对比度"]
        self.func = ""
        self.path = ''
        
        self.InitUI()
        self.Centre()

        
    def InitUI(self):
        # 创建菜单栏
        menubar = wx.MenuBar()
        
        # 文件菜单
        fileMenu = wx.Menu()
        openItem = fileMenu.Append(wx.ID_OPEN, "&打开图片", "选择图片文件")
        fileMenu.AppendSeparator()
        exitItem = fileMenu.Append(wx.ID_EXIT, "&退出", "退出程序")
        menubar.Append(fileMenu, "&文件")

        # 增加测试方法下拉菜单
        tagMenu = wx.Menu()
        self.tagItems = {}
        
        # 动态创建标签菜单项
        for func in self.funcs:
            item = tagMenu.Append(wx.ID_ANY, func, f"选择'{func}'测试方法")
            self.tagItems[func] = item
            self.Bind(wx.EVT_MENU, lambda evt, t=func: self.OnClickFunc(evt, t), item)
        
        
        menubar.Append(tagMenu, "&标签")
        
        self.SetMenuBar(menubar)
        
        # 创建状态栏
        self.CreateStatusBar()
        self.SetStatusText("准备就绪")
        
        # 主面板
        panel = wx.Panel(self)
        
        # 垂直布局
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 底部按钮
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        btnOpen = wx.Button(panel, label="打开图片")
        btnTest = wx.Button(panel, label="执行测试")
        
        hbox.Add(btnOpen, 0, wx.ALL, 5)
        hbox.Add(btnTest, 0, wx.ALL, 5)
        
        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.BOTTOM, 0)
        
        panel.SetSizer(vbox)
        
        # 绑定事件
        self.Bind(wx.EVT_MENU, self.OnOpen, openItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitItem)
        btnOpen.Bind(wx.EVT_BUTTON, self.OnOpen)
        btnTest.Bind(wx.EVT_BUTTON, self.OnTest)
        
        # 当前图片路径
        self.currentImagePath = None
        
    def OnOpen(self, event):
        """打开图片文件"""
        wildcard = "图片文件 (*.jpg;*.png;*.bmp;*.gif)|*.jpg;*.png;*.bmp;*.gif|所有文件 (*.*)|*.*"
        
        with wx.FileDialog(self, "选择图片文件", 
                          wildcard=wildcard,
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            path = dialog.GetPath()
            self.path = path
            self.LoadImage(path)
    
    def OnTest(self, event):
        """开始测试"""
        if self.func == self.funcs[0]:
            SFR.main(self.path)
        if self.func == self.funcs[1]:
            ColorSaturation.main(self.path)
        if self.func == self.funcs[2]:
            SNR.main(self.path)
        if self.func == self.funcs[3]:
            print('testfunc:3')
        if self.func == self.funcs[4]:
            print('testfunc:4')

    def LoadImage(self, path):
        """加载并显示图片"""
        try:
            # 检查文件是否存在
            if not os.path.exists(path):
                wx.MessageBox(f"文件不存在: {path}", "错误", wx.OK | wx.ICON_ERROR)
                return
                
            # 加载图片
            image = wx.Image(path, wx.BITMAP_TYPE_ANY)
            
            self.image = image

        except Exception as e:
            wx.MessageBox(f"无法加载图片: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnClickFunc(self, event, tag):
        """选择测试方法"""
        self.func = tag

        self.SetStatusText("测试方法： " + tag)
    
    def ScaleImage(self, image, maxWidth, maxHeight):
        """按比例缩放图片"""
        origWidth = image.GetWidth()
        origHeight = image.GetHeight()
        
        # 计算缩放比例
        widthRatio = maxWidth / origWidth
        heightRatio = maxHeight / origHeight
        scale = min(widthRatio, heightRatio)
        
        # 应用缩放
        newWidth = int(origWidth * scale)
        newHeight = int(origHeight * scale)
        
        return image.Scale(newWidth, newHeight, wx.IMAGE_QUALITY_HIGH)
    
    
    def OnExit(self, event):
        """退出程序"""
        self.Close()

class ImageViewerApp(wx.App):
    def OnInit(self):
        frame = ImageViewerFrame(None, title="图片查看器")
        frame.Show()
        return True

if __name__ == "__main__":
    app = ImageViewerApp()
    app.MainLoop()
