from bot_tool_framework import BaseTest, register_test

@register_test("Thermal")
class ThermalTest(BaseTest):
    param_template = {"sensor_id": 0, "threshold": 60}
    def run(self):
        self.add_log("ThermalTest started")
        # TODO: 实现 Thermal 测试逻辑
        self.result = "ThermalTest finished" 