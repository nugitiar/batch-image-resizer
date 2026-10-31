# macOS Batch Image Resizer & Upscaler (Apple Silicon arm64)

[![Platform](https://img.shields.io/badge/Platform-macOS%20Apple%20Silicon%20(arm64)-000000.svg?logo=apple&style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&style=flat-square)](#)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg?style=flat-square)](#)
[![Engine](https://img.shields.io/badge/Engine-ImageMagick%207-orange.svg?style=flat-square)](#)

A high-performance, native desktop application engineered for Apple Silicon (M1/M2/M3/M4) that automates batch image upscaling, aspect ratio center-cropping, and quality resampling using Python and the native ImageMagick CLI engine.

Designed to replace cumbersome Terminal scripts with an intuitive, modern macOS desktop experience.

---

## Key Features

- **Multi-Threaded Concurrency**: Employs an asynchronous `concurrent.futures.ThreadPoolExecutor` background worker architecture. Prevents GUI freezes, utilizes Apple Silicon Performance and Efficiency cores, and provides instantaneous cancellation.
- **Modern CustomTkinter GUI**: Native macOS aesthetic featuring smooth typography, high-contrast indicators, and automatic synchronization with macOS Dark and Light appearance modes.
- **High-Performance ImageMagick CLI Engine**: Automatically discovers native Apple Silicon binaries (`/opt/homebrew/bin/magick`), probing image dimensions with `magick identify` and invoking safe argument arrays without shell injection vulnerabilities.
- **Scale Multipliers**:
  - `1x`: Original scale (Aspect ratio crop only)
  - `2x`: 200% Upscale
  - `3x`: 300% Upscale
  - `4x`: 400% Upscale
- **Aspect Ratio Presets (Zero-Distortion Center-Crop)**:
  - `Original Ratio`: No cropping, pure resampling/scaling
  - `Square (1:1)`: Instagram / Avatar standard
  - `Landscape (4:3)`: Traditional photography / Tablet display
  - `Portrait (3:4)`: Mobile portrait format
  - `Widescreen (16:9)`: YouTube / Desktop wallpaper / HD standard
  - `Vertical (9:16)`: TikTok / Instagram Reels / YouTube Shorts
- **Quality Resampling Algorithms**:
  - `Lanczos`: Sinc-windowed filter offering exceptional sharpness and high detail retention for upscaling.
  - `Cubic / Bicubic`: Smooth photographic transitions with reduced aliasing.
  - `Mitchell`: Balanced cubic filter minimizing edge-ringing artifacts.
  - `Catrom`: Sharp Catmull-Rom cubic spline interpolation.
  - `Triangle`: Fast linear resampling.
  - `Point`: Nearest-neighbor interpolation ideal for pixel art and crisp integer scaling.
- **File Management & Drag-and-Drop**:
  - Drag-and-drop support for folders or multiple images.
  - Supports `.jpg`, `.jpeg`, `.png`, `.webp`, `.tiff`, `.heic`, and `.bmp`.
  - Output formats: Original format, Lossless PNG, Standard JPEG, or Modern WebP.
- **Live Activity Console & Progress Feedback**: Real-time progress bar, percentage indicator, ETA countdown timer, and scrollable activity log with timestamps.
- **Finder Integration**: One-click "Reveal in Finder" button to open processed results directly in macOS Finder.

---

## System Requirements

- **Operating System**: macOS 11.0 (Big Sur) or newer.
- **Architecture**: Apple Silicon (`arm64` — M1, M2, M3, M4 series).
- **Core Dependencies**: Homebrew, Python 3.10+, and ImageMagick 7.

---

## Self-Build Instructions

Follow these steps to set up the environment and compile the application from source code.

### 1. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd macos-batch-resizer
```

### 2. Environment Setup (Automated)

Run the included Apple Silicon automated configuration script:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

### 3. Environment Setup (Manual)

If you prefer configuring your environment manually:

```bash
# 1. Install ImageMagick and Python Tkinter formula via Homebrew
brew install imagemagick python python-tk

# 2. Create and activate a clean arm64 virtual environment
/opt/homebrew/bin/python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install pinned Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application in Development Mode

```bash
source venv/bin/activate
python3 src/main.py
```

### 5. Execute Test Suite

Run the unit and end-to-end integration tests:

```bash
python3 -m unittest discover -s tests -v
```

### 6. Compile Standalone `.app` Bundle

To package the application into a standalone macOS `.app` bundle optimized for Apple Silicon:

```bash
chmod +x build_app.sh
./build_app.sh
```

The build script will:
1. Bundle assets and code using PyInstaller (`mac_resizer.spec`) targeting `arm64`.
2. Configure macOS `Info.plist` for Retina resolution (`NSHighResolutionCapable`) and native Dark Mode (`NSRequiresAquaSystemAppearance`).
3. Apply required ad-hoc code signature (`codesign --force --deep --sign -`).
4. Strip extended quarantine attributes (`xattr -cr`).
5. Output the distribution bundle to:
   - `dist/Batch Image Resizer.app`
   - `dist/Batch-Image-Resizer-macOS-arm64.zip`

To launch your compiled app directly:
```bash
open "dist/Batch Image Resizer.app"
```

---

## Distribution Notice & Limited Binary Access

> [!IMPORTANT]
> **Source Code & Binary Policy**
> 
> - **Source Code**: You are free to clone, inspect, modify, and build this software from the source code for personal, research, or non-commercial use following the repository guidelines.
> - **Pre-Compiled Binaries**: Pre-built, notarized standalone `.app` bundles are distributed exclusively upon private request. If you require access to an official pre-compiled `.app` installer without building it locally, please contact the repository maintainer directly via **Private Message**.

---

## Architecture & Codebase Map

```
macos-batch-resizer/
├── README.md                 # Complete documentation and build guide
├── requirements.txt          # Python runtime dependencies
├── setup_env.sh              # Automated Apple Silicon environment setup
├── build_app.sh              # PyInstaller arm64 compilation and signing script
├── mac_resizer.spec          # PyInstaller bundle specification with Info.plist
├── .gitignore                # Ignore rules for OS, bytecode, and build artifacts
├── src/
│   ├── main.py               # Main application entry point & Retina initialization
│   ├── core/
│   │   ├── config.py         # Data models, aspect ratio definitions, and filters
│   │   ├── detector.py       # ImageMagick discovery (/opt/homebrew/bin/magick)
│   │   ├── processor.py      # Center-crop math and safe subprocess argument generator
│   │   └── worker.py         # Multi-threaded background job worker & cancellation
│   └── ui/
│       ├── app_window.py     # CustomTkinter macOS GUI window layout
│       ├── components.py     # DropZone, StatBadge, and LogViewer widgets
│       └── dnd_handler.py    # Drag-and-drop parsing with TkinterDnD fallback
└── tests/
    └── test_processor.py     # Unit test suite & live ImageMagick conversions
```

---

## License

Copyright © 2026. All rights reserved. Source code available under personal and educational use terms. See [Distribution Notice](#distribution-notice--limited-binary-access) for pre-compiled binary distribution terms.
