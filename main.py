import sys
import os
from PySide6.QtWidgets import QApplication
from Controllers.main_controller import AppController

def resource_path(relative_path):
    """Calcola il percorso assoluto, compatibile sia per lo sviluppo che per l'eseguibile compilato"""
    try:
        # PyInstaller crea una cartella temporanea e mette il percorso in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Percorso di base per l'ambiente di sviluppo normale
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Image Processing Project")
    app.setApplicationVersion("1.0.0")

    qss_path = resource_path("Interface_Package/assets/style.qss")

    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())
    else:
        print(f"[DEBUG - ERROR] File di stile non trovato al percorso: {qss_path}")

    """try:
        with open("Interface_Package/assets/style.qss","r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Attenzione: file di stile non trovato")"""

    controller = AppController()
    controller.avvia()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()