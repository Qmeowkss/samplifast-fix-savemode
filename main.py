import sys
from PyQt5.QtWidgets import QApplication
from editor_window import AudioEditor

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = AudioEditor()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
