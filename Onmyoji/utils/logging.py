import sys
from PyQt6.QtCore import QObject, pyqtSignal

class LogEmitter(QObject):
    log_signal = pyqtSignal(str)

    def write(self, message):
        if message.strip():
            self.log_signal.emit(message)

    def flush(self):
        pass

def setup_logging(window):
    log_emitter = LogEmitter()
    log_emitter.log_signal.connect(window.log_redirect.print)
    sys.stdout = log_emitter
    sys.stderr = log_emitter