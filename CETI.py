from PyQt5 import QtWidgets
from gui.overlay import Overlay
from core.monitor import JournalMonitor
from core.edsm import check_system_on_edsm
from config.style import APP_STYLE
import datetime

last_queried_system = None

def on_new_system(system_name):
    global last_queried_system
    system_name = system_name.strip()
    if system_name == last_queried_system:
        return
    last_queried_system = system_name
    print(f"New system detected: {system_name}")
    start_time = datetime.datetime.now()
    overlay.loading_active = True
    overlay.current_timing = ""
    overlay.update_display(system_name, False, None)
    visited, system_id, status_code = check_system_on_edsm(system_name)
    elapsed = datetime.datetime.now() - start_time
    ms = int(elapsed.total_seconds() * 1000)
    print(f"Response #: {status_code}, {ms} ms")
    overlay.current_timing = f"Response {status_code} : {ms} ms"
    overlay.loading_active = False
    if visited is not None:
        overlay.update_display(system_name, visited, system_id)

def on_galmap_open():
    if overlay.visibility_tied_to_map:
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()

def on_galmap_close():
    if overlay.visibility_tied_to_map:
        overlay.hide()

# --- Qt App Initialization ---
app = QtWidgets.QApplication([])
app.setStyleSheet(APP_STYLE)

overlay = Overlay()
if overlay.visibility_tied_to_map:
    overlay.hide()
else:
    overlay.show()

monitor = JournalMonitor()
monitor.new_targeted_system.connect(on_new_system)
monitor.galmap_opened.connect(on_galmap_open)
monitor.galmap_closed.connect(on_galmap_close)

monitor.start()

app.exec_()
monitor.stop()
monitor.wait()
overlay.csv_file_handle.close()
