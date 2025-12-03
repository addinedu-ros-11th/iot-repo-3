import sys
from PyQt6.QtWidgets import QApplication
from controller import SmartHomeController


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    controller = SmartHomeController()
    controller.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()