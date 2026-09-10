#!/usr/bin/env bash
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m'

echo ""
echo -e "${CYAN}  ┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}  │  AESTRA  ·  Competitive Programming Execution Sandbox      │${NC}"
echo -e "${CYAN}  └─────────────────────────────────────────────────────────────┘${NC}"
echo ""

PYTHON_BIN=""
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}  [X] Python could not be found.${NC}"
    echo -e "      Please install Python 3.10 or newer from https://www.python.org or your package manager."
    exit 1
fi

PYTHON_VERSION=$(${PYTHON_BIN} -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}  [✓] Python ${PYTHON_VERSION} detected${NC}"

INSTALL_DIR="$HOME/.aestra"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if [ -f "pyproject.toml" ] && grep -q "aestra" pyproject.toml 2>/dev/null; then
    REPO_ROOT="$(pwd)"
else
    if command -v git &> /dev/null; then
        if [ -d "$INSTALL_DIR/.git" ]; then
            echo -e "${CYAN}  [*] Updating Aestra in $INSTALL_DIR...${NC}"
            git -C "$INSTALL_DIR" pull --quiet
        else
            echo -e "${CYAN}  [*] Cloning Aestra repository into $INSTALL_DIR...${NC}"
            git clone --depth 1 --quiet https://github.com/Elitsuv/aestra.git "$INSTALL_DIR"
        fi
    else
        echo -e "${CYAN}  [*] Downloading Aestra archive...${NC}"
        curl -sSL https://github.com/Elitsuv/aestra/archive/refs/heads/main.tar.gz | tar -xz -C "$INSTALL_DIR" --strip-components=1
    fi
    REPO_ROOT="$INSTALL_DIR"
fi

cat <<EOF > "$BIN_DIR/aestra"
#!/usr/bin/env bash
export PYTHONPATH="$REPO_ROOT:\$PYTHONPATH"
exec ${PYTHON_BIN} -m src.cli "\$@"
EOF
chmod +x "$BIN_DIR/aestra"

if [ -f "./aestra" ]; then
    chmod +x "./aestra" 2>/dev/null || true
fi

if command -v cargo &> /dev/null; then
    echo -e "${GREEN}  [✓] Rust toolchain detected — Building native POSIX hardware sandbox...${NC}"
    ${PYTHON_BIN} -m pip install --quiet --upgrade maturin 2>/dev/null || true
    (cd "$REPO_ROOT" && ${PYTHON_BIN} -m maturin develop --release 2>/dev/null) || true
else
    echo -e "${GREEN}  [✓] SubprocessEngine ready (Zero compiler required)${NC}"
fi

echo ""
echo -e "${GREEN}  +-------------------------------------------------------------+${NC}"
echo -e "${GREEN}  |  [OK] AESTRA INSTALLED SUCCESSFULLY                         |${NC}"
echo -e "${GREEN}  +-------------------------------------------------------------+${NC}"
echo -e "  Location: ${GRAY}${REPO_ROOT}${NC}"
echo -e "  Command : ${GRAY}'aestra' (available globally in ~/.local/bin)${NC}"
echo ""
echo -e "${YELLOW}  Quickstart:${NC}"
echo -e "    ${CYAN}aestra --help${NC}"
echo -e "    ${CYAN}aestra run ./solution --time-limit 1000 --memory-limit 256${NC}"
echo -e "    ${CYAN}aestra test ./solution --cases ./testcases/${NC}"
echo ""
