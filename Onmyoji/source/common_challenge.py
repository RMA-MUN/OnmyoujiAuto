"""
挑战函数，用for循环构建资源路径，在用if来控制自加。
"""

import os
from ..tools.OnmyojiAuto import OnmyjiAutomation


def common_challenge(times, config, script_dir, window_title):
    automation_obj = OnmyjiAutomation(window_title)

    i = 0
    while i < times:
        # 动态遍历配置文件中的所有图片键
        for key in config['image_paths']:
            img_path = os.path.join(script_dir, config['image_paths'][key])
            try:
                if automation_obj.perform_action(img_path):
                    # 执行开始操作后，i来充当计数器
                    if key == 'tiaozhan':
                        i += 1
                        print(f"还剩{times - i}次挑战")
                    elif key == 'xiezhu':
                        print("注意！！！已自动为您拒绝好友的协助！！！")
                    elif key == 'kaishi':
                        i += 1
                        print(f"还剩{times - i}次挑战")
                    elif key == 'baocang':
                        print("Warning: 您的御魂已爆仓，请注意清理御魂！！！")
            except ValueError as e:
                if "needle dimension" in str(e):
                    print(f"\n\n错误：{str(e)}")
                    print("可能原因：1.窗口尺寸不正确 2.游戏画面未正确加载 3.图片资源尺寸不匹配")
                    print("解决方案：检查窗口设置 -> 确保游戏完全加载 -> 验证图片资源尺寸")
                    return False
                raise