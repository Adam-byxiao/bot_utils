import wx
from bot_tool_framework import Device
from bot_tests.motor_test import MotorTest

class MotorTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Motor 批量测试工具", size=wx.Size(800, 600))
        self.panel = wx.Panel(self)
        self.device = None
        self.test_thread = None
        self.init_ui()
        self.Centre()
        self.Show()

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 设备信息区
        device_box = wx.StaticBox(self.panel, label="设备信息")
        device_sizer = wx.StaticBoxSizer(device_box, wx.HORIZONTAL)
        self.ip_input = wx.TextCtrl(self.panel, value="192.168.1.2")
        self.user_input = wx.TextCtrl(self.panel, value="root")
        self.pwd_input = wx.TextCtrl(self.panel, value="test0000", style=wx.TE_PASSWORD)
        device_sizer.Add(wx.StaticText(self.panel, label="IP:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        device_sizer.Add(self.ip_input, 0, wx.RIGHT, 10)
        device_sizer.Add(wx.StaticText(self.panel, label="用户名:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        device_sizer.Add(self.user_input, 0, wx.RIGHT, 10)
        device_sizer.Add(wx.StaticText(self.panel, label="密码:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        device_sizer.Add(self.pwd_input, 0, wx.RIGHT, 10)
        vbox.Add(device_sizer, 0, wx.EXPAND|wx.ALL, 10)

        # 用例参数区
        case_box = wx.StaticBox(self.panel, label="批量用例参数配置")
        case_sizer = wx.StaticBoxSizer(case_box, wx.VERTICAL)
        self.case_list = wx.ListCtrl(self.panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.case_list.InsertColumn(0, "用例名", width=180)
        self.case_list.InsertColumn(1, "参数", width=500)
        case_sizer.Add(self.case_list, 1, wx.EXPAND|wx.ALL, 5)
        btn_add = wx.Button(self.panel, label="添加用例")
        btn_add.Bind(wx.EVT_BUTTON, self.on_add_case)
        btn_del = wx.Button(self.panel, label="删除选中用例")
        btn_del.Bind(wx.EVT_BUTTON, self.on_del_case)
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(btn_add, 0, wx.RIGHT, 10)
        btn_hbox.Add(btn_del, 0)
        case_sizer.Add(btn_hbox, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        vbox.Add(case_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 操作区
        op_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.start_btn = wx.Button(self.panel, label="开始测试")
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_test)
        self.clear_btn = wx.Button(self.panel, label="清空日志")
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_log)
        op_hbox.Add(self.start_btn, 0, wx.RIGHT, 10)
        op_hbox.Add(self.clear_btn, 0)
        vbox.Add(op_hbox, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 10)

        # 日志区
        log_box = wx.StaticBox(self.panel, label="日志输出")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        log_sizer.Add(self.log_text, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        self.panel.SetSizer(vbox)

    def on_add_case(self, event):
        dlg = AddCaseDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            case_name, param_str = dlg.get_case()
            idx = self.case_list.InsertItem(self.case_list.GetItemCount(), case_name)
            self.case_list.SetItem(idx, 1, param_str)
        dlg.Destroy()

    def on_del_case(self, event):
        selected = []
        idx = self.case_list.GetFirstSelected()
        while idx != -1:
            selected.append(idx)
            idx = self.case_list.GetNextSelected(idx)
        for i in reversed(selected):
            self.case_list.DeleteItem(i)

    def on_start_test(self, event):
        ip = self.ip_input.GetValue()
        user = self.user_input.GetValue()
        pwd = self.pwd_input.GetValue()
        self.device = Device(ip, user, pwd)
        self.device.connect()
        # 组装批量用例参数
        case_params = {}
        for i in range(self.case_list.GetItemCount()):
            case_name = self.case_list.GetItemText(i)
            param_str = self.case_list.GetItemText(i, 1)
            try:
                param_dict = eval(param_str) if param_str else {}
            except Exception as e:
                self.log_text.AppendText(f"参数解析错误: {param_str}\n")
                continue
            case_params.setdefault(case_name, []).append(param_dict)
        test = MotorTest(self.device, case_params)
        test.run()
        # 显示日志
        for log in test.log:
            self.log_text.AppendText(log + "\n")
        self.log_text.AppendText(f"结果: {test.result}\n")
        self.device.disconnect()

    def on_clear_log(self, event):
        self.log_text.Clear()

class AddCaseDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="添加用例", size=wx.Size(400, 250))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label="用例名:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.case_choice = wx.ComboBox(panel, choices=[
            "Case_HorizontalMax", "Case_VerticalMax", "Case_H_with_V", "Case_HorizontalMax_pressure", "Case_Continue"
        ], style=wx.CB_READONLY)
        self.case_choice.SetSelection(0)
        hbox1.Add(self.case_choice, 1)
        vbox.Add(hbox1, 0, wx.EXPAND|wx.ALL, 10)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(panel, label="参数(字典格式):"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.param_input = wx.TextCtrl(panel, value="{}")
        hbox2.Add(self.param_input, 1)
        vbox.Add(hbox2, 0, wx.EXPAND|wx.ALL, 10)
        btns = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL)
        btns.AddButton(ok_btn)
        btns.AddButton(cancel_btn)
        btns.Realize()
        vbox.Add(btns, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        panel.SetSizer(vbox)
        self.Fit()

    def get_case(self):
        return self.case_choice.GetValue(), self.param_input.GetValue()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MotorTestFrame()
    app.MainLoop() 