#!/usr/bin/env bash
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}==> Installing Aestra (Competitive Programming Execution Sandbox)${NC}"

PYTHON_BIN=""
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}[X] Python could not be found.${NC}"
    echo -e "Please install Python 3.10 or newer from https://www.python.org or your package manager."
    exit 1
fi

PYTHON_VERSION=$(${PYTHON_BIN} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Detected Python ${PYTHON_VERSION}${NC}"

OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo -e "${GREEN}[✓] Linux / WSL detected — Native POSIX hardware sandbox enabled.${NC}"
        ;;
    Darwin*)
        echo -e "${GREEN}[✓] macOS detected — Cross-platform sandbox enabled.${NC}"
        ;;
    CYGWIN*|MINGW*|MSYS*)
        echo -e "${GREEN}[✓] Windows detected — Native cross-platform subprocess sandbox enabled.${NC}"
        ;;
    *)
        echo -e "${YELLOW}[!] Unknown OS (${OS}) — Attempting cross-platform installation.${NC}"
        ;;
esac

if ! ${PYTHON_BIN} -m pip --version &> /dev/null; then
    echo -e "${YELLOW}[!] pip not found. Bootstrapping with ensurepip...${NC}"
    ${PYTHON_BIN} -m ensurepip --default-pip || true
fi

echo -e "${BLUE}==> Installing Aestra package...${NC}"

if [ -f "pyproject.toml" ] && grep -q "aestra" pyproject.toml 2>/dev/null; then
    ${PYTHON_BIN} -m pip install --quiet --upgrade .
else
    ${PYTHON_BIN} -m pip install --quiet --upgrade aestra 2>/dev/null || \
    ${PYTHON_BIN} -m pip install --quiet --upgrade "git+https://github.com/Elitsuv/aestra.git"
fi

echo ""
echo -e "${BOLD}${GREEN}[✓] Aestra installed successfully!${NC}"
echo -e "${BOLD}Quickstart:${NC}"
echo -e "  Run code safely:   ${BLUE}aestra run ./solution --time-limit 1000 --memory-limit 256${NC}"
echo -e "  Run batch tests:   ${BLUE}aestra test ./solution --cases ./tests/${NC}"
echo ""
