from PyQt5 import QtCore
import os, glob, json

class JournalMonitor(QtCore.QThread):
    new_targeted_system = QtCore.pyqtSignal(str)
    galmap_opened = QtCore.pyqtSignal()
    galmap_closed = QtCore.pyqtSignal()

    def __init__(self, poll_interval=1000):
        super().__init__()
        self.poll_interval = poll_interval
        self.running = False
        self.last_position = 0
        self.journal_file = None
        self.start_at_end = True
        self.in_galmap = False

    def find_latest_journal(self):
        path = os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous/")
        journal_files = sorted(glob.glob(os.path.join(path, "Journal.*.log")), key=os.path.getmtime, reverse=True)
        return journal_files[0] if journal_files else None

    def run(self):
        self.running = True

        while self.running:
            try:
                latest = self.find_latest_journal()

                # Switch to the latest journal if it changed or was never set
                if latest != self.journal_file:
                    self.journal_file = latest
                    self.last_position = 0
                    self.start_at_end = True
                    if latest:
                        print(f"[JournalMonitor] Switched to new journal: {os.path.basename(latest)}")
                    else:
                        print("[JournalMonitor] No journal file found")

                if not self.journal_file or not os.path.exists(self.journal_file):
                    self.msleep(self.poll_interval)
                    continue

                with open(self.journal_file, "r", encoding="utf-8") as f:
                    if self.start_at_end:
                        f.seek(0, os.SEEK_END)
                        self.last_position = f.tell()
                        self.start_at_end = False
                    else:
                        f.seek(self.last_position)

                    new_lines = f.readlines()
                    self.last_position = f.tell()

                for line in new_lines:
                    try:
                        entry = json.loads(line)
                        event = entry.get("event")

                        if event == "FSDTarget" and "Name" in entry:
                            self.new_targeted_system.emit(entry["Name"])

                        elif event == "Music":
                            track = entry.get("MusicTrack", "")
                            if track == "GalaxyMap" and not self.in_galmap:
                                self.in_galmap = True
                                self.galmap_opened.emit()
                            elif track != "GalaxyMap" and self.in_galmap:
                                self.in_galmap = False
                                self.galmap_closed.emit()

                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                print(f"[JournalMonitor] Error: {e}")

            self.msleep(self.poll_interval)

    def stop(self):
        self.running = False
