# 初始化应用程序
from PyQt6 import QtWidgets

from Onmyoji.utils.error_handler import handle_global_exception
from Onmyoji.tools.mainGui import MainWindow

def launch_app():
    app = QtWidgets.QApplication([])
    window = None
    try:
        window = MainWindow()
        window.show()
        print("程序启动成功")
        print("新增稳定模式和快速模式。\n快速模式刷本更加迅速，但是安全性低，容易被检测封号\n"
              "稳定模式刷本更加安全，但是速度较慢")
        return app.exec()
    except Exception as e:
        handle_global_exception(e, window)
        return 1