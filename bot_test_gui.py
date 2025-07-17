import wx
from bot_tool_framework import Device, TEST_REGISTRY
# 显式导入所有测试类，确保注册
from bot_tests.audio_test import AudioTest
from bot_tests.camera_test import CameraTest
from bot_tests.media_test import MediaTest
from bot_tests.motor_test import MotorTest
from bot_tests.doa_test import DOATest
from bot_tests.tracking_test import TrackingTest
from bot_tests.network_test import NetworkTest
from bot_tests.thermal_test import ThermalTest

class BotTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Bot 测试工具箱", size=wx.Size(900, 700))
        self.panel = wx.Panel(self)
        self.device = None
        self.test_instance = None
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

        # 测试类型选择区
        type_box = wx.StaticBox(self.panel, label="测试类型")
        type_sizer = wx.StaticBoxSizer(type_box, wx.HORIZONTAL)
        self.test_types = list(TEST_REGISTRY.keys())
        self.type_choice = wx.ComboBox(self.panel, choices=self.test_types, style=wx.CB_READONLY)
        self.type_choice.SetSelection(0)
        self.type_choice.Bind(wx.EVT_COMBOBOX, self.on_type_change)
        type_sizer.Add(wx.StaticText(self.panel, label="选择测试类型:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        type_sizer.Add(self.type_choice, 1)
        vbox.Add(type_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # 用例参数区
        case_box = wx.StaticBox(self.panel, label="批量用例参数配置")
        case_sizer = wx.StaticBoxSizer(case_box, wx.VERTICAL)
        self.case_list = wx.ListCtrl(self.panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.case_list.InsertColumn(0, "参数", width=700)
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
        self.update_case_columns()

    def on_type_change(self, event):
        self.update_case_columns()
        self.case_list.DeleteAllItems()

    def update_case_columns(self):
        self.case_list.ClearAll()
        test_type = self.type_choice.GetValue()
        # 尝试获取参数模板
        param_template = self.get_param_template(test_type)
        if param_template:
            for idx, key in enumerate(param_template.keys()):
                self.case_list.InsertColumn(idx, key, width=120)
        else:
            self.case_list.InsertColumn(0, "参数", width=700)

    def get_param_template(self, test_type):
        test_cls = TEST_REGISTRY.get(test_type)
        if test_cls is not None and hasattr(test_cls, 'param_template'):
            return test_cls.param_template
        return None

    def on_add_case(self, event):
        test_type = self.type_choice.GetValue()
        param_template = self.get_param_template(test_type) or {}
        dlg = AddCaseDialog(self, param_template)
        if dlg.ShowModal() == wx.ID_OK:
            param_dict = dlg.get_params()
            idx = self.case_list.InsertItem(self.case_list.GetItemCount(), "")
            for col, key in enumerate(param_template.keys()):
                self.case_list.SetItem(idx, col, str(param_dict.get(key, "")))
            if not param_template:
                self.case_list.SetItem(idx, 0, str(param_dict))
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
        test_type = self.type_choice.GetValue()
        test_cls = TEST_REGISTRY[test_type]
        # 组装批量用例参数
        param_template = self.get_param_template(test_type) or {}
        case_params = []
        for i in range(self.case_list.GetItemCount()):
            if param_template:
                param_dict = {key: self.case_list.GetItemText(i, col) for col, key in enumerate(param_template.keys())}
                # 保持所有参数为字符串，类型转换交由后端用例处理
            else:
                try:
                    param_dict = eval(self.case_list.GetItemText(i, 0))
                except Exception:
                    param_dict = {}
            case_params.append(param_dict)
        # 适配MotorTest等批量参数格式
        if hasattr(test_cls, 'batch_param_key'):
            batch_key = test_cls.batch_param_key
            params = {batch_key: case_params}
            test = test_cls(self.device, params)
        else:
            test = test_cls(self.device)
            test.case_params = case_params
        test.run()
        for log in test.log:
            self.log_text.AppendText(log + "\n")
        self.log_text.AppendText(f"结果: {test.result}\n")
        self.device.disconnect()

    def on_clear_log(self, event):
        self.log_text.Clear()

class AddCaseDialog(wx.Dialog):
    def __init__(self, parent, param_template):
        super().__init__(parent, title="添加用例", size=wx.Size(500, 250))
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.inputs = {}
        if param_template:
            for key, default in param_template.items():
                hbox = wx.BoxSizer(wx.HORIZONTAL)
                hbox.Add(wx.StaticText(self, label=f"{key}:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
                input_ctrl = wx.TextCtrl(self, value=str(default))
                hbox.Add(input_ctrl, 1)
                vbox.Add(hbox, 0, wx.EXPAND|wx.ALL, 10)
                self.inputs[key] = input_ctrl
        else:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(wx.StaticText(self, label="参数(字典格式):"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
            self.param_input = wx.TextCtrl(self, value="{}")
            hbox.Add(self.param_input, 1)
            vbox.Add(hbox, 0, wx.EXPAND|wx.ALL, 10)
        btns = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK)
        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        btns.AddButton(ok_btn)
        btns.AddButton(cancel_btn)
        btns.Realize()
        vbox.Add(btns, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        self.SetSizer(vbox)
        self.Fit()

    def get_params(self):
        def smart_cast(val):
            try:
                v = val.strip()
                if v.lower() == "true":
                    return True
                if v.lower() == "false":
                    return False
                if v.startswith('-') and v[1:].replace('.', '', 1).isdigit():
                    if '.' in v:
                        return float(v)
                    return int(v)
                if v.replace('.', '', 1).isdigit():
                    if '.' in v:
                        return float(v)
                    return int(v)
                return v
            except Exception:
                return val
        if self.inputs:
            return {k: smart_cast(v.GetValue()) for k, v in self.inputs.items()}
        elif hasattr(self, 'param_input'):
            try:
                return eval(self.param_input.GetValue())
            except Exception:
                return {}
        return {}

if __name__ == "__main__":
    app = wx.App(False)
    frame = BotTestFrame()
    app.MainLoop() 