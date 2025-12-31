# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui import StudyBuddy

def main():
    app = QApplication(sys.argv)
    window = StudyBuddy()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
