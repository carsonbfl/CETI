from PyQt5 import QtWidgets
from gui.overlay import Overlay
from core.monitor import JournalMonitor
from core.edsm import check_system_on_edsm
from core.edastro import check_system_on_edastro
from core.spansh import check_system_on_spansh
from core.constants import EDSM_SYSTEM_URL, EDASTRO_API_URL, SPANSH_SYSTEM_URL
from config.style import APP_STYLE
import datetime


last_queried_system = None

def on_new_system(system_name, system_address):
    global last_queried_system
    system_name = system_name.strip()
    if system_name == last_queried_system:
        return
    last_queried_system = system_name
    print(f"New system detected: {system_name}")
    
    overlay.loading_active = True
    overlay.update_display(system_name, False, None)

    edsm_start = datetime.datetime.now()
    edsm_visited, _, edsm_status = check_system_on_edsm(system_name)
    edsm_elapsed = datetime.datetime.now() - edsm_start
    edsm_ms = int(edsm_elapsed.total_seconds() * 1000)

    edastro_start = datetime.datetime.now()
    edastro_visited, edastro_url, edastro_status = check_system_on_edastro(system_name)
    edastro_elapsed = datetime.datetime.now() - edastro_start
    edastro_ms = int(edastro_elapsed.total_seconds() * 1000)

    spansh_url = SPANSH_SYSTEM_URL.format(str(system_address))
    spansh_status = 200  # always 200 as it's just a URL
    spansh_visited = False  # Spansh does not report visited status

    print(f"[EDSM] Response: {edsm_status} in {edsm_ms} ms")
    print(f"[EDASTRO] Response: {edastro_status} in {edastro_ms} ms")
    print(f"[SPANSH] Response: {spansh_status} (link only)")

    overlay.loading_active = False

    combined_timing = f"Response: {'Yes' if edsm_visited else 'No'} | {edsm_ms} ms"

    visited = bool(edsm_visited or edastro_visited or spansh_visited)


    urls = {
        "edsm": EDSM_SYSTEM_URL.format(system_name),
        "edastro": EDASTRO_API_URL.format(system_name),
        "spansh": spansh_url
    }

    overlay.update_display(system_name, visited, None, timing_info=combined_timing, urls=urls)

def on_galmap_open():
    if overlay.visibility_tied_to_map:
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()

def on_galmap_close():
    if overlay.visibility_tied_to_map:
        overlay.hide()

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
