from PyQt5 import QtWidgets, QtGui, QtCore
import pyperclip
import requests
import threading
import webbrowser
import csv
import os
import re
from datetime import datetime
import keyboard

# Application Style
APP_STYLE = """
QWidget, QDialog {
    background-color: #371e09;
    color: white;
    font-family: "Segoe UI", Arial, sans-serif;
    border: 2px solid #ff7a00;
}
QLabel#statusText {
    font-size: 14pt;
    font-weight: bold;
    color: white;
    padding: 8px;
    border: 2px solid #ff7a00;
    background-color: #2e1608;
}
QPushButton#mainButton, QPushButton#edsmButton, QPushButton#findNearbyButton {
    background-color: #371e09;
    color: white;
    border: 2px solid #ff7a00;
    padding: 4px 10px;
}
QPushButton#edsmButton {
    background-color: #a00;
}
QPushButton#findNearbyButton {
    background-color: #0077cc;
}
QPushButton#cornerButton {
    background-color: #cc8400;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#cornerButton:hover {
    background-color: #e09500;
}
"""

# API URLs, Regex, constants
EDSM_API_URL = "https://www.edsm.net/api-v1/systems?systemName={}&showId=1"
EDSM_SYSTEM_URL = "https://www.edsm.net/en/system/id/{}/name/{}"
SPHERE_SYSTEMS_API_URL = "https://www.edsm.net/api-v1/sphere-systems?x={}&y={}&z={}&radius={}&showId=1&showCoordinates=1"
SYSTEM_NAME_PATTERN = re.compile(r"^[\w\s\-\'*\.:()]{1,64}$")
last_queried_system = None
version = "1.2"


class ClipboardMonitor(QtCore.QThread):
    new_clipboard_text = QtCore.pyqtSignal(str)

    def __init__(self, poll_interval=1000):
        super().__init__()
        self.poll_interval = poll_interval
        self.last_clipboard = ""
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.last_clipboard:
                    self.last_clipboard = current_clipboard
                    self.new_clipboard_text.emit(current_clipboard)
            except Exception as e:
                print(f"Clipboard error: {e}")
            self.msleep(self.poll_interval)

    def stop(self):
        self.running = False

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle(f"CETI {version}")
        self.resize(350, 160)
        self.setMinimumSize(100, 100)

        # State variables
        self.system_id = None
        self.visited = False
        self.toggle_key = "/"
        self.hotkey_blocked = False
        self.last_displayed_system = "N/A"
        self.last_displayed_status = "Not visited"
        self.current_timing = ""
        self.loading_active = False
        self.settings_open = False

        # CSV config and data
        self.bg_color = "#371e09"
        self.border_color = "#ff7a00"
        self.text_color = "white"
        self.csv_file = f"CETI{version}_saved_systems.csv"
        expected_header = [
            "System Name", "Status", "Time Saved", "EDSM Link", "XYZ",
            "BackgroundColor", "BorderColor", "TextColor", "Keybind"
        ]
        file_exists = os.path.isfile(self.csv_file)
        config_loaded = False

        # Read config if present, else write default config and header
        if file_exists and os.stat(self.csv_file).st_size > 0:
            with open(self.csv_file, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows and rows[0][:10] == expected_header:
                    if len(rows) > 1:
                        config_row = rows[1]
                        if len(config_row) >= 9:
                            self.bg_color = config_row[5] or self.bg_color
                            self.border_color = config_row[6] or self.border_color
                            self.text_color = config_row[7] or self.text_color
                            self.toggle_key = config_row[8] or self.toggle_key
                            config_loaded = True
        if not config_loaded:
            with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(expected_header)
                writer.writerow(["", "", "", "", "", self.bg_color, self.border_color, self.text_color, self.toggle_key])

        self.csv_file_handle = open(self.csv_file, mode="a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file_handle)
        self.apply_style()

        # Layouts and Widgets
        layout = QtWidgets.QVBoxLayout(self)
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel(f"CETI {version}")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        resize_button = QtWidgets.QPushButton("🗗")
        resize_button.setFixedSize(24, 24)
        resize_button.clicked.connect(lambda: self.resize(350, 160))

        close_button = QtWidgets.QPushButton("X")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(resize_button)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        self.system_label = QtWidgets.QLabel("Waiting for system name, CMDR...")
        self.system_label.setAlignment(QtCore.Qt.AlignCenter)
        self.system_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.system_label)

        button_layout = QtWidgets.QHBoxLayout()
        self.settings_button = QtWidgets.QPushButton("⚙️")
        self.settings_button.clicked.connect(self.open_settings)

        self.save_button = QtWidgets.QPushButton("💾")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_to_csv)

        self.find_button = QtWidgets.QPushButton("Find Nearby")
        self.find_button.setObjectName("findNearbyButton")
        self.find_button.setEnabled(False)
        self.find_button.clicked.connect(self.find_nearby_system)

        self.edsm_button = QtWidgets.QPushButton("EDSM")
        self.edsm_button.setObjectName("edsmButton")
        self.edsm_button.setEnabled(False)
        self.edsm_button.clicked.connect(self.open_edsm)

        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.find_button)   
        button_layout.addWidget(self.edsm_button)
        layout.addLayout(button_layout)

        # Register hotkey for toggling overlay
        try:
            keyboard.add_hotkey(self.toggle_key, self.toggle_visibility)
        except Exception as e:
            print(f"Hotkey registration failed: {e}")

    def apply_style(self):
        style = f"""
        QWidget, QDialog {{
            background-color: {self.bg_color};
            color: {self.text_color};
            font-family: "Segoe UI", Arial, sans-serif;
            border: 2px solid {self.border_color};
        }}
        QLabel#statusText {{
            font-size: 14pt;
            font-weight: bold;
            color: {self.text_color};
            padding: 8px;
            border: 2px solid {self.border_color};
            background-color: #2e1608;
        }}
        QPushButton#mainButton, QPushButton#edsmButton, QPushButton#findNearbyButton {{
            background-color: {self.bg_color};
            color: {self.text_color};
            border: 2px solid {self.border_color};
            padding: 4px 10px;
        }}
        QPushButton#edsmButton {{
            background-color: #a00;
        }}
        QPushButton#findNearbyButton {{
            background-color: #0077cc;
        }}
        QPushButton#cornerButton {{
            background-color: #cc8400;
            color: {self.text_color};
            border: none;
            font-weight: bold;
        }}
        QPushButton#cornerButton:hover {{
            background-color: #e09500;
        }}
        """
        self.setStyleSheet(style)
        QtWidgets.QApplication.instance().setStyleSheet(style)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def open_settings(self):
        self.settings_open = True
        dlg = SettingsDialog(self, self.update_hotkey, self.bg_color, self.border_color, self.text_color)
        dlg.hotkey_changed.connect(self.update_hotkey)
        dlg.color_changed.connect(self.update_colors)
        dlg.exec_()
        self.settings_open = False

    def save_to_csv(self):
        system_name = self.last_displayed_system
        status = self.last_displayed_status
        time_saved = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        xyz_str = ""
        if self.visited and self.system_id:
            edsm_link = EDSM_SYSTEM_URL.format(self.system_id, system_name)
        else:
            coords = self.get_xyz_coords_dialog()
            if coords is None:
                return
            x, y, z = coords
            edsm_link = "N/A"
            xyz_str = f"{x}, {y}, {z}"

        self.csv_writer.writerow([system_name, status, time_saved, edsm_link, xyz_str, "", "", "", ""])
        self.csv_file_handle.flush()
        print(f"System details saved to {self.csv_file}")
        current_text = self.system_label.text()
        if "*saved" not in current_text:
            self.system_label.setText(current_text + "\n*saved")

    def get_xyz_coords_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        layout = QtWidgets.QVBoxLayout(dialog)

        # Title bar
        title_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Enter System Coordinates")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        close_button = QtWidgets.QPushButton("X")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(dialog.reject)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        layout.addLayout(title_layout)

        input_field = QtWidgets.QLineEdit()
        input_field.setPlaceholderText("X, Y, Z (e.g., 123.45, -67.8, 9000)")
        layout.addWidget(input_field)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            try:
                parts = [float(p.strip()) for p in input_field.text().split(",")]
                if len(parts) != 3:
                    raise ValueError("Expected 3 values")
                return tuple(parts)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter 3 numeric values separated by commas.")
                return None
        return None

    def save_config_to_csv(self):
        # Update config row in CSV
        with open(self.csv_file, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        if len(rows) < 2:
            rows = [
                ["System Name", "Status", "Time Saved", "EDSM Link", "XYZ",
                 "BackgroundColor", "BorderColor", "TextColor", "Keybind"],
                ["", "", "", "", "", self.bg_color, self.border_color, self.text_color, self.toggle_key]
            ]
        else:
            rows[1][5:9] = [self.bg_color, self.border_color, self.text_color, self.toggle_key]
        with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def update_colors(self, bg_color, border_color, text_color):
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.apply_style()
        self.save_config_to_csv()

    def update_hotkey(self, new_key):
        if new_key:
            try:
                keyboard.remove_hotkey(self.toggle_key)
            except KeyError:
                pass
            self.toggle_key = new_key
            try:
                keyboard.add_hotkey(new_key, self.toggle_visibility)
                print(f"Hotkey updated to: {new_key}")
            except Exception as e:
                print(f"Failed to set hotkey '{new_key}': {e}")
            self.save_config_to_csv()

    def toggle_visibility(self):
        if self.hotkey_blocked or self.settings_open:
            return
        if not self.isVisible():
            self.showNormal()
            self.activateWindow()
            self.raise_()
        else:
            self.hide()

    def update_display(self, system_name, visited, system_id):
        display_name = system_name if len(system_name) <= 64 else "N/A"
        self.visited = visited
        self.system_id = system_id
        self.last_displayed_system = display_name
        self.last_displayed_status = "Visited" if visited else "Not visited"
        base_text = f"<div>System: {display_name}<br>Status: {self.last_displayed_status}</div>"
        timing_text = f"<div style='text-align: center; font-size: 8pt; color: #aaa;'>{self.current_timing}</div>" if self.current_timing else ""
        self.system_label.setText(base_text + timing_text)
        self.edsm_button.setEnabled(visited)
        self.save_button.setEnabled(True)
        self.find_button.setEnabled(True)  
        self.edsm_button.setStyleSheet("color: white; background-color: #0a0;" if visited else "color: white; background-color: #a00;")

    def open_edsm(self):
        if self.visited and self.system_id:
            url = EDSM_SYSTEM_URL.format(self.system_id, self.last_displayed_system)
            webbrowser.open_new_tab(url)


    def get_coords_and_radius(self):
        dialog = QtWidgets.QDialog(self)
        dialog._drag_pos = None

        def mousePressEvent(event):
            if event.button() == QtCore.Qt.LeftButton:
                dialog._drag_pos = event.globalPos() - dialog.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if event.buttons() == QtCore.Qt.LeftButton and dialog._drag_pos:
                dialog.move(event.globalPos() - dialog._drag_pos)
                event.accept()

        dialog.mousePressEvent = mousePressEvent
        dialog.mouseMoveEvent = mouseMoveEvent
        dialog.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        layout = QtWidgets.QVBoxLayout(dialog)

        # Title bar for Find Nearest Visited
        title_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Find Nearest Visited")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        close_button = QtWidgets.QPushButton("X")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(dialog.reject)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        layout.addLayout(title_layout)

        input_field = QtWidgets.QLineEdit()
        input_field.setPlaceholderText("X,Y,Z, Radius(1-200ly) (e.g., 0,0,0,10)")
        layout.addWidget(input_field)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            try:
                parts = [float(p.strip()) for p in input_field.text().split(",")]
                if len(parts) != 4:
                    raise ValueError("Expected 4 values")
                x, y, z, radius = parts
                if not (1 <= radius <= 200):
                    QtWidgets.QMessageBox.warning(self, "Invalid Radius", "Radius must be between 1 and 200.")
                    return None
                return (x, y, z, radius)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter 4 numeric values separated by commas.")
                return None
        return None

    def find_nearby_system(self):
        try:
            coords = self.get_coords_and_radius()
            if not coords:
                return
            x, y, z, radius = coords
            start_time = datetime.now()
            response = requests.get(SPHERE_SYSTEMS_API_URL.format(x, y, z, radius))
            elapsed = datetime.now() - start_time
            ms = int(elapsed.total_seconds() * 1000)

            if response.status_code == 200 and response.json():
                nearest = sorted(response.json(), key=lambda s: s.get("distance", float('inf')))[0]
                system_id = nearest.get("id")
                system_name = nearest.get("name")
                distance = nearest.get("distance")

                dialog = QtWidgets.QDialog(self)
                dialog._drag_pos = None

                def mousePressEvent(event):
                    if event.button() == QtCore.Qt.LeftButton:
                        dialog._drag_pos = event.globalPos() - dialog.frameGeometry().topLeft()
                        event.accept()

                def mouseMoveEvent(event):
                    if event.buttons() == QtCore.Qt.LeftButton and dialog._drag_pos:
                        dialog.move(event.globalPos() - dialog._drag_pos)
                        event.accept()

                dialog.mousePressEvent = mousePressEvent
                dialog.mouseMoveEvent = mouseMoveEvent

                dialog.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
                layout = QtWidgets.QVBoxLayout(dialog)

                # Title bar for Nearest Visited System
                title_layout = QtWidgets.QHBoxLayout()
                title = QtWidgets.QLabel("Nearest Visited System")
                close_button = QtWidgets.QPushButton("X")
                close_button.setFixedSize(24, 24)
                close_button.clicked.connect(dialog.reject)
                title_layout.addWidget(title)
                title_layout.addStretch()
                title_layout.addWidget(close_button)
                layout.addLayout(title_layout)

                layout.addWidget(QtWidgets.QLabel(f"Reference System: {self.last_displayed_system}"))
                layout.addWidget(QtWidgets.QLabel(f"User Input: X={x}, Y={y}, Z={z}"))
                layout.addWidget(QtWidgets.QLabel(f"Search Radius: {radius} LY"))
                layout.addWidget(QtWidgets.QLabel(f"Nearest Visited: {system_name}"))
                layout.addWidget(QtWidgets.QLabel(f"Distance: {distance:.2f} LY"))
                layout.addWidget(QtWidgets.QLabel(f"Response {response.status_code} : {ms} ms"))

                open_button = QtWidgets.QPushButton("Open in EDSM")
                open_button.setStyleSheet("color: white; background-color: #0a0; border: 2px solid #ff7a00;")
                open_button.clicked.connect(lambda: webbrowser.open_new_tab(EDSM_SYSTEM_URL.format(system_id, system_name)))
                layout.addWidget(open_button)

                dialog.exec_()
                return
            else:
                QtWidgets.QMessageBox.warning(self, "No Result", "No nearby systems found.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

class SettingsDialog(QtWidgets.QDialog):
    hotkey_changed = QtCore.pyqtSignal(str)
    color_changed = QtCore.pyqtSignal(str, str, str)

    def __init__(self, parent, toggle_hotkey_callback, bg_color, border_color, text_color):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(340, 260)

        main_layout = QtWidgets.QVBoxLayout(self)

        # Title bar with GH, Reset, and Close buttons
        title_bar = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Settings")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        gh_button = QtWidgets.QPushButton("GH")
        gh_button.setFixedSize(32, 24)
        gh_button.clicked.connect(lambda: webbrowser.open_new_tab("https://github.com/carsonbfl/CETI"))
        reset_button = QtWidgets.QPushButton("R")
        reset_button.setFixedSize(24, 24)
        reset_button.setToolTip("Reset to default settings")
        reset_button.clicked.connect(self.reset_defaults)
        close_btn = QtWidgets.QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(title)
        title_bar.addStretch()
        title_bar.addWidget(gh_button)
        title_bar.addWidget(reset_button)
        title_bar.addWidget(close_btn)
        main_layout.addLayout(title_bar)

        # Color Scheme Controls
        color_layout = QtWidgets.QHBoxLayout()
        bg_label = QtWidgets.QLabel("Background:")
        self.bg_picker = QtWidgets.QPushButton()
        self.bg_picker.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #888;")
        self.bg_picker.setFixedWidth(40)
        self.bg_picker.clicked.connect(self.pick_bg_color)

        border_label = QtWidgets.QLabel("Border:")
        self.border_picker = QtWidgets.QPushButton()
        self.border_picker.setStyleSheet(f"background-color: {border_color}; border: 1px solid #888;")
        self.border_picker.setFixedWidth(40)
        self.border_picker.clicked.connect(self.pick_border_color)

        text_label = QtWidgets.QLabel("Text:")
        self.text_picker = QtWidgets.QPushButton()
        self.text_picker.setStyleSheet(f"background-color: {text_color if text_color != 'white' else '#fff'}; border: 1px solid #888;")
        self.text_picker.setFixedWidth(40)
        self.text_picker.clicked.connect(self.pick_text_color)

        color_layout.addWidget(bg_label)
        color_layout.addWidget(self.bg_picker)
        color_layout.addSpacing(10)
        color_layout.addWidget(border_label)
        color_layout.addWidget(self.border_picker)
        color_layout.addSpacing(10)
        color_layout.addWidget(text_label)
        color_layout.addWidget(self.text_picker)
        main_layout.addLayout(color_layout)

        transparency_label = QtWidgets.QLabel("Window Transparency: (30-100%)")
        self.transparency_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.transparency_slider.setRange(30, 100)
        self.transparency_slider.setValue(int(parent.windowOpacity() * 100))
        self.transparency_slider.valueChanged.connect(lambda v: parent.setWindowOpacity(v / 100.0))

        hotkey_label = QtWidgets.QLabel("Toggle GUI Keybind: (Use Galaxy Map keybind)")
        self.hotkey_button = QtWidgets.QPushButton(f"{parent.toggle_key}")
        self.hotkey_button.clicked.connect(self.capture_new_hotkey)

        main_layout.addWidget(hotkey_label)
        main_layout.addWidget(self.hotkey_button)
        main_layout.addSpacing(10)
        main_layout.addWidget(transparency_label)
        main_layout.addWidget(self.transparency_slider)

        self._drag_pos = None
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color

    def reset_defaults(self):
        default_bg = "#371e09"
        default_border = "#ff7a00"
        default_text = "white"
        self.bg_color = default_bg
        self.border_color = default_border
        self.text_color = default_text
        self.bg_picker.setStyleSheet(f"background-color: {default_bg}; border: 1px solid #888;")
        self.border_picker.setStyleSheet(f"background-color: {default_border}; border: 1px solid #888;")
        self.text_picker.setStyleSheet(f"background-color: {default_text if default_text != 'white' else '#fff'}; border: 1px solid #888;")
        self.color_changed.emit(default_bg, default_border, default_text)

    def pick_bg_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.bg_color), self, "Select Background Color")
        if color.isValid():
            self.bg_color = color.name()
            self.bg_picker.setStyleSheet(f"background-color: {self.bg_color}; border: 1px solid #888;")
            self.color_changed.emit(self.bg_color, self.border_color, self.text_color)

    def pick_border_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.border_color), self, "Select Border Color")
        if color.isValid():
            self.border_color = color.name()
            self.border_picker.setStyleSheet(f"background-color: {self.border_color}; border: 1px solid #888;")
            self.color_changed.emit(self.bg_color, self.border_color, self.text_color)

    def pick_text_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.text_color), self, "Select Text Color")
        if color.isValid():
            self.text_color = color.name()
            self.text_picker.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #888;")
            self.color_changed.emit(self.bg_color, self.border_color, self.text_color)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        if hasattr(self, 'listening') and self.listening:
            key = event.text() or event.key()
            self.hotkey_changed.emit(str(key))
            self.hotkey_button.setText(str(key))
            self.parent().hotkey_blocked = False
            self.listening = False
            self.hotkey_button.setEnabled(True)

    def capture_new_hotkey(self):
        self.hotkey_button.setText("Listening for key...")
        self.hotkey_button.setEnabled(False)
        self.listening = True
        self.parent().hotkey_blocked = True

def check_system_on_edsm(system_name):
    try:
        response = requests.get(EDSM_API_URL.format(system_name))
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return True, data.get("id", None), response.status_code
        else:
            return False, None, response.status_code
    except Exception as e:
        print(f"Error querying EDSM: {e}")
        return None, None, None

def on_new_system(system_name):
    global last_queried_system
    system_name = system_name.strip()
    if not SYSTEM_NAME_PATTERN.match(system_name):
        print(f"Ignored clipboard text (not a valid system name): '{system_name}'")
        return
    if system_name == last_queried_system:
        return
    last_queried_system = system_name
    print(f"New system detected: {system_name}")
    start_time = datetime.now()
    overlay.loading_active = True
    overlay.current_timing = ""
    overlay.update_display(system_name, False, None)
    visited, system_id, status_code = check_system_on_edsm(system_name)
    elapsed = datetime.now() - start_time
    ms = int(elapsed.total_seconds() * 1000)
    print(f"Response #: {status_code}, {ms} ms")
    overlay.current_timing = f"Response {status_code} : {ms} ms"
    overlay.loading_active = False
    if visited is not None:
        overlay.update_display(system_name, visited, system_id)

# Application Entry Point
app = QtWidgets.QApplication([])
app.setStyleSheet(APP_STYLE)
overlay = Overlay()
overlay.show()
monitor = ClipboardMonitor()
monitor.new_clipboard_text.connect(on_new_system)
monitor.start()
app.exec_()
monitor.stop()
monitor.wait()
overlay.csv_file_handle.close()
