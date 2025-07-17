from bot_tool_framework import BaseTest, register_test

@register_test("Tracking")
class TrackingTest(BaseTest):
    param_template = {"target_id": 1, "duration": 5}
    def run(self):
        self.add_log("TrackingTest started")
        # TODO: 实现 Tracking 测试逻辑
        self.result = "TrackingTest finished" 