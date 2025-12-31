import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QListWidget,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
import psutil
import os
from plyer import notification

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


class StudyBuddy(QWidget):
    def __init__(self):
        super().__init__()
        self.blocker = AppBlocker()
        self.blocker_counter = 0
        self.blocker_interval = 5  # seconds

        self.setWindowTitle("Study Buddy")
        self.resize(300, 250)

        # ----- Widgets -----

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        # Timer display
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: bold;")

        # Study input
        self.study_label = QLabel("Study (min):")
        self.study_input = QSpinBox()
        self.study_input.setRange(1, 180)
        self.study_input.setValue(50)

        # Break input
        self.break_label = QLabel("Break (min):")
        self.break_input = QSpinBox()
        self.break_input.setRange(1, 60)
        self.break_input.setValue(10)

        # Interval input
        self.interval_label = QLabel("Sessions:")
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 10)
        self.interval_input.setValue(4)

        # Start & Reset buttons
        self.start_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")

        # Block list widgets
        self.block_label = QLabel("Blocked applications:")
        self.block_list = QListWidget()
        self.block_input = QLineEdit()
        self.block_input.setPlaceholderText("App name (e.g. Safari, Discord)")
        self.add_block_button = QPushButton("Add")
        self.remove_block_button = QPushButton("Remove Selected")

        # ----- Layout -----
        main_layout = QVBoxLayout()

        # Add status and timer
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.timer_label)

        # Study, Break, Interval rows
        study_row = QHBoxLayout()
        study_row.addWidget(self.study_label)
        study_row.addWidget(self.study_input)

        break_row = QHBoxLayout()
        break_row.addWidget(self.break_label)
        break_row.addWidget(self.break_input)

        interval_row = QHBoxLayout()
        interval_row.addWidget(self.interval_label)
        interval_row.addWidget(self.interval_input)

        main_layout.addLayout(study_row)
        main_layout.addLayout(break_row)
        main_layout.addLayout(interval_row)

        # Button row
        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.reset_button)
        main_layout.addLayout(button_row)

        # Block list layout
        block_input_row = QHBoxLayout()
        block_input_row.addWidget(self.block_input)
        block_input_row.addWidget(self.add_block_button)

        main_layout.addWidget(self.block_label)
        main_layout.addWidget(self.block_list)
        main_layout.addLayout(block_input_row)
        main_layout.addWidget(self.remove_block_button)

        self.setLayout(main_layout)

        # ---- Fucntionality ----
        # Timer logic
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.is_study = True
        self.is_paused = False
        self.remaining_seconds = 0
        self.sessions_left = 0

        self.start_button.clicked.connect(self.handle_button)
        self.reset_button.clicked.connect(self.reset_timer)

        self.add_block_button.clicked.connect(self.add_blocked_app)
        self.remove_block_button.clicked.connect(self.remove_blocked_app)
        
    def start_timer(self):
        self.sessions_left = self.interval_input.value()
        self.start_study_session()

        blocked_apps = [
            self.block_list.item(i).text()
            for i in range(self.block_list.count())
        ]
        self.blocker.set_blocked_apps(blocked_apps)


    def start_study_session(self):
        if self.sessions_left <= 0:
            self.timer_label.setText("Done")
            self.start_button.setText("Start")
            self.remaining_seconds = 0
            self.status_label.setText("All sessions complete!")
            return

        self.is_study = True
        self.remaining_seconds = self.study_input.value() * 60
        self.status_label.setText("Study Time")
        self.timer.start(1000)

        # Optional: notification
        self.send_notification(
            "Study Session Started",
            f"Focus for {self.study_input.value()} minutes."
        )

    def start_break_session(self):
        self.is_study = False
        self.remaining_seconds = self.break_input.value() * 60
        self.status_label.setText("Break Time")
        self.timer.start(1000)

        # Optional: notification
        self.send_notification(
            "Break Started",
            f"Relax for {self.break_input.value()} minutes."
        )

    def handle_button(self):
        if not self.timer.isActive() and self.remaining_seconds == 0:
            # Fresh start
            self.start_button.setText("Pause")
            self.is_paused = False
            self.start_timer()

        elif self.timer.isActive():
            # Pause
            self.timer.stop()
            self.is_paused = True
            self.start_button.setText("Resume")

        else:
            # Resume
            self.timer.start(1000)
            self.is_paused = False
            self.start_button.setText("Pause")

    def reset_timer(self):
        self.timer.stop()
        self.remaining_seconds = 0
        self.sessions_left = self.interval_input.value()
        self.is_study = True
        self.is_paused = False

        self.timer_label.setText("00:00")
        self.status_label.setText("Ready")
        self.start_button.setText("Start")

    def update_timer(self):
        # Enforce app blocking during study sessions every blocker_interval seconds
        if self.is_study and not self.is_paused:
            self.blocker_counter += 1
            if self.blocker_counter >= self.blocker_interval:
                self.blocker.enforce()
                self.blocker_counter = 0

        # Countdown
        if not self.is_paused:
            self.remaining_seconds -= 1
            self.update_display()

        # Handle session end
        if self.remaining_seconds <= 0:
            self.timer.stop()

            if self.is_paused:
                return

            if self.is_study:
                if self.sessions_left == 1:
                    # Last study session completed
                    self.send_notification(
                        "Congratulations!",
                        "All study sessions complete. Good job!"
                    )
                    self.timer_label.setText("Done")
                    self.start_button.setText("Start")
                    self.remaining_seconds = 0
                    self.sessions_left = 0
                else:
                    self.sessions_left -= 1
                    self.start_break_session()
            else:
                self.start_study_session()


    def add_blocked_app(self):
        app_name = self.block_input.text().strip()
        if app_name:
            self.block_list.addItem(app_name)
            self.block_input.clear()

    def remove_blocked_app(self):
        for item in self.block_list.selectedItems():
            self.block_list.takeItem(self.block_list.row(item))

    def update_display(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def send_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name="Study Buddy",
            timeout=5  # seconds
        )



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudyBuddy()
    window.show()
    app.exec()
