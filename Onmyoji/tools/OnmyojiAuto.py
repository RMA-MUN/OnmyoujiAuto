import random
import threading
import time
import math

import win32gui
import win32api
import win32con
import pyautogui


class OnmyjiAutomation:
    def __init__(self, window_title):
        window_rect = self.get_window_rect(window_title)
        if window_rect:
            x1, y1, window_width, window_height = window_rect
            self.area = (x1, y1, window_width, window_height)
        else:
            print(f"无法找到窗口 {window_title}")
            raise Exception('无法获取游戏窗口尺寸')
        self.x1 = None
        self.y1 = None
        self.lock = threading.Lock()
        self.shutdown_flag = False

        # 节点时间控制核心参数
        self.node_interval = 0.05  # 每个节点移动间隔（秒）
        self.max_nodes = 10  # 最大节点数（避免总时间过长）
        self.min_nodes = 3  # 最小节点数（保证基本平滑度）
        self.max_total_time = 1.5  # 总流程上限

    # 输出窗口信息
    def print_window_info(self):
        if self.area:
            x1, y1, width, height = self.area
            x2 = x1 + width
            y2 = y1 + height
            print('已获取到游戏窗口信息\n'
                  f'窗口左上角的位置是({x1},{y1})\n'
                  f'窗口右下角的位置是({x2},{y2})\n')

    def get_window_rect(self, window_title):
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            x1, y1, x2, y2 = rect
            return (x1, y1, x2 - x1, y2 - y1)
        else:
            print('没有找到指定窗口！')
            return None

    def Onmyji(self, logo):
        target = pyautogui.locateOnScreen(logo, confidence=0.8, region=self.area)
        if target:
            x, y, width, height = target
            self.x1 = random.randint(x, x + width)
            self.y1 = random.randint(y, y + height)
            return True
        return False

    # 快速贝塞尔计算
    def bezier_point(self, p0, p1, p2, t):
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        return (round(x), round(y))

    # 生成紧凑控制点（减少路径长度）
    def get_control_point(self, start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.hypot(dx, dy)

        # 控制点靠近直线中点，仅保留微小偏移
        ctrl_x = start[0] + dx * 0.5 + random.uniform(-distance*0.05, distance*0.05)
        ctrl_y = start[1] + dy * 0.5 + random.uniform(-distance*0.05, distance*0.05)
        return (round(ctrl_x), round(ctrl_y))

    # 使用win32 API移动鼠标
    def win32_move_mouse(self, x, y):
        """底层鼠标移动，直接调用Windows API"""
        win32api.SetCursorPos((x, y))

    # 使用win32 API双击鼠标
    def win32_double_click(self):
        """底层双击操作，直接发送鼠标事件"""
        # 左键按下
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        # 双击间隔
        time.sleep(0.05)
        # 左键再次按下
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def fixed_interval_move(self, end_pos):
        # 使用win32 API获取当前鼠标位置
        start_pos = win32api.GetCursorPos()
        if start_pos == end_pos:
            return 0.0

        # 计算距离
        distance = math.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])

        # 动态计算节点数
        nodes = int(min(max(distance / 80, self.min_nodes), self.max_nodes))

        # 获取控制点
        ctrl = self.get_control_point(start_pos, end_pos)

        # 按固定间隔移动节点
        start_time = time.time()
        for i in range(nodes + 1):
            if self.shutdown_flag:
                return time.time() - start_time

            t = i / nodes
            x, y = self.bezier_point(start_pos, ctrl, end_pos, t)
            self.win32_move_mouse(x, y)  # 使用底层API移动


            # 最后一个节点不等待
            if i < nodes:
                # 精确控制间隔时间
                elapsed = time.time() - (start_time + i * self.node_interval)
                sleep_time = max(0.001, self.node_interval - elapsed)
                time.sleep(sleep_time)

        return time.time() - start_time

    def perform_action(self, logo, speed):
        if speed == "Slow":
            with self.lock:
                if self.Onmyji(logo):
                    total_start = time.time()

                    # 执行固定间隔移动
                    move_duration = self.fixed_interval_move((self.x1, self.y1))

                    # 使用底层API执行双击
                    self.win32_double_click()

                    # 计算剩余允许时间并设置延迟
                    elapsed = time.time() - total_start
                    remaining = max(0.0, self.max_total_time - elapsed)
                    post_delay = random.uniform(0.05, min(0.3, remaining))
                    time.sleep(post_delay)

                    # 调试信息
                    # total_duration = time.time() - total_start
                    # nodes_used = int(min(max(math.hypot(self.x1 - win32api.GetCursorPos()[0],
                    #                                     self.y1 - win32api.GetCursorPos()[1])/80,
                    #                          self.min_nodes), self.max_nodes))
                    # print(f"节点数: {nodes_used}, 实际间隔: {move_duration/nodes_used:.3f}秒, 总耗时: {total_duration:.3f}秒")
                    return True
                return False

        elif speed == "Fast":
            # 获取锁
            with self.lock:
                if self.Onmyji(logo):
                    logo_target = pyautogui.moveTo(self.x1, self.y1)
                    pyautogui.doubleClick(logo_target)
                    # print(f'移动到{self.x1}, {self.y1}并执行操作')
                    time.sleep(2)
                    return True  # 成功执行操作，返回 True
                return False
        else:
            print("未知的运行模式")
            return False