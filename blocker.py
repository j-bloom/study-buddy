import platform
import subprocess
import os

OS_NAME = platform.system()


class AppBlocker:
    def __init__(self):
        self.blocked_apps = []

    def set_blocked_apps(self, apps):
        self.blocked_apps = apps

    def enforce(self):
        if not self.blocked_apps:
            return

        try:
            if OS_NAME == "Darwin":
                self._block_macos()
            elif OS_NAME == "Windows":
                self._block_windows()
        except Exception as e:
            print("Blocker error:", e)

    # ---------------- macOS ----------------

    def _block_macos(self):
        for app in self.blocked_apps:
            subprocess.run(
                ["pkill", "-f", app],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    # ---------------- Windows ----------------

    def _block_windows(self):
        for app in self.blocked_apps:
            subprocess.run(
                ["taskkill", "/IM", f"{app}.exe", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
