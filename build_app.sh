#!/usr/bin/env bash
# ==============================================================================
# Build Standalone macOS .app Bundle for Apple Silicon (arm64)
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE} Compiling macOS Standalone App Bundle (arm64)        ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Activate Virtual Environment if present
if [[ -d "${SCRIPT_DIR}/venv" ]]; then
    echo -e "${BLUE}→ Activating virtual environment...${RESET}"
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/venv/bin/activate"
fi

# 2. Check for PyInstaller
if ! command -v pyinstaller &>/dev/null; then
    echo -e "${RED}✗ PyInstaller is not installed. Run: pip install pyinstaller${RESET}"
    exit 1
fi

# 3. Clean prior build artifacts
echo -e "\n${BOLD}[1/4] Cleaning previous build artifacts...${RESET}"
rm -rf build dist

# Use project-local cache directory for PyInstaller
export PYINSTALLER_CONFIG_DIR="${SCRIPT_DIR}/.pyinstaller_cache"
mkdir -p "$PYINSTALLER_CONFIG_DIR"

# 4. Compile with PyInstaller
echo -e "\n${BOLD}[2/4] Running PyInstaller with mac_resizer.spec...${RESET}"
pyinstaller mac_resizer.spec --noconfirm

APP_PATH="dist/Batch Image Resizer.app"
BINARY_PATH="${APP_PATH}/Contents/MacOS/Batch Image Resizer"

if [[ ! -d "$APP_PATH" ]]; then
    echo -e "${RED}✗ Compilation failed: ${APP_PATH} was not created.${RESET}"
    exit 1
fi

# 5. Architecture Verification
echo -e "\n${BOLD}[3/4] Verifying Apple Silicon Binary Architecture...${RESET}"
ARCH_INFO=$(file "$BINARY_PATH")
echo -e "Binary Info: ${ARCH_INFO}"

if echo "$ARCH_INFO" | grep -q "arm64"; then
    echo -e "${GREEN}✓ Verified native Apple Silicon (arm64) binary.${RESET}"
else
    echo -e "${YELLOW}! Warning: Binary does not appear to be arm64: ${ARCH_INFO}${RESET}"
fi

# 6. Ad-Hoc Code Signing & Quarantine Cleansing
echo -e "\n${BOLD}[4/4] Ad-Hoc Code Signing & Hardening...${RESET}"
# macOS Apple Silicon requires ad-hoc codesigning to execute unsigned local builds
codesign --force --deep --sign - "$APP_PATH"
echo -e "${GREEN}✓ Applied ad-hoc code signature.${RESET}"

# Remove quarantine flags so macOS Gatekeeper allows immediate launch
xattr -cr "$APP_PATH"
echo -e "${GREEN}✓ Cleared quarantine xattrs.${RESET}"

# Create convenient distribution ZIP archive
echo -e "\n${BLUE}→ Packaging distribution archive...${RESET}"
(cd dist && zip -r -q "Batch-Image-Resizer-macOS-arm64.zip" "Batch Image Resizer.app")

echo -e "\n${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN} ✔ Standalone App Bundle Successfully Generated!     ${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}"
echo -e "Application Bundle: ${SCRIPT_DIR}/${APP_PATH}"
echo -e "Distribution Zip:   ${SCRIPT_DIR}/dist/Batch-Image-Resizer-macOS-arm64.zip"
echo -e "\nTo launch the app:"
echo -e "  open \"${APP_PATH}\""
