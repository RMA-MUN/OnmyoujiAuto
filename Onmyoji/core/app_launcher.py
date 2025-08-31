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
        return app.exec()
    except Exception as e:
        handle_global_exception(e, window)
        return 1