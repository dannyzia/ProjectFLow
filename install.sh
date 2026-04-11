#!/usr/bin/env bash
# Project Flow — one-command installer for Linux and macOS
# Usage: curl -fsSL https://raw.githubusercontent.com/dannyzia/ProjectFLow/main/install.sh | bash

set -e

REPO="git+https://github.com/dannyzia/ProjectFLow.git"
VENV_DIR="$HOME/.project-flow-env"
GREEN="\033[0;32m"; YELLOW="\033[0;33m"; RED="\033[0;31m"; NC="\033[0m"

info()    { echo -e "${GREEN}▶${NC} $*"; }
warn()    { echo -e "${YELLOW}!${NC} $*"; }
die()     { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

echo ""
echo "  Project Flow — Installer"
echo "  ────────────────────────"
echo ""

# ── 1. Require Python 3.11+ ──────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.13 python3.12 python3.11 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c 'import sys; print(sys.version_info >= (3,11))' 2>/dev/null)
        if [ "$ver" = "True" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

[ -z "$PYTHON" ] && die "Python 3.11+ is required. Install from https://python.org and try again."
info "Using $(${PYTHON} --version)"

# ── 2. Try pipx (cleanest path) ──────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"

install_via_pipx() {
    if ! command -v pipx &>/dev/null; then
        info "Installing pipx..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y pipx -qq 2>/dev/null || return 1
        elif command -v brew &>/dev/null; then
            brew install pipx -q 2>/dev/null || return 1
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y pipx -q 2>/dev/null || return 1
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python-pipx 2>/dev/null || return 1
        else
            "$PYTHON" -m pip install --user -q pipx 2>/dev/null || return 1
        fi
        export PATH="$HOME/.local/bin:$PATH"
    fi

    command -v pipx &>/dev/null || return 1

    info "Installing project-flow via pipx..."
    pipx install "$REPO" --force -q 2>/dev/null || return 1
    pipx ensurepath --force 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
    return 0
}

# ── 3. Venv fallback (works everywhere, no sudo required) ────────────────────
install_via_venv() {
    info "Installing project-flow into $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q --upgrade pip
    "$VENV_DIR/bin/pip" install -q "$REPO"

    BIN_LINE="export PATH=\"$VENV_DIR/bin:\$PATH\""

    # Append to all common shell RC files (skip if already present)
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
        if [ -f "$rc" ] && ! grep -qF "$VENV_DIR" "$rc"; then
            echo "" >> "$rc"
            echo "# project-flow" >> "$rc"
            echo "$BIN_LINE" >> "$rc"
        fi
    done

    export PATH="$VENV_DIR/bin:$PATH"
}

# ── Run ───────────────────────────────────────────────────────────────────────
if install_via_pipx; then
    METHOD="pipx"
else
    warn "pipx not available — using local venv fallback"
    install_via_venv
    METHOD="venv"
fi

# ── Verify ────────────────────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}✓ project-flow installed successfully!${NC}"
echo ""
echo "  Starting project-flow serve ..."
echo ""

if command -v project-flow &>/dev/null; then
    project-flow serve
elif [ -f "$VENV_DIR/bin/project-flow" ]; then
    "$VENV_DIR/bin/project-flow" serve
else
    warn "Could not find project-flow binary. Restart your terminal and run: project-flow serve"
fi
