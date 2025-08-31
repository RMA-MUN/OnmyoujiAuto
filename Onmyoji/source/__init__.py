import os

from .common_challenge import common_challenge

# 定义模式和对应文件夹名的映射字典
MODE_MAPPING = {
    '魂土': {
        'default': 'huntu',
        '队长': 'huntu',
        '队员': 'huntu_double'
    },
    '魂王': {
        'default': 'hunwang_double',
        '队长': 'hunwang_double',
        '队员': 'hunwang_double'
    },
    '业原火': 'yeyuanhuo',
    '觉醒': 'juexing',
    '爬塔': {
        'default': 'pata',
        '门票' : 'pata',
        '体力' : 'pata_tili',
    },
    '灵染试炼': 'lingran',
    '御灵': 'yuling',
    '契灵探查': 'qilingtancha'
}

__all__ = ['mode_choice']

# 模式选择函数
def mode_choice(mode, sub_mode, times, config, window_title):
    # 从映射字典获取模式配置
    folder_info = MODE_MAPPING.get(mode)
    if folder_info:
        # 处理带子模式的配置
        if isinstance(folder_info, dict):
            folder_name = folder_info.get(sub_mode, folder_info['default'])
        # 处理简单配置
        else:
            folder_name = folder_info

        # 构建脚本路径
        script_dir = os.path.join(os.path.dirname(__file__), folder_name)
        # 执行通用挑战函数
        common_challenge(times, config, script_dir, window_title)
    else:
        print('暂不支持此模式，敬请期待！')