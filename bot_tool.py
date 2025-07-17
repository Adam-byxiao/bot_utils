import os
import sys
import paramiko
import time
from scp import SCPClient
from datetime import datetime
import posixpath as path
import logging
import signal
from retrying import retry
import subprocess
import re
from threading import Thread
from requests import get, post
from PIL import Image
import platform


class bot_device(object):
    name = 'root'
    port = 22
    ip = ''
    pwd='test0000'
    power_status=True

    def __init__(self, ipaddress):
        self.ip = ipaddress
        self.port = bot_device.port
        self.name = bot_device.name
        self.client = None
        self.pwd = bot_device.pwd

    

class bot_test():
    test_mode = (
        'Audio',
        'Camera',
        'Media',
        'Motor',
        'DOA',
        'Tracking',
        'Network',
        'Thermal',
    )

    def __init__(self, modes, bot):
        self.modes = modes
        self.device = bot
        print(self.device.ip, self.device.port, self.device.name,self.device.pwd)

    @retry(stop_max_attempt_number=3, wait_fixed=1000)
    def connect(self):
        retries = 3
        while retries > 0:
            try:
                #signal.signal(signal.SIGINT, signal_handler)
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                logging.info(f'Trying to connect to {self.device.ip}')
                self.client.connect(self.device.ip, self.device.port, self.device.name,self.device.pwd, timeout=30)
                logging.info('Connected successfully')
                return True
            except TimeoutError:
                logging.warning('Connection timeout, retrying...')
                time.sleep(1)
                retries -= 1
            except paramiko.SSHException as e:
                logging.warning(f'SSH connection failed: {str(e)}')
                time.sleep(1)
                retries -= 1

        logging.error(f'Failed to connect to {self.ip}')
        return False

    def AudioTest(self):
        print('AudioTest')

    def CameraTest(self):
        print('CameraTest')

    def MediaTest(self):
        print('MediaTest')

    def MotorTest(self):
        motortest = MotorTester(self.client)
        #motortest.Case_HorizontalMax()
        #motortest.Case_HorizontalMax_pressure()
        #motortest.ReadTestInput()
        #motortest.StartTest()
        motortest.Case_Continue()

    def DOATest(self):
        print('DOATest')

    def TrackingTest(self):
        print('TrackingTest')

    def NetworkTest(self):
        print('NetworkTest')

    def ThermalTest(self):
        print('ThermalTest')

    def SingleModeTest(self, mode):
        if mode == bot_test.test_mode[0]:
            self.AudioTest()
        elif mode == bot_test.test_mode[1]:
            self.CameraTest()
        elif mode == bot_test.test_mode[2]:
            self.MediaTest()
        elif mode == bot_test.test_mode[3]:
            self.MotorTest()
        elif mode == bot_test.test_mode[4]:
            self.DOATest()
        elif mode == bot_test.test_mode[5]:
            self.TrackingTest()
        elif mode == bot_test.test_mode[6]:
            self.NetworkTest()
        elif mode == bot_test.test_mode[7]:
            self.ThermalTest()
        

    def ModeTest(self):
        Modenum = len(self.modes)
        mode_index = 0
        while mode_index < Modenum:
            command =input('Input test command(start or pass): ')
            if(command == 'start'):
                print('Start this testcase\n')
                self.SingleModeTest(self.modes[mode_index])
                mode_index += 1
                continue
            if(command == 'pass'):
                print('Pass this testcase\n')
                mode_index += 1
                continue
            else:
                print("Re-input your test command. input 'start' to start this testcase; input 'pass' to pass this testcase.\n")
                continue
        
        if(input('Input ENTER to end the test')):
            exit()

class MotorTester(object):

    def __init__(self,client):
        self.controller = MotorController()
        self.client = client
        self.testcase = []
    
    def ReadTestInput(self):
        line = []
        with open('CaseList.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line[0] == '#':
                    continue
                else: 
                    self.testcase.append(line)
        print(self.testcase)
            

    def StartTest(self):
        for key in self.testcase:
            if key == 'Case_HorizontalMax':
                self.Case_HorizontalMax()
            if key == 'Case_VerticalMax':
                self.Case_VerticalMax()
            if key == 'Case_H_with_V':
                self.Case_H_with_V()
            if key == 'Case_HorizontalMax_pressure':
                self.Case_HorizontalMax_pressure()
            else: 
                continue
            time.sleep(1)
    
    def Case_HorizontalMax(self):
        zero = self.controller.MotorRotateTotally(0, 340, 500, 500)
        command1 = self.controller.MotorRotateTotally(170, 340, 500, 500)
        command2 = self.controller.MotorRotateTotally(-170, 340, 500, 500)
        self.client.exec_command(zero)
        time.sleep(3)
        print('rotate to the Rightmost degree')
        self.client.exec_command(command1)
        time.sleep(3)
        print('rotate to the Leftmost degree')
        self.client.exec_command(command2)
        time.sleep(3)
    def Case_VerticalMax(self):
        zero = self.controller.MotorRotateFullDegree([0, 16])
        command1 = self.controller.MotorRotateFullDegree([0, 8])
        command2 = self.controller.MotorRotateFullDegree([0, 30])
        self.client.exec_command(zero)
        time.sleep(3)
        print('rotate to the lowest degree')
        self.client.exec_command(command1)
        time.sleep(3)
        print('rotate to the highest degree')
        self.client.exec_command(command2)
        time.sleep(3)
    def Case_H_with_V(self):
        pass
    def Case_HorizontalMax_pressure(self):
        command1 = self.controller.MotorRotateTotally(170, 340, 500, 500)
        command2 = self.controller.MotorRotateTotally(-170, 80, 500, 500)
        for i in range(20):
            self.client.exec_command(command1)
            print('Highest speed and Rightmost degree rotate in ' + str(i) + ' times')
            time.sleep(3)
            print('A low speed and Leftmost degree rotate in ' + str(i) + ' times')     
            self.client.exec_command(command2)  
            time.sleep(7)   
    def Case_Continue(self):
        for i in range(2000):
            self.Case_HorizontalMax()


class MotorController(object):

    def __init__(self, degree_hori = 0, degree_vert = 8, speed_hori = 100, speed_vert = 20, ac = 500, dc = 500):
        self.degree_hori = degree_hori
        self.degree_vert = degree_vert
        self.speed_hori = speed_hori
        self.speed_vert = speed_vert
        self.ac = ac
        self.dc = dc

    #a standard fulldegree rotation command is like: vibe-sensor-server -s degree_full 50 20 ，50 horizontal and 20 vertical
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
    
    #a standard rotate command is like: vibe-sensor-server -s rotate 50 200 500 500  50 horizontal degree, 200 horizontal speed, 500 speed acceleration and 500 speed decceleration
    def MotorRotateTotally(self, degree, speed, ac, dc):
        command = 'vibe-sensor-server -s rotate ' + str(degree) + ' ' + str(speed) + ' ' + str(ac) + ' ' + str(dc)
        self.degree_hori = degree
        self.speed_hori = speed
        self.ac = ac
        self.dc = dc
        return command
    
    #check the result of rotation-degree, return true/false
    def MotorCheckResultDegree(self, command):

        return True

    def MotorCheckResultSpeed(self, command):

        return True
        
    












bot1 = bot_device('192.168.51.169')
bot2 = bot_device('192.168.50.27')
bot3 = bot_device('192.168.51.113')

mode = ['Motor']
bottest = bot_test(mode, bot3)
bottest.connect()

bottest.ModeTest()