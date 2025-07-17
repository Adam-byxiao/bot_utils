from bot_tool_framework import BaseTest, register_test

@register_test("DOA")
class DOATest(BaseTest):
    param_template = {"mic_count": 4, "angle": 90}
    def run(self):
        self.add_log("DOATest started")
        # TODO: 实现 DOA 测试逻辑
        self.result = "DOATest finished" 