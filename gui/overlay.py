from PyQt5 import QtWidgets, QtGui, QtCore
from datetime import datetime
import webbrowser, csv, requests, os
from core.constants import EDSM_SYSTEM_URL, SPHERE_SYSTEMS_API_URL, VERSION

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.visibility_tied_to_map = True  
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(f"CETI {VERSION}")
        self.resize(350, 160)
        self.setMinimumSize(100, 100)
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "CETI_logo-export.ico")
        self.tray_icon.setIcon(QtGui.QIcon(icon_path))
        self.tray_icon.setToolTip(f"CETI {VERSION}")

        # Add a menu to the tray icon
        tray_menu = QtWidgets.QMenu()
        restore_action = tray_menu.addAction("Show CETI")
        restore_action.triggered.connect(self.show_overlay_from_tray)

        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.qApp.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.showMessage(
        "CETI Active",
        f"CETI {VERSION} is running.\nRight-click the tray icon to show or exit.",
        QtWidgets.QSystemTrayIcon.Information,
        6000
        )
        self.tray_icon.activated.connect(self.handle_tray_click)

        # State variables
        self.system_id = None
        self.visited = False
        self.last_displayed_system = "N/A"
        self.last_displayed_status = "Not visited"
        self.current_timing = ""
        self.loading_active = False
        self.settings_open = False

        # CSV config and data
        self.bg_color = "#371e09"
        self.border_color = "#ff7a00"
        self.text_color = "white"
        self.csv_file = f"CETI{VERSION}_saved_systems.csv"
        file_exists = os.path.isfile(self.csv_file)
        expected_header = [
            "System Name", "Status", "Time Saved", "EDSM Link", "XYZ",
            "BackgroundColor", "BorderColor", "TextColor", "Keybind", "MapVisibility",
            "Width", "Height"
        ]
        config_loaded = False


        # And update loading logic:
        if file_exists and os.stat(self.csv_file).st_size > 0:
            with open(self.csv_file, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows and rows[0][:10] == expected_header[:10]:  # ignore last column for now
                    if len(rows) > 1:
                        config_row = rows[1]
                        if len(config_row) >= 12:
                            self.bg_color = config_row[5] or self.bg_color
                            self.border_color = config_row[6] or self.border_color
                            self.text_color = config_row[7] or self.text_color
                            # index 8 is old toggle_key — ignored
                            self.visibility_tied_to_map = config_row[9].lower() == "true"
                            try:
                                self.resize(int(config_row[10]), int(config_row[11]))
                            except ValueError:
                                pass

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
                writer.writerow([
                    "", "", "", "", "",
                    self.bg_color, self.border_color, self.text_color,
                    "",  # keybind
                    str(self.visibility_tied_to_map),
                    str(self.width()), str(self.height())
                ])


        self.csv_file_handle = open(self.csv_file, mode="a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file_handle)
        self.apply_style()

        # Layouts and Widgets
        layout = QtWidgets.QVBoxLayout(self)
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel(f"CETI {VERSION}")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        resize_button = QtWidgets.QPushButton("🗗")
        resize_button.setFixedSize(24, 24)
        resize_button.clicked.connect(lambda: self.resize(350, 160))

        close_button = QtWidgets.QPushButton("X")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.hide)


        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(resize_button)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        self.system_label = QtWidgets.QLabel("Greetings CMDR ...")
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

    def handle_tray_click(self, reason):
            if reason == QtWidgets.QSystemTrayIcon.Trigger:
                if self.isVisible():
                    self.hide()
                else:
                    self.show_overlay_from_tray()

    def show_overlay_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()

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
        dlg = SettingsDialog(self, self.bg_color, self.border_color, self.text_color)
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
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)


        layout = QtWidgets.QVBoxLayout(dialog)

        # Title bar
        title_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Enter System Coordinates")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        close_button = QtWidgets.QPushButton("X")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)
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
                 "BackgroundColor", "BorderColor", "TextColor"],
                ["", "", "", "", "", self.bg_color, self.border_color, self.text_color, self.toggle_key, str(self.visibility_tied_to_map)]
            ]
        else:
            rows[1][5:12] = [
            self.bg_color,
            self.border_color,
            self.text_color,
            "",  # placeholder for removed toggle key
            str(self.visibility_tied_to_map),
            str(self.width()),
            str(self.height())
        ]


        with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def update_colors(self, bg_color, border_color, text_color):
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.apply_style()
        self.save_config_to_csv()


    def toggle_visibility(self):
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
    color_changed = QtCore.pyqtSignal(str, str, str)

    def __init__(self, parent, bg_color, border_color, text_color):
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

        self.map_checkbox = QtWidgets.QCheckBox("Only show GUI when Galaxy Map is open")
        self.map_checkbox.setChecked(parent.visibility_tied_to_map)
        self.map_checkbox.stateChanged.connect(lambda state: self.toggle_map_mode(state, parent))
        main_layout.addWidget(self.map_checkbox)

        main_layout.addSpacing(10)
        main_layout.addWidget(transparency_label)
        main_layout.addWidget(self.transparency_slider)

        self._drag_pos = None
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color

        size_layout = QtWidgets.QHBoxLayout()
        width_label = QtWidgets.QLabel("Width:")
        self.width_input = QtWidgets.QSpinBox()
        self.width_input.setRange(100, 2000)
        self.width_input.setValue(parent.width())

        height_label = QtWidgets.QLabel("Height:")
        self.height_input = QtWidgets.QSpinBox()
        self.height_input.setRange(100, 2000)
        self.height_input.setValue(parent.height())

        apply_size_button = QtWidgets.QPushButton("Apply Size")
        apply_size_button.clicked.connect(lambda: parent.resize(
            self.width_input.value(), self.height_input.value()))

        size_layout.addWidget(width_label)
        size_layout.addWidget(self.width_input)
        size_layout.addSpacing(10)
        size_layout.addWidget(height_label)
        size_layout.addWidget(self.height_input)
        size_layout.addSpacing(10)
        size_layout.addWidget(apply_size_button)
        main_layout.addLayout(size_layout)


    def toggle_map_mode(self, state, parent):
        parent.visibility_tied_to_map = bool(state)
        parent.save_config_to_csv()


    def reset_defaults(self):
        default_bg = "#371e09"
        default_border = "#ff7a00"
        default_text = "white"
        default_width = 350
        default_height = 160
        default_map_only = True

        self.bg_color = default_bg
        self.border_color = default_border
        self.text_color = default_text

        self.bg_picker.setStyleSheet(f"background-color: {default_bg}; border: 1px solid #888;")
        self.border_picker.setStyleSheet(f"background-color: {default_border}; border: 1px solid #888;")
        self.text_picker.setStyleSheet(f"background-color: {default_text if default_text != 'white' else '#fff'}; border: 1px solid #888;")
        
        self.color_changed.emit(default_bg, default_border, default_text)
        self.width_input.setValue(default_width)
        self.height_input.setValue(default_height)
        self.map_checkbox.setChecked(default_map_only)

        self.parent().resize(default_width, default_height)
        self.parent().visibility_tied_to_map = default_map_only
        self.parent().save_config_to_csv()


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

    