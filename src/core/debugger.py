import inspect
import traceback


class Debugger:

    def __init__(self, enable_log=False, enable_warn=False, enable_error=False):
        self.enable_log = enable_log
        self.enable_warn = enable_warn
        self.enable_error = enable_error

    def log(self, message):
        if self.enable_log:
            print(f"[DEBUG]: {message}")

    def warning(self, message: str):
        if self.enable_warn:
            print(f"[WARNING]: {message}")

    def error(self, message):
        if self.enable_error:
            format_traceback: str = "\n".join(traceback.format_stack())
            print(f"[ERROR]: {message}\n From: \n{format_traceback}")
