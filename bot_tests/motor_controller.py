class MotorController:
    def __init__(self, degree_hori=0, degree_vert=8, speed_hori=100, speed_vert=20, ac=500, dc=500):
        self.degree_hori = degree_hori
        self.degree_vert = degree_vert
        self.speed_hori = speed_hori
        self.speed_vert = speed_vert
        self.ac = ac
        self.dc = dc

    def MotorRotateFullDegree(self, degree):
        D = str(degree[0]) + ' ' + str(degree[1])
        command = 'vibe-sensor-server -s degree_full ' + D
        self.degree_hori = degree[0]
        self.degree_vert = degree[1]
        return command

    def MotorRotateChangeFullSpeed(self, velocity):
        V = str(velocity[0]) + ' ' + str(velocity[1])
        command = 'vibe-sensor-server -s speed_full ' + V
        self.speed_hori = velocity[0]
        self.speed_vert = velocity[1]
        return command

    def MotorRotateTotally(self, degree, speed, ac, dc):
        command = f'vibe-sensor-server -s rotate {degree} {speed} {ac} {dc}'
        self.degree_hori = degree
        self.speed_hori = speed
        self.ac = ac
        self.dc = dc
        return command

    def MotorCheckResultDegree(self, command):
        # TODO: 实现旋转角度结果检查
        return True

    def MotorCheckResultSpeed(self, command):
        # TODO: 实现旋转速度结果检查
        return True 