# 📸 Native macOS Batch Image Resizer & Upscaler

Native macOS desktop application optimized for Apple Silicon (M1/M2/M3/M4) to automate batch image upscaling, ratio conversion, and cropping with zero UI latency.

---

### 👤 Author & Maintainer
**Nugi Tiartanto** ([@nugitiar](https://github.com/nugitiar))  
*Informatics Student & Independent Software Developer*

---

## 🌟 Key Features
- **Native Apple Silicon Support (`arm64`)**
- **Multi-threaded GUI:** Built with `CustomTkinter` using Python `threading` to prevent UI lag.
- **ImageMagick Integration:** High-performance CLI backend execution.
- **Aspect Ratio Cropping:** Supports 1:1, 4:3, 3:4, 16:9, and 9:16 presets.
- **Scaling Multipliers:** High-quality 2x, 3x, and 4x upscaling.

## 📖 User Manual & Self-Build Instructions
1. Clone this repository:
   ```bash
   git clone [https://github.com/nugitiar/macos-batch-image-resizer.git](https://github.com/nugitiar/macos-batch-image-resizer.git)
   cd macos-batch-image-resizer
   ```

2. Install dependencies:
   ```bash
   brew install imagemagick python-tk
   python3 -m venv venv
   source venv/bin/activate
   pip install customtkinter pillow pyinstaller
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Compile `.app` bundle:
   ```bash
   chmod +x build_app.sh
   ./build_app.sh
   ```

---

## 📄 License & Distribution Notice

Copyright © 2026 **Nugi Tiartanto**. All rights reserved.

- **Source Code:** Available under personal and educational use terms.
- **Pre-Compiled Binaries:** Subject to controlled distribution terms. Please contact the author via LinkedIn or direct message for access to pre-built executable `.app` bundles.
