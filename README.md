# CH3X's EDSM Toolkit Interface (CETI)

**Version:** 1.1  
**Author:** CH3X  
**Purpose:** Overlay tool for Elite: Dangerous that checks system visitation status via the EDSM API.

---

## 🚀 Features

- 📋 Monitors clipboard for system names copied from the Galaxy Map.
- 🔍 Queries the [EDSM](https://www.edsm.net/) API for visitation status.
- ✅ Displays status (Visited / Not Visited) in a minimalist overlay.
- 💾 Saves system data (visited or not) to a local CSV, including manual XYZ entry for unvisited systems.
- 🌐 Opens EDSM links in the browser for visited systems.
- 🗗 Reset window size.
- ⚙️ Settings menu for:
  - Window transparency
  - Custom hotkey binding
  - Color scheme (background, border, text)
  - Quick access to GitHub
  - Reset to default settings
- 🔎 "Find Nearby" tool to search for visited systems near a set of coordinates.
- Always-on-top overlay with draggable, resizable interface.

---

## 🖱 Usage

1. Launch CETI.
2. Configure the keybind to match your Galaxy Map key in-game.
3. The overlay will:
   - Detect system names when copied to clipboard
   - Query EDSM
   - Show the status (Visited/Not Visited)
   - Toggle visibility on keybind
4. Use the 💾 button to save system data (works for both visited and unvisited systems).
   - For unvisited systems, you will be prompted to enter XYZ coordinates.
5. Use the "Find Nearby" button to search for visited systems near a set of coordinates (Target focus and use the Galaxy Map grid).

---

## 🗃 Output CSV Format

Saved to: `CETIv1.1_saved_systems.csv`

| Column           | Description                                 |
|------------------|---------------------------------------------|
| System Name      | Name of the star system                     |
| Status           | Visited / Not Visited                       |
| Time Saved       | Local time the data was saved               |
| EDSM Link        | Direct link to the EDSM system page or "N/A"|
| XYZ              | Comma-separated X, Y, Z coordinates         |
| BackgroundColor  | Overlay background color (config row only)  |
| BorderColor      | Overlay border color (config row only)      |
| TextColor        | Overlay text color (config row only)        |
| Keybind          | Overlay toggle keybind (config row only)    |

- **Note:** The second row in the CSV always holds the current configuration for colors and keybind. System data rows only fill the first five columns.

---

## 🧩 Hotkeys

| Function        | Default Key |
|-----------------|-------------|
| Toggle Overlay  |     `/`     |

You can customize this in the ⚙️ Settings menu.

---

## 🛠 Requirements

- **If you are using the packaged `.exe` version, no dependencies or Python installation are required.**
- If you are running from source, you need:
  - Python 3.8+
  - `PyQt5`, `pyperclip`, `requests`, `keyboard`

Install dependencies with:

```bash
pip install pyqt5 pyperclip requests keyboard
```

**Important:**  
The `.exe` or Python script **must be located in the same folder as the `CETIv1.1_saved_systems.csv` file**.  
For best results, keep all files together in a dedicated folder.

---

## 📝 Additional Notes

- The overlay can be moved by dragging and resized with the 🗗 button.
- The settings menu allows you to change the overlay's color scheme and reset to defaults.
- The "GH" button in settings opens the GitHub repository.
- The "R" button in settings resets all overlay colors and keybind to defaults.
- Saving an unvisited system will prompt you for XYZ coordinates, which are stored in the CSV.
- The overlay always stays on top for easy reference while playing.

---
