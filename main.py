import sys
from PySide6.QtWidgets import QApplication
from Controllers.main_controller import AppController


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Image Processing Project")
    app.setApplicationVersion("1.0.0")

    try:
        with open("Interface_Package/assets/style.qss","r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Attenzione: file di stile non trovato")

    controller = AppController()
    controller.avvia()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()