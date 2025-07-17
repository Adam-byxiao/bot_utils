# bot_tool_framework.py
"""
重构后的后端测试框架，适用于自动化设备测试，便于扩展和与GUI集成。
"""

import paramiko
from abc import ABC, abstractmethod

# 设备管理类
class Device:
    def __init__(self, ip, username, password, port=22):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.ip, self.port, self.username, self.password, timeout=30)

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def exec_command(self, command):
        if not self.client:
            raise Exception("Device not connected")
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

# 测试基类
class BaseTest(ABC):
    def __init__(self, device):
        self.device = device
        self.result = None
        self.log = []

    @abstractmethod
    def run(self):
        pass

    def add_log(self, message):
        self.log.append(message)

# 测试注册表
TEST_REGISTRY = {}

def register_test(name):
    def decorator(cls):
        TEST_REGISTRY[name] = cls
        return cls
    return decorator

# 示例测试实现
@register_test("Audio")
class AudioTest(BaseTest):
    def run(self):
        self.add_log("Running audio test...")
        # 这里写具体测试逻辑
        self.result = "Audio test passed"

@register_test("Camera")
class CameraTest(BaseTest):
    def run(self):
        self.add_log("Running camera test...")
        self.result = "Camera test passed"

# 测试任务
class TestTask:
    def __init__(self, test_name, device):
        self.test_name = test_name
        self.device = device
        self.test_instance = None
        self.result = None
        self.log = []

    def run(self):
        test_cls = TEST_REGISTRY.get(self.test_name)
        if not test_cls:
            raise Exception(f"Test {self.test_name} not registered")
        self.test_instance = test_cls(self.device)
        self.test_instance.run()
        self.result = self.test_instance.result
        self.log = self.test_instance.log

# 示例主流程
if __name__ == "__main__":
    device = Device("192.168.1.2", "root", "test0000")
    device.connect()
    task = TestTask("Audio", device)
    task.run()
    print("Result:", task.result)
    print("Log:", "\n".join(task.log))
    device.disconnect() 