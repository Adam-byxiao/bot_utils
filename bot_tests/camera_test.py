from bot_tool_framework import BaseTest, register_test

@register_test("Camera")
class CameraTest(BaseTest):
    param_template = {"image_path": "", "resolution": "1920x1080"}
    def run(self):
        self.add_log("CameraTest started")
        # TODO: 实现摄像头测试逻辑
        self.result = "CameraTest finished" 