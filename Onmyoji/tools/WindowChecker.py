"""
窗口操作工具集
包含功能：
1. 窗口尺寸获取 (get_window_size)
2. 窗口尺寸调整 (resize_window)
3. 窗口连接检测 (connect_all)
4. 构建算法，获取窗口位置和尺寸并检查是否为标准尺寸，传递参数给Auto的region
"""


import win32gui
import win32con

from typing import Optional, Tuple
from .OnmyojiAuto import OnmyjiAutomation

class WindowChecker:
    """窗口状态检查与操作类"""

    def __init__(self):
        self.window_title = None
        self.window_handle = None

    def set_window_title(self, window_title: str) -> None:
        """设置窗口标题"""
        self.window_title = window_title
        self.automation = OnmyjiAutomation(window_title)

    def set_window_handle(self, hwnd: int):
        # 添加设置窗口句柄的方法
        self.window_handle = hwnd

    def get_window_info(self) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        """
        获取窗口的位置和尺寸信息
        返回值格式：((左上角 x, 左上角 y), (右下角 x, 右下角 y), (宽度, 高度))
        """
        if not self.window_handle and not self.window_title:
            print('窗口标题未设置且未提供窗口句柄')
            return None

        if not self.window_handle:
            hwnd = win32gui.FindWindow(None, self.window_title)
        else:
            hwnd = self.window_handle

        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            return (left, top), (right, bottom), (width, height)
        print('未找到指定客户端窗口')
        return None

    def resize_window(self, width: int, height: int, hwnd: Optional[int] = None):
        if not hwnd:
            if self.window_handle:
                hwnd = self.window_handle
            elif self.window_title:
                hwnd = win32gui.FindWindow(None, self.window_title)
            else:
                print('窗口标题未设置且未提供窗口句柄')
                return

        if hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, width, height, win32con.SWP_NOMOVE)
        else:
            print('未找到指定客户端窗口')

    def connect_all(self, target_width: int = 1404, target_height: int = 834) -> None:
        """执行完整窗口连接流程"""
        if not self.window_title:
            print('窗口标题未设置')
            return

        current_size = self.get_window_info()
        if current_size:
            current_width, current_height = current_size[2]
            if current_width != target_width or current_height != target_height:
                self.resize_window(target_width, target_height)
                # 添加区域尺寸校验
                updated_size = self.get_window_info()
                if updated_size[2] != (target_width, target_height):
                    raise ValueError(f"窗口尺寸调整失败，当前尺寸：{updated_size[2]}")

    # 获取所有窗口
    @staticmethod
    def creat_hwnd_list(self) -> list:
        """
        获取所有窗口
        """
        # 先获取到所有的窗口并存储到一个列表里
        window_hwnd_of_all = []
        win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), window_hwnd_of_all)
        return window_hwnd_of_all

    # 模糊化查找窗口
    @staticmethod
    def find_window_by_title(self, title: str) -> dict:
        """
        先遍历所有窗口，然后将窗口存储到一个列表中
        然后根据已知的要查找的窗口标题内的存在的字符串，遍历列表，找到包含该字符串的窗口并返回其句柄等信息
        """
        # 先获取到所有的窗口并存储到一个列表里
        window_list_hwnd = self.creat_hwnd_list()
        # 将窗口标题转换为字符串
        window_list_title = [win32gui.GetWindowText(hwnd) for hwnd in window_list_hwnd]

        # 遍历窗口标题列表，查找包含title字符串的窗口标题
        for window_title in window_list_title:
            if title in window_title:
                target_dict = {
                    'hwnd': window_list_hwnd[window_list_title.index(window_title)],
                    'title': window_title
                }
                return target_dict
            else:
                continue
