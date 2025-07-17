from bot_tool_framework import BaseTest, register_test

@register_test("Network")
class NetworkTest(BaseTest):
    param_template = {"host": "8.8.8.8", "timeout": 5}
    def run(self):
        self.add_log("NetworkTest started")
        # TODO: 实现 Network 测试逻辑
        self.result = "NetworkTest finished" 