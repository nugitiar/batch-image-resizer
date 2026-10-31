#!/usr/bin/env bash
# ==============================================================================
# Setup Environment for macOS Apple Silicon (arm64 - M1/M2/M3/M4)
# Batch Image Upscaler & Resizer Desktop App
# ==============================================================================

set -euo pipefail

# ANSI Color Codes
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE} macOS Apple Silicon (arm64) Environment Setup        ${RESET}"
echo -e "${BOLD}${BLUE} Batch Image Upscaler & Resizer Desktop App           ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}"

# 1. Architecture Verification
ARCH=$(uname -m)
echo -e "\n${BOLD}[1/5] Checking Processor Architecture...${RESET}"
if [[ "$ARCH" == "arm64" ]]; then
    echo -e "${GREEN}✓ Native Apple Silicon detected: ${ARCH} (M1/M2/M3/M4)${RESET}"
else
    echo -e "${YELLOW}! Detected architecture: ${ARCH}. Script will proceed, but arm64 optimizations are recommended.${RESET}"
fi

# 2. Homebrew Verification
echo -e "\n${BOLD}[2/5] Checking Homebrew Package Manager...${RESET}"
BREW_PREFIX="/opt/homebrew"

if [[ -f "${BREW_PREFIX}/bin/brew" ]]; then
    eval "$(${BREW_PREFIX}/bin/brew shellenv)"
    echo -e "${GREEN}✓ Homebrew is installed at ${BREW_PREFIX}${RESET}"
elif command -v brew &>/dev/null; then
    echo -e "${GREEN}✓ Homebrew found in PATH: $(which brew)${RESET}"
else
    echo -e "${RED}✗ Homebrew not found!${RESET}"
    echo -e "  Install Homebrew by running the following in your terminal:"
    echo -e "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 3. Native CLI Tools & ImageMagick Installation
echo -e "\n${BOLD}[3/5] Verifying System Dependencies (ImageMagick & Python Tkinter)...${RESET}"

# Check ImageMagick
if ! command -v magick &>/dev/null && ! [[ -f "/opt/homebrew/bin/magick" ]]; then
    echo -e "${YELLOW}→ ImageMagick is not installed. Installing via Homebrew...${RESET}"
    brew install imagemagick
else
    MAGICK_BIN=$(command -v magick || echo "/opt/homebrew/bin/magick")
    echo -e "${GREEN}✓ ImageMagick detected at: ${MAGICK_BIN}${RESET}"
    $MAGICK_BIN -version | head -n 1
fi

# Check / Install Python & python-tk
# NOTE: On Apple Silicon Homebrew, Python requires 'python-tk' formula for Tkinter GUI support
echo -e "${BLUE}→ Ensuring Python and Tkinter formulas are installed...${RESET}"
brew install python python-tk 2>/dev/null || true

# 4. Virtual Environment Creation
echo -e "\n${BOLD}[4/5] Setting up Python arm64 Virtual Environment...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

if [[ -d "$VENV_DIR" ]]; then
    echo -e "${BLUE}→ Existing virtual environment detected at ${VENV_DIR}.${RESET}"
else
    echo -e "${BLUE}→ Creating virtual environment at ${VENV_DIR}...${RESET}"
    # Prefer Homebrew's native arm64 python3
    if [[ -x "/opt/homebrew/bin/python3" ]]; then
        /opt/homebrew/bin/python3 -m venv "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
fi

# Activate venv
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

VENV_PYTHON="${VENV_DIR}/bin/python3"
VENV_ARCH=$($VENV_PYTHON -c "import platform; print(platform.machine())")
echo -e "${GREEN}✓ Virtual environment active with Python ${VENV_ARCH}${RESET}"

# 5. Installing Pip Dependencies
echo -e "\n${BOLD}[5/5] Installing Python Dependencies from requirements.txt...${RESET}"
pip install --upgrade pip setuptools wheel
pip install -r "${SCRIPT_DIR}/requirements.txt"

# 6. Self-Test Diagnostic
echo -e "\n${BOLD}======================================================${RESET}"
echo -e "${BOLD} Running System Verification Self-Test                ${RESET}"
echo -e "${BOLD}======================================================${RESET}"

python3 - << 'EOF'
import sys
import platform

print(f"Python Executable: {sys.executable}")
print(f"Python Version:    {sys.version.split()[0]}")
print(f"Architecture:      {platform.machine()} ({sys.byteorder}-endian)")

try:
    import tkinter
    print(f"Tkinter:           Available (Tcl/Tk {tkinter.TkVersion})")
except Exception as e:
    print(f"Tkinter:           ERROR - {e}")
    print("  TIP: Run 'brew install python-tk' to fix Tkinter on macOS Homebrew Python.")

try:
    import customtkinter
    print(f"CustomTkinter:     Available (v{customtkinter.__version__})")
except Exception as e:
    print(f"CustomTkinter:     ERROR - {e}")

try:
    import PIL
    print(f"Pillow (PIL):      Available (v{PIL.__version__})")
except Exception as e:
    print(f"Pillow:            ERROR - {e}")

try:
    from src.core.detector import ImageMagickDetector
    detector = ImageMagickDetector()
    info = detector.get_info()
    if info.is_available:
        print(f"ImageMagick:       Detected at {info.binary_path} (Version: {info.version_string})")
    else:
        print(f"ImageMagick:       NOT FOUND - {info.error_message}")
except Exception as e:
    print(f"ImageMagick Check: Skipping module check ({e})")
EOF

echo -e "\n${BOLD}${GREEN}✔ Setup complete!${RESET}"
echo -e "To launch the app:"
echo -e "  source venv/bin/activate"
echo -e "  python3 src/main.py"
