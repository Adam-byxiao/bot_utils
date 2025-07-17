from bot_tool_framework import BaseTest, register_test
from .motor_controller import MotorController
import time

@register_test("Motor")
class MotorTest(BaseTest):
    param_template = {"degree": 170, "speed": 340, "ac": 500, "dc": 500}
    batch_param_key = "Case_HorizontalMax"  # 默认批量用例键
    def __init__(self, device, case_params=None):
        super().__init__(device)
        self.controller = MotorController()
        self.case_params = case_params or {}

    def run(self):
        if not self.case_params:
            self.add_log("No test cases specified, running default Case_HorizontalMax once.")
            self.Case_HorizontalMax()
        else:
            for case_name, param_list in self.case_params.items():
                for params in param_list:
                    case_func = getattr(self, case_name, None)
                    if case_func:
                        self.add_log(f"Running {case_name} with params {params}")
                        case_func(**params)
                    else:
                        self.add_log(f"Unknown test case: {case_name}")
        self.result = "Batch motor test finished"

    def Case_HorizontalMax(self, degree=170, speed=340, ac=500, dc=500):
        degree = int(degree)
        speed = int(speed)
        ac = int(ac)
        dc = int(dc)
        zero = self.controller.MotorRotateTotally(0, speed, ac, dc)
        command1 = self.controller.MotorRotateTotally(degree, speed, ac, dc)
        command2 = self.controller.MotorRotateTotally(-degree, speed, ac, dc)
        self.device.exec_command(zero)
        time.sleep(3)
        self.add_log('rotate to the Rightmost degree')
        self.device.exec_command(command1)
        time.sleep(3)
        self.add_log('rotate to the Leftmost degree')
        self.device.exec_command(command2)
        time.sleep(3)

    def Case_VerticalMax(self, degree=16, speed=200, ac=500, dc=500):
        degree = int(degree)
        speed = int(speed)
        ac = int(ac)
        dc = int(dc)
        zero = self.controller.MotorRotateFullDegree([0, degree])
        command1 = self.controller.MotorRotateFullDegree([0, 8])
        command2 = self.controller.MotorRotateFullDegree([0, 30])
        self.device.exec_command(zero)
        time.sleep(3)
        self.add_log('rotate to the lowest degree')
        self.device.exec_command(command1)
        time.sleep(3)
        self.add_log('rotate to the highest degree')
        self.device.exec_command(command2)
        time.sleep(3)

    def Case_H_with_V(self, **kwargs):
        self.add_log('Case_H_with_V not implemented')
        pass

    def Case_HorizontalMax_pressure(self, degree=170, speed1=340, speed2=80, ac=500, dc=500, repeat=20):
        degree = int(degree)
        speed1 = int(speed1)
        speed2 = int(speed2)
        ac = int(ac)
        dc = int(dc)
        repeat = int(repeat)
        command1 = self.controller.MotorRotateTotally(degree, speed1, ac, dc)
        command2 = self.controller.MotorRotateTotally(-degree, speed2, ac, dc)
        for i in range(repeat):
            self.device.exec_command(command1)
            self.add_log(f'Highest speed and Rightmost degree rotate in {i} times')
            time.sleep(3)
            self.add_log(f'A low speed and Leftmost degree rotate in {i} times')
            self.device.exec_command(command2)
            time.sleep(7)

    def Case_Continue(self, repeat=10):
        repeat = int(repeat)
        for i in range(repeat):
            self.Case_HorizontalMax() 