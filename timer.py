class PomodoroTimer:
    def __init__(self):
        self.is_study = True
        self.remaining_seconds = 0
        self.sessions_left = 0

    def start_study(self, minutes):
        self.is_study = True
        self.remaining_seconds = minutes * 60

    def start_break(self, minutes):
        self.is_study = False
        self.remaining_seconds = minutes * 60

    def tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
        return self.remaining_seconds
