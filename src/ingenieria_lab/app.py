import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from ingenieria_lab.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Ingeniería Lab")
    app.setOrganizationName("IngenieriaLab")
    try:
        window = MainWindow()
    except Exception as exc:
        QMessageBox.critical(
            None,
            "No se pudo abrir Ingeniería Lab",
            f"No fue posible iniciar el programa: {exc}",
        )
        return 1
    window.show()
    return app.exec()
