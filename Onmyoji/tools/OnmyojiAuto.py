import random
import threading
import time
import math
from functools import lru_cache

import win32gui
import win32api
import win32con
import pyautogui
import numpy as np


class OnmyjiAutomation:
    def __init__(self, window_title):
        # 窗口信息获取与初始化
        self.hwnd = win32gui.FindWindow(None, window_title)
        if not self.hwnd:
            print(f"无法找到窗口 {window_title}")
            raise Exception('无法获取游戏窗口尺寸')

        self.area = self.get_window_rect()
        self.x1, self.y1, self.width, self.height = self.area
        self.x2, self.y2 = self.x1 + self.width, self.y1 + self.height

        # 线程与控制变量
        self.lock = threading.Lock()
        self.shutdown_flag = False

        # 节点时间控制核心参数（优化后）
        self.base_interval = 0.01  # 基础节点间隔（秒）
        self.max_nodes = 8  # 减少最大节点数
        self.min_nodes = 2  # 减少最小节点数
        self.max_total_time = 1.2  # 缩短总流程上限

        # 图像识别缓存
        self.recognition_cache = {}
        self.cache_timeout = 1.0  # 缓存超时时间（秒）

    def print_window_info(self):
        """输出窗口信息"""
        print('已获取到游戏窗口信息\n'
              f'窗口左上角的位置是({self.x1},{self.y1})\n'
              f'窗口右下角的位置是({self.x2},{self.y2})\n')

    def get_window_rect(self):
        """获取窗口矩形区域"""
        rect = win32gui.GetWindowRect(self.hwnd)
        x1, y1, x2, y2 = rect
        return (x1, y1, x2 - x1, y2 - y1)

    @lru_cache(maxsize=32)
    def _get_scaled_logo(self, logo, scale=1.0):
        """缓存并返回缩放后的图像模板"""
        # 这里也可以添加图像预处理逻辑，如缩放、灰度化
        return logo

    def onmyji(self, logo, use_cache=True):
        """图像识别 + 缓存机制"""
        current_time = time.time()

        # 检查缓存
        if use_cache and logo in self.recognition_cache:
            cached_result, cache_time = self.recognition_cache[logo]
            if current_time - cache_time < self.cache_timeout:
                if cached_result:
                    x, y, width, height = cached_result
                    self.x1 = random.randint(x, x + width)
                    self.y1 = random.randint(y, y + height)
                return cached_result is not None

        # 执行图像识别
        target = pyautogui.locateOnScreen(
            logo,
            confidence=0.75,
            region=self.area,
            grayscale=True
        )

        # 更新缓存
        self.recognition_cache[logo] = (target, current_time)

        if target:
            x, y, width, height = target
            self.x1 = random.randint(x, x + width)
            self.y1 = random.randint(y, y + height)
            return True
        return False

    def bezier_point(self, p0, p1, p2, t):
        """贝塞尔曲线计算，使用向量运算"""
        mt = 1.0 - t
        mt_sq = mt * mt
        t_sq = t * t

        x = mt_sq * p0[0] + 2 * mt * t * p1[0] + t_sq * p2[0]
        y = mt_sq * p0[1] + 2 * mt * t * p1[1] + t_sq * p2[1]
        return (round(x), round(y))

    def get_control_point(self, start, end):
        """控制点生成算法"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # 控制点计算简化
        ctrl_x = start[0] + dx * 0.5 + random.uniform(-5, 5)
        ctrl_y = start[1] + dy * 0.5 + random.uniform(-5, 5)
        return (round(ctrl_x), round(ctrl_y))

    def move_mouse(self, x, y):
        """鼠标移动"""
        # 使用绝对坐标移动，更高效
        win32api.SetCursorPos((x, y))

    def win32_double_click(self):
        """优化的双击操作，减少延迟"""
        # 组合鼠标事件，减少系统调用
        flags = win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP
        win32api.mouse_event(flags, 0, 0, 0, 0)
        # 更短的双击间隔
        time.sleep(0.03)
        win32api.mouse_event(flags, 0, 0, 0, 0)

    def calculate_movement_parameters(self, start_pos, end_pos):
        """预计算移动参数，减少实时计算量"""
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = math.hypot(dx, dy)

        # 根据距离动态调整节点数和间隔
        if distance < 50:
            nodes = self.min_nodes
            interval = self.base_interval * 1.5
        elif distance < 200:
            nodes = int(self.min_nodes + (self.max_nodes - self.min_nodes) * 0.5)
            interval = self.base_interval
        else:
            nodes = self.max_nodes
            interval = self.base_interval * 0.8

        return nodes, interval, self.get_control_point(start_pos, end_pos)

    def fixed_interval_move(self, end_pos):
        """根据贝塞尔曲线算法移动鼠标"""
        start_pos = win32api.GetCursorPos()
        if start_pos == end_pos:
            return 0.0

        # 预计算所有参数
        nodes, interval, ctrl = self.calculate_movement_parameters(start_pos, end_pos)

        # 预生成所有贝塞尔曲线上的点
        points = []
        for i in range(nodes + 1):
            t = i / nodes
            points.append(self.bezier_point(start_pos, ctrl, end_pos, t))

        # print(f"贝塞尔曲线上的点: {points}")

        # 执行移动
        start_time = time.time()
        for i, (x, y) in enumerate(points):
            if self.shutdown_flag:
                return time.time() - start_time

            self.move_mouse(x, y)

            # 最后一个节点不等待
            if i < nodes:
                # 更精确的时间控制
                target_time = start_time + i * interval
                current_time = time.time()
                if current_time < target_time:
                    time.sleep(target_time - current_time)

        return time.time() - start_time

    def perform_action(self, logo, speed):
        # 先进行识别，减少锁持有时间
        found = self.onmyji(logo)
        if not found:
            return False

        with self.lock:  # 只在执行关键操作时持有锁
            if speed == "Slow":
                total_start = time.time()

                # 执行移动
                move_duration = self.fixed_interval_move((self.x1, self.y1))

                # 执行点击
                self.win32_double_click()

                # 优化延迟时间
                elapsed = time.time() - total_start
                remaining = max(0.0, self.max_total_time - elapsed)
                time.sleep(random.uniform(1.0, 2.0) + remaining)

                # print(f"慢速模式下，移动耗时{move_duration:.3f}秒")
                return True

            elif speed == "Fast":
                # 快速模式
                self.move_mouse(self.x1, self.y1)
                self.win32_double_click()
                time.sleep(random.uniform(1.5, 3.0))
                return True

            else:
                print("未知的运行模式")
                return False

    def clear_cache(self):
        """清除识别缓存"""
        self.recognition_cache.clear()
        self._get_scaled_logo.cache_clear()
