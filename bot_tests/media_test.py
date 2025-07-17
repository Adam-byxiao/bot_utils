from bot_tool_framework import BaseTest, register_test

@register_test("Media")
class MediaTest(BaseTest):
    param_template = {"media_file": "", "duration": 10}
    def run(self):
        self.add_log("MediaTest started")
        # TODO: 实现媒体测试逻辑
        self.result = "MediaTest finished" 