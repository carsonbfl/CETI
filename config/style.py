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