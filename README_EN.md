# OppoPods-Win

Windows desktop controller for OPPO TWS earphones via Bluetooth RFCOMM protocol.

**Supported Devices**

OPPO Enco Free4 — fully supported (only tested model)

**Features**

Battery display (left / right / case with charging indicator ⚡)

Noise control: Smart, Light, Medium, Deep, Adaptive, Transparency, Off

Master EQ: Authentic, Vocal, Bass, Dynamic

Spatial sound toggle

Game mode toggle

Persistent system tray icon with real-time battery tooltip

Minimize to tray, auto-start on boot

Full tray right-click menu (noise control / EQ / spatial sound / game mode)

**Install**

```bash
pip install -r requirements.txt
python oppopods_ctk.py
```

**Build EXE**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "OppoPods-Win" --icon "tuopan.ico" \
    --add-data "left.png;." --add-data "right.png;." --add-data "cang.png;." \
    --add-data "tuopan.png;." --add-data "tuopandis.png;." oppopods_ctk.py
```

**Usage**

1. Pair OPPO Enco Free4 in Windows Bluetooth settings
2. Run OppoPods-Win.exe, earphones connect automatically
3. Main window shows battery, noise control and EQ controls
4. Right-click tray icon for quick access to all functions
5. Enable "Minimize to tray" to hide on close instead of quit
6. Enable "Auto-start" to launch minimized on boot

**How It Works**

Establishes a Bluetooth RFCOMM connection (channel 15) via WinSock2 AF_BTH socket, using OPPO's proprietary protocol (UUID 0000079A-D102-11E1-9B23-00025B00A5A5). Paired device address is read from registry HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices.

**Credits**

[OppoPods](https://github.com/Leaf-lsgtky/OppoPods) by Leaf-lsgtky — OPPO protocol reverse engineering

[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern Python GUI framework

**License**

GPL-3.0
