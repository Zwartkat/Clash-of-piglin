import time

from core.accessors import get_debugger


class Timer:
    def __init__(self, name: str):
        self.timer_name: str = name
        self.start_time: float = time.perf_counter()
        self.paused: bool = False
        self.elapsed_paused: float = 0.0
        self.pause_start: float = 0.0

    def pause(self):
        """
        Pauses the timer.

        If the timer is already paused, a warning message is displayed.
        """
        if not self.paused:
            self.paused = True
            self.pause_start = time.perf_counter()
        else:
            get_debugger().warning(f"{self.timer_name} est déjà en pause")

    def resume(self):
        """
        Resume the timer.

        If the timer is not paused, a warning message is displayed.
        """
        if self.paused:
            self.paused = False
            self.elapsed_paused += time.perf_counter() - self.pause_start
            self.pause_start = 0.0
        else:
            get_debugger().warning(f"{self.timer_name} est déjà en pause")

    def elapsed_ms(self):
        """
        Get elapsed time in ms
        Return:
            float : Time in ms
        """
        if self.paused:
            current_elapsed = self.pause_start - self.start_time - self.elapsed_paused
        else:
            current_elapsed = (
                time.perf_counter() - self.start_time - self.elapsed_paused
            )
        return current_elapsed * 1000

    def elapsed(self):
        """
        Get elapsed time in seconds
        Return:
            int : Time in seconds
        """
        return int(self.elapsed_ms() // 1000)

    def get_format_elapsed(self) -> str:
        """
        Get formatted elapsed time mm:ss
        Return:
            str : "minutes:seconds"
        """
        elapsed = self.elapsed()
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"

    def reset(self):
        """
        Reset timer
        """
        self.start_time = time.perf_counter()
        self.paused = False
        self.elapsed_paused = 0.0
        self.pause_start = 0.0

    def is_paused(self):
        return self.pause_start != 0.0
