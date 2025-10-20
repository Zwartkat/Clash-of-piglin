class Debugger:

    def __init__(self, enabled=False):
        self.enabled = enabled

    def log(self, message):
        if self.enabled:
            print(f"[DEBUG]: {message}")

    def error(self, message):
        if self.enabled:
            print(f"[ERROR]: {message}")
