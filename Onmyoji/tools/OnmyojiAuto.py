"""
模块功能：构建主要的连点函数和算法，为后续主程序导入和使用创造条件
"""
import random
import threading
import time

import pyautogui
import win32gui


# 构建类
class OnmyjiAutomation:
    def __init__(self, window_title):
        # 根据当前窗口尺寸动态设置区域
        window_rect = self.get_window_rect(window_title)
        if window_rect:
            x1, y1, window_width, window_height = window_rect
            self.area = (x1, y1, window_width, window_height)
        else:
            print(f"无法找到窗口 {window_title}")
            raise Exception('无法获取游戏窗口尺寸')
        # print(f'[DEBUG] 初始化截图区域尺寸: {self.area[2]}x{self.area[3]}')
        self.x1 = None
        self.y1 = None
        # 初始化锁对象
        self.lock = threading.Lock()
        self.shutdown_flag = False

    # 用于获取窗口位置的函数
    def get_window_rect(self, window_title):
        # 查找窗口句柄
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            # 获取窗口的坐标
            """
            :param x1,x2,y1,y2: 窗口左上角和右下角的坐标
            :param width,height: 窗口的宽度和高度
            :return: (x1, y1, width, height)
            """
            rect = win32gui.GetWindowRect(hwnd)
            x1 = rect[0]
            y1 = rect[1]
            x2 = rect[2]
            y2 = rect[3]
            width = x2 - x1
            height = y2 - y1
            # 这里只返回窗口信息，不打印
            return (x1, y1, width, height)
        else:
            print('没有找到指定窗口！')
            return None

    # 输出窗口信息
    def print_window_info(self):
        if self.area:
            x1, y1, width, height = self.area
            x2 = x1 + width
            y2 = y1 + height
            print('已获取到游戏窗口信息\n'
                  f'窗口左上角的位置是({x1},{y1})\n'
                  f'窗口右下角的位置是({x2},{y2})\n')

    # 主要的连点函数
    def Onmyji(self, logo):
        # 寻找图片
        target = pyautogui.locateOnScreen(logo, confidence=0.8, region=self.area)
        if target is not None:
            # 每一次随机点位，防止持续点击一个位置被查封
            x, y, width, height = target
            self.x1 = random.randint(x, x + width)
            self.y1 = random.randint(y, y + height)
            return True
        return False

    # 输出提示
    def perform_action(self, logo):
        # 获取锁
        with self.lock:
            if self.Onmyji(logo):
                logo_target = pyautogui.moveTo(self.x1, self.y1)
                pyautogui.doubleClick(logo_target)
                # print(f'移动到{self.x1}, {self.y1}并执行操作')
                time.sleep(2)
                return True  # 成功执行操作，返回 True
            return False