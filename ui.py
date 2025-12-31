import sys
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QSpinBox,
    QListWidget, QLineEdit, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer

from blocker import AppBlocker
from timer import PomodoroTimer
from notifications import send_notification


class StudyBuddy(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Study Buddy")
        self.resize(320, 420)

        # ---- Logic Objects ----
        self.timer_logic = PomodoroTimer()
        self.blocker = AppBlocker()
        self.blocker_counter = 0
        self.blocker_interval = 5  # seconds

        # ---- UI Widgets ----
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: bold;")

        self.study_input = QSpinBox()
        self.study_input.setRange(1, 180)
        self.study_input.setValue(50)

        self.break_input = QSpinBox()
        self.break_input.setRange(1, 60)
        self.break_input.setValue(10)

        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 10)
        self.interval_input.setValue(4)

        self.start_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")

        self.block_list = QListWidget()
        self.block_input = QLineEdit()
        self.block_input.setPlaceholderText("App name (e.g. Discord)")
        self.add_block_button = QPushButton("Add")
        self.remove_block_button = QPushButton("Remove Selected")

        # ---- Layouts ----
        main = QVBoxLayout(self)
        main.addWidget(self.status_label)
        main.addWidget(self.timer_label)

        for label, widget in [
            ("Study (min):", self.study_input),
            ("Break (min):", self.break_input),
            ("Sessions:", self.interval_input)
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(widget)
            main.addLayout(row)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.reset_button)
        main.addLayout(buttons)

        main.addWidget(QLabel("Blocked applications:"))
        main.addWidget(self.block_list)

        block_row = QHBoxLayout()
        block_row.addWidget(self.block_input)
        block_row.addWidget(self.add_block_button)
        main.addLayout(block_row)
        main.addWidget(self.remove_block_button)

        # ---- Timer ----
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        # ---- State ----
        self.is_paused = False

        # ---- Signals ----
        self.start_button.clicked.connect(self.handle_start)
        self.reset_button.clicked.connect(self.reset_timer)
        self.add_block_button.clicked.connect(self.add_blocked_app)
        self.remove_block_button.clicked.connect(self.remove_blocked_app)

    # ------------------ Logic ------------------

    def handle_start(self):
        if not self.timer.isActive() and self.timer_logic.remaining_seconds == 0:
            self.start_sessions()
        elif self.timer.isActive():
            self.timer.stop()
            self.is_paused = True
            self.start_button.setText("Resume")
        else:
            self.timer.start(1000)
            self.is_paused = False
            self.start_button.setText("Pause")

    def start_sessions(self):
        self.timer_logic.sessions_left = self.interval_input.value()
        self.start_study()
        self.start_button.setText("Pause")

        apps = [self.block_list.item(i).text() for i in range(self.block_list.count())]
        self.blocker.set_blocked_apps(apps)

    def start_study(self):
        self.status_label.setText("Study Time")
        self.timer_logic.start_study(self.study_input.value())
        self.timer.start(1000)
        send_notification("Study Started", "Time to focus")

    def start_break(self):
        self.status_label.setText("Break Time")
        self.timer_logic.start_break(self.break_input.value())
        self.timer.start(1000)
        send_notification("Break Time", "Take a break")

    def update_timer(self):
        if self.timer_logic.is_study and not self.is_paused:
            self.blocker_counter += 1
            if self.blocker_counter >= self.blocker_interval:
                self.blocker.enforce()
                self.blocker_counter = 0

        self.timer_logic.tick()
        self.update_display()

        if self.timer_logic.remaining_seconds <= 0:
            self.timer.stop()
            if self.timer_logic.is_study:
                self.timer_logic.sessions_left -= 1
                if self.timer_logic.sessions_left == 0:
                    self.status_label.setText("All sessions complete!")
                    send_notification("Done", "Great job!")
                    self.start_button.setText("Start")
                else:
                    self.start_break()
            else:
                self.start_study()

    def update_display(self):
        m = self.timer_logic.remaining_seconds // 60
        s = self.timer_logic.remaining_seconds % 60
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def reset_timer(self):
        self.timer.stop()
        self.timer_logic.remaining_seconds = 0
        self.timer_label.setText("00:00")
        self.status_label.setText("Ready")
        self.start_button.setText("Start")

    def add_blocked_app(self):
        app_name = self.block_input.text().strip()
        if app_name:
            self.block_list.addItem(app_name)
            self.block_input.clear()
            self.sync_blocked_apps()

    def remove_blocked_app(self):
        for item in self.block_list.selectedItems():
            self.block_list.takeItem(self.block_list.row(item))
        self.sync_blocked_apps()

    def sync_blocked_apps(self):
        blocked_apps = [
            self.block_list.item(i).text()
            for i in range(self.block_list.count())
        ]
        self.blocker.set_blocked_apps(blocked_apps)
