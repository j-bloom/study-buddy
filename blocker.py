import psutil

class AppBlocker:
    def __init__(self):
        self.blocked_apps = set()

    def set_blocked_apps(self, apps):
        self.blocked_apps = {app.lower() for app in apps}

    def enforce(self):
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name and any(app in name.lower() for app in self.blocked_apps):
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
