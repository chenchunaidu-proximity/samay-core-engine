# Samay Core Engine

A privacy-focused desktop application for automated time tracking and activity monitoring. Built on the ActivityWatch foundation with custom branding and enhanced authentication features.

## Quick Start

<<<<<<< HEAD
### Automated Build (Recommended)

```bash
# For macOS
./build_samay_macos.sh

# For Linux (coming soon)
./build_samay_linux.sh

# For Windows (coming soon)
./build_samay_windows.sh
```

This will create:
- **DMG Installer**: `dist/installers/macos/Samay-YYYYMMDD.dmg` (for macOS users)
- **AppImage**: `dist/installers/linux/Samay-YYYYMMDD.AppImage` (for Linux users)
- **EXE Installer**: `dist/installers/windows/Samay-YYYYMMDD.exe` (for Windows users)

- **App Bundle**: `dist/app/Samay.app` (for development)


## Usage

- **For Users**: Download and install the DMG file
- **For Development**: Use the app bundle directly
=======
1. To setup this create python virtual env using ` python -m venv activity-watch-venv` command
2. cd into `activity-watch-venv`
3. Create `src` folder
4. Activate venv by running `source <PATH_TO_activity-watch-venv_FOLDER>/bin`
5. Clone this repo in src folder
6. You can run build by running `make build` in main folder
7. You build .dmg file by running `make dist/Samay.dmg`
8. It will create dmg file under `dist` folder

## Logs

1. You can check if something is wrong in logs
2. Click on app icon upper bar
3. Click on open log folder
4. It will open a folder with 5 sub folders
5. You can logs in any one of them to check logs
>>>>>>> master
