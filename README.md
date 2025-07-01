# Ch3x's Exploration Toolkit Interface (CETI)

**Version:** 1.3
**Author:** CH3X
**Purpose:** Minimalist overlay utility for Elite: Dangerous, focused on exploration tools including system status checking, map-linked display, and data recording.

---

## 🚀 Features

* 📅 **Monitors the Elite Dangerous Player Journal** 
  * Tracks when the Galaxy Map is opened or closed for display visibility
  * Detects when a system is targeted. (Next in route or just target)

* 🔍 Queries the [EDSM](https://www.edsm.net/) API for visitation status
* ✅ Displays system status (Visited / Not Visited) in a compact overlay
* 📂 (Optional) Saves system data to a local CSV with optional XYZ coordinates
* 🔐 System tray integration

  * Always-running tray icon with restore and exit options
  * Overlay can be hidden but remains active
* 📁 "Find Nearby" tool for locating visited systems near coordinates (searches ONLY off of coords, reference name is disregarded)
* 🔹 Quick access to EDSM page for visited systems
* ⚙️ Settings menu for:

  * Overlay transparency
  * Color theme (background, border, text)
  * Reset to defaults
  * GitHub link
  * Visivibility Toggle
  * Window Size

---

## 💪 How It Works

1. Launch CETI.
2. The overlay starts hidden if Galaxy Map detection is enabled and Galaxy Map is open.
3. CETI monitors your Player Journal for:

   * **GalaxyMap** to determine when to show/hide overlay.
4. When a system is targeted:

   * CETI queries the EDSM API
   * Displays status and enables options
5. Use the 📂 button to save system data (manual XYZ for unvisited)
6. Use "Find Nearby" to search visited systems around user-defined coordinates. (Mostly useful for unvisited systems, does not pull targeted system but instead prompts the user for coordinates, the name is irrelevant for this. More in future WIP)

---

## 📃 Output CSV Format

Saved to: `CETIv1.3_saved_systems.csv`

| Column          | Description                                |
| --------------- | ------------------------------------------ |
| System Name     | Name of the star system                    |
| Status          | Visited / Not Visited                      |
| Time Saved      | Local time the data was saved              |
| EDSM Link       | Direct link to EDSM system page or "N/A"   |
| XYZ             | Manually entered coordinates               |
| BackgroundColor | Overlay background color (config row only) |
| BorderColor     | Overlay border color (config row only)     |
| TextColor       | Overlay text color (config row only)       |
| MapVisibility   | True / False for map-triggered visibility  |

* **Note:** Second row stores the current overlay configuration.

---

## 🚪 System Tray Behavior

* CETI runs as a tray application.
* Right-click the tray icon to:

  * Show/restore the overlay
  * Exit the applicaton
