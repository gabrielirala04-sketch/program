from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QMessageBox,
    QFrame,
)
import pyqtgraph as pg


def label(text, style=""):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(True)
    if style:
        widget.setObjectName(style)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


def spin(value=0, minimum=-1e9, maximum=1e9, decimals=6):
    widget = QDoubleSpinBox()
    widget.setDecimals(decimals)
    widget.setRange(minimum, maximum)
    widget.setValue(value)
    widget.setKeyboardTracking(False)
    return widget


def heading(layout, title, subtitle):
    layout.addWidget(label(title, "title"))
    layout.addWidget(label(subtitle, "muted"))


def panel():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


def plot_widget(y="Amplitud", x="Tiempo", units="s"):
    plot = pg.PlotWidget(background="#ffffff")
    plot.setMinimumHeight(230)
    plot.showGrid(x=True, y=True, alpha=0.15)
    plot.setLabel("bottom", x, units=units)
    plot.setLabel("left", y)
    for axis in ("bottom", "left"):
        plot.getAxis(axis).setPen("#9ba9b9")
        plot.getAxis(axis).setTextPen("#46556b")
    return plot


def error(parent, exc):
    QMessageBox.warning(parent, "Revisá los datos", str(exc))


STYLE = """
QWidget { font-family: "Segoe UI", "DejaVu Sans", sans-serif; font-size: 13px; color: #25354a; }
QMainWindow, QStackedWidget { background: #f2f5f9; }
QLabel { background: transparent; }
QLabel#title { font-size: 28px; font-weight: 700; color: #15263c; padding-top: 4px; }
QLabel#muted { color: #65758a; padding-bottom: 8px; }
QLabel#section { font-size: 17px; font-weight: 600; }
QLabel#metric { font-size: 30px; font-weight: 700; color: #117b73; }
QFrame#card { background: white; border: 1px solid #dfe6ee; border-radius: 12px; }
QFrame#sidebar { background: #122438; border: none; }
QFrame#sidebar QLabel { color: #afc2d7; }
QFrame#sidebar QLabel#brand { font-size: 22px; font-weight: 700; color: white; }
QListWidget#nav { background: transparent; border: none; color: #c2d1e1; outline: none; }
QListWidget#nav::item { padding: 13px 12px; margin: 3px 0; border-radius: 7px; }
QListWidget#nav::item:selected { background: #1d4555; color: #80e1cf; }
QListWidget#nav::item:hover { background: #1c364e; }
QPushButton { background: white; border: 1px solid #ccd7e3; border-radius: 6px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #eaf4f3; border-color: #16998e; }
QPushButton:disabled { color: #9ca9b8; background: #e5eaf0; }
QPushButton#primary { background: #127d74; color: white; border-color: #127d74; }
QPushButton#primary:hover { background: #0d665f; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox, QDateEdit { background: white; border: 1px solid #ccd7e3; border-radius: 5px; padding: 6px; selection-background-color: #b5e5dd; selection-color: #172c37; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border: 1px solid #168b80; }
QTableWidget, QListWidget { background: white; border: 1px solid #dfe6ee; border-radius: 6px; gridline-color: #edf1f5; alternate-background-color: #f7f9fc; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected, QListWidget::item:selected { background: #d7eeea; color: #15382f; }
QHeaderView::section { background: #eaf0f6; border: none; padding: 9px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #dfe6ee; background: white; border-radius: 5px; }
QTabBar::tab { padding: 11px 18px; background: #e5ecf3; }
QTabBar::tab:selected { background: white; color: #127d74; }
QProgressBar { border: none; border-radius: 5px; background: #e5ecf3; height: 12px; text-align: center; }
QProgressBar::chunk { background: #1b9d90; border-radius: 5px; }
QScrollArea { border: none; background: transparent; }
QToolTip { background: #122438; color: white; border: none; padding: 6px; }
"""
