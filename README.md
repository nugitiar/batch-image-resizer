# 📸 Cross-Platform Batch Image Resizer & Upscaler

[![License](https://img.shields.io/badge/License-Copyright%20%C2%A9%202026%20Nugi%20Tiartanto-blue.svg?style=flat-square)](#author--maintainer)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg?style=flat-square)](#system-requirements--installation)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&style=flat-square)](#)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg?style=flat-square)](#)
[![Engine](https://img.shields.io/badge/Engine-ImageMagick%207-orange.svg?style=flat-square)](#)

A high-performance, cross-platform desktop application designed to run seamlessly on **Windows**, **macOS**, and **Linux**. It automates batch image upscaling, aspect ratio center-cropping, and quality resampling using Python and the native ImageMagick CLI engine (`magick`, `magick.exe`, or `convert`).

Engineered with asynchronous multi-threading, modern Dark/Light mode customization, and non-blocking background workers.

---

## 👨‍💻 Author & Maintainer

- **Name**: **Nugi Tiartanto** ([@nugitiar](https://github.com/nugitiar))
- **Role**: Informatics Student & Software Creator
- **Project Repository**: [`batch-image-resizer`](https://github.com/nugitiar/batch-image-resizer)

---

## 🚀 Key Features

- **Cross-Platform Compatibility**: Native support and OS auto-detection for **Windows** (x64/ARM64), **macOS** (Apple Silicon M1/M2/M3/M4 & Intel), and **Linux** (Debian, Ubuntu, Arch, Fedora).
- **Multi-Threaded Concurrency**: Employs an asynchronous `concurrent.futures.ThreadPoolExecutor` worker architecture. Ensures the CustomTkinter GUI never freezes during heavy batch jobs, supports instant cancellation, and optimizes CPU core utilization.
- **ImageMagick CLI Engine**: Automatically discovers local ImageMagick binaries (`magick`, `magick.exe`, `convert`), probes dimensions via `magick identify`, and invokes safe argument lists (`List[str]`) avoiding shell injection vulnerabilities.
- **Windows Silent Processing**: Configured with `subprocess.CREATE_NO_WINDOW` on Windows to eliminate command prompt window popups during batch runs.
- **Scale Multipliers**:
  - `1x`: Original scale (Aspect ratio crop only)
  - `2x`: 200% Upscale
  - `3x`: 300% Upscale
  - `4x`: 400% Upscale
- **Aspect Ratio Presets (Zero-Distortion Center-Crop)**:
  - `Original Ratio`: No cropping, pure scale/resample
  - `Square (1:1)`: Instagram / Profile picture standard
  - `Landscape (4:3)`: Traditional photography / Tablet display
  - `Portrait (3:4)`: Mobile vertical format
  - `Widescreen (16:9)`: YouTube / Wallpaper / 1080p / 4K standard
  - `Vertical (9:16)`: TikTok / Instagram Reels / YouTube Shorts
- **Quality Resampling Algorithms**:
  - `Lanczos`: Sinc-windowed filter offering sharp details and high retention for upscaling.
  - `Cubic / Bicubic`: Smooth photographic transitions with reduced aliasing.
  - `Mitchell`: Balanced cubic filter minimizing edge-ringing artifacts.
  - `Catrom`: Sharp Catmull-Rom cubic spline interpolation.
  - `Triangle`: Fast linear resampling.
  - `Point`: Nearest-neighbor interpolation ideal for pixel art and crisp integer scaling.
- **Intuitive File Management & Drag-and-Drop**:
  - Full Drag-and-Drop support for folders and multiple image files across all operating systems.
  - Supported input formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.tiff`, `.heic`, and `.bmp`.
  - Output formats: Original format, Lossless PNG, Standard JPEG, or Modern WebP.
- **Live Activity Console & Progress Feedback**: Real-time progress bar, percentage indicator, ETA countdown timer, and scrollable activity log.
- **OS-Responsive File Manager Integration**: One-click button to reveal output directly in macOS Finder, Windows File Explorer, or Linux File Manager.

---

## 🛠️ System Requirements & Installation

ImageMagick 7 and Python 3.10+ are required. Follow the instructions for your operating system:

### 1. macOS (Apple Silicon & Intel)

#### Install Dependencies via Homebrew:
```bash
brew install imagemagick python python-tk
```
*(Note: `python-tk` is required on Homebrew Python for Tkinter GUI support).*

#### Setup Virtual Environment & Run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 src/main.py
```

---

### 2. Windows 10 / 11 (x64 & ARM64)

#### Install ImageMagick via Winget:
Open PowerShell or Command Prompt:
```powershell
winget install ImageMagick.ImageMagick
```
*Alternatively, download the official Windows installer from [ImageMagick.org](https://imagemagick.org/script/download.php) (make sure to check "Add to system PATH" during installation).*

#### Setup Virtual Environment & Run:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python src\main.py
```

---

### 3. Linux (Debian, Ubuntu, Arch, Fedora)

#### Install Dependencies via Package Manager:

- **Debian / Ubuntu / Linux Mint**:
  ```bash
  sudo apt update
  sudo apt install -y imagemagick python3-tk python3-pip python3-venv
  ```

- **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -S imagemagick tk python-pip
  ```

- **Fedora / RHEL**:
  ```bash
  sudo dnf install -y ImageMagick python3-tkinter python3-pip
  ```

#### Setup Virtual Environment & Run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 src/main.py
```

---

## 🧪 Running Automated Tests

A comprehensive unit test suite is included to verify aspect ratio math, command argument generation, and cross-platform installation hint detection:

```bash
# macOS & Linux:
python3 -m unittest discover -s tests -v

# Windows:
python -m unittest discover -s tests -v
```

---

## 📦 Standalone Binary Compilation (Self-Build)

You can compile the application into a standalone binary on your host platform using PyInstaller:

### On macOS (arm64 / x86_64 `.app` Bundle):
```bash
chmod +x build_app.sh
./build_app.sh
```
*Outputs: `dist/Batch Image Resizer.app` and `dist/Batch-Image-Resizer-macOS-arm64.zip`.*

### On Windows (`.exe` Standalone):
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "Batch-Image-Resizer" --add-data "venv\Lib\site-packages\customtkinter;customtkinter" src\main.py
```
*Outputs: `dist\Batch-Image-Resizer\Batch-Image-Resizer.exe`.*

### On Linux (ELF Binary):
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "Batch-Image-Resizer" --add-data "$(python3 -c 'import customtkinter, os; print(os.path.dirname(customtkinter.__file__))'):customtkinter" src/main.py
```
*Outputs: `dist/Batch-Image-Resizer/Batch-Image-Resizer`.*

---

## 🔒 Distribution Notice & Limited Binary Access

> [!IMPORTANT]
> **Source Code & Binary Policy**
> 
> - **Source Code Freedom**: You are completely free to clone, inspect, modify, and build this software from source code for personal, research, or non-commercial use.
> - **Pre-Compiled Executables**: Pre-built, notarized standalone `.app` and `.exe` binaries are distributed exclusively upon private request. If you require access to an official pre-compiled installer without building it locally, please contact **Nugi Tiartanto** directly via **Private Message** on GitHub ([@nugitiar](https://github.com/nugitiar)).

---

## 📂 Project Architecture

```
batch-image-resizer/
├── README.md                 # Complete cross-platform documentation
├── requirements.txt          # Python runtime dependencies
├── setup_env.sh              # Environment setup script for Unix/macOS
├── build_app.sh              # macOS packaging script with ad-hoc signing
├── mac_resizer.spec          # PyInstaller bundle specification
├── .gitignore                # Ignore rules for OS, bytecode, and build artifacts
├── src/
│   ├── main.py               # Main application entry point & OS platform detector
│   ├── core/
│   │   ├── config.py         # Data models, aspect ratio presets, and filters
│   │   ├── detector.py       # Cross-platform ImageMagick discovery engine
│   │   ├── processor.py      # Center-crop math and safe subprocess argument builder
│   │   └── worker.py         # Thread-safe multi-threaded background worker
│   └── ui/
│       ├── app_window.py     # CustomTkinter GUI window layout & OS integration
│       ├── components.py     # DropZone, StatBadge, and LogViewer widgets
│       └── dnd_handler.py    # Cross-platform drag-and-drop path parser
└── tests/
    └── test_processor.py     # Unit test suite & integration verification
```

---

## 📄 License & Copyright

**Copyright © 2026 Nugi Tiartanto ([@nugitiar](https://github.com/nugitiar)). All rights reserved.**

Developed with precision by **Nugi Tiartanto**, Informatics Student & Software Creator.
See the [Distribution Notice](#-distribution-notice--limited-binary-access) for pre-compiled binary distribution terms.
