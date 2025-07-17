from bot_tool_framework import BaseTest, register_test

@register_test("Audio")
class AudioTest(BaseTest):
    param_template = {"file_path": "", "sample_rate": 16000}
    def run(self):
        self.add_log("AudioTest started")
        # TODO: 实现音频测试逻辑
        self.result = "AudioTest finished" 