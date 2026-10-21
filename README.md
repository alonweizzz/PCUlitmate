# PCULTIMATE

![PCULTIMATE logo](assets/pcultimate-logo.svg)

![PCULTIMATE app icon](assets/pcultimate-icon.svg)


Windows 10/11 desktop PC dashboard, version 0.1.0.

## Features
- Live CPU, RAM and system-drive usage, refreshed every 2 seconds
- PC name, CPU, graphics card, RAM, cores, architecture, OS and boot time
- Buttons to open Task Manager, Windows Settings and Device Manager
- Dark-mode UI; local-only monitoring, no sign-in

## Run source
Install Python 3.11+ and run:
```powershell
py -m pip install -r requirements.txt
py pcultimate.py
```

## Download Windows EXE
Go to [Actions](../../actions/workflows/build-windows.yml), open a successful **Build Windows EXE** run, and download the `PCULTIMATE-Windows` artifact ZIP. Extract `PCULTIMATE.exe`. This build is unsigned and Windows may warn about an unknown publisher.

## Build locally
```powershell
py -m PyInstaller --noconfirm --clean --onefile --windowed --name PCULTIMATE pcultimate.py
```
Output: `dist/PCULTIMATE.exe`.

## Planned updates
Process monitor, GPU and temperature data (when available), performance charts, and Hebrew UI.
