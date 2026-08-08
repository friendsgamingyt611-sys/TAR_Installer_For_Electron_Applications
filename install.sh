#!/usr/bin/env bash
# TIFEA Universal Linux Installer
# Installs TIFEA system-wide (root mode) or per-user (non-root mode) on any Linux distribution.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# Determine installation target directories based on privileges
if [[ $EUID -eq 0 ]]; then
    PREFIX="${PREFIX:-/usr/local}"
    BIN_DIR="$PREFIX/bin"
    DATA_DIR="$PREFIX/share"
    MAN_DIR="$DATA_DIR/man/man1"
    BASH_COMP_DIR="/usr/share/bash-completion/completions"
    ZSH_COMP_DIR="/usr/share/zsh/site-functions"
    FISH_COMP_DIR="/usr/share/fish/vendor_completions.d"
    METAINFO_DIR="/usr/share/metainfo"
    
    PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || echo "$PREFIX/lib/python3/dist-packages")
    IS_ROOT=true
    printf '==> Installing TIFEA system-wide (root mode) into %s...\n' "$PREFIX"
else
    PREFIX="${PREFIX:-$HOME/.local}"
    BIN_DIR="$PREFIX/bin"
    DATA_DIR="$PREFIX/share"
    MAN_DIR="$DATA_DIR/man/man1"
    BASH_COMP_DIR="$DATA_DIR/bash-completion/completions"
    ZSH_COMP_DIR="$DATA_DIR/zsh/site-functions"
    FISH_COMP_DIR="$DATA_DIR/fish/vendor_completions.d"
    METAINFO_DIR="$DATA_DIR/metainfo"
    
    PYTHON_SITE=$(python3 -c "import site; print(site.getusersitepackages())" 2>/dev/null || echo "$PREFIX/lib/python3/site-packages")
    IS_ROOT=false
    printf '==> Installing TIFEA for current user into %s...\n' "$PREFIX"
fi

# 1. Create target directories
mkdir -p "$BIN_DIR" "$MAN_DIR" "$BASH_COMP_DIR" "$ZSH_COMP_DIR" "$FISH_COMP_DIR" "$METAINFO_DIR" "$PYTHON_SITE"

# 2. Copy Python modules so tifea can be imported globally
printf '  * Copying TIFEA Python modules to %s...\n' "$PYTHON_SITE"
cp -r "$SCRIPT_DIR/tifea" "$PYTHON_SITE/"
cp -r "$SCRIPT_DIR/targz_installer" "$PYTHON_SITE/" 2>/dev/null || true

# 3. Create standalone CLI binary launcher
printf '  * Installing binary launcher to %s/tifea...\n' "$BIN_DIR"
cat << 'EOF' > "$BIN_DIR/tifea"
#!/usr/bin/env python3
import sys
import os

# Resolve launcher symlinks and site-packages paths
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
parent_dir = os.path.abspath(os.path.join(script_dir, ".."))

for p in [parent_dir, os.path.join(parent_dir, "lib", "python3", "site-packages"), os.path.join(parent_dir, "lib")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from tifea.cli import main

if __name__ == "__main__":
    sys.exit(main() or 0)
EOF

chmod 755 "$BIN_DIR/tifea"
ln -sf "$BIN_DIR/tifea" "$BIN_DIR/tifiea"
ln -sf "$BIN_DIR/tifea" "$BIN_DIR/targz-installer"

# 4. Install Man Page
if [[ -f "$SCRIPT_DIR/data/man/tifea.1" ]]; then
    printf '  * Installing man page to %s/tifea.1...\n' "$MAN_DIR"
    cp -f "$SCRIPT_DIR/data/man/tifea.1" "$MAN_DIR/tifea.1"
    chmod 644 "$MAN_DIR/tifea.1"
fi

# 5. Install Shell Completions
if [[ -d "$SCRIPT_DIR/data/completions" ]]; then
    printf '  * Installing shell completions...\n'
    cp -f "$SCRIPT_DIR/data/completions/tifea.bash" "$BASH_COMP_DIR/tifea" 2>/dev/null || true
    cp -f "$SCRIPT_DIR/data/completions/tifea.zsh" "$ZSH_COMP_DIR/_tifea" 2>/dev/null || true
    cp -f "$SCRIPT_DIR/data/completions/tifea.fish" "$FISH_COMP_DIR/tifea.fish" 2>/dev/null || true
fi

# 6. Install AppStream Metainfo
if [[ -f "$SCRIPT_DIR/data/metainfo/org.example.tifea.metainfo.xml" ]]; then
    cp -f "$SCRIPT_DIR/data/metainfo/org.example.tifea.metainfo.xml" "$METAINFO_DIR/"
fi

# 7. Configure PATH automatically if needed
if [[ "$IS_ROOT" == "false" ]]; then
    case ":${PATH}:" in
      *:"$BIN_DIR":*) ;;
      *)
        if [[ -f "$HOME/.bashrc" ]]; then
            if ! grep -q 'export PATH=.*\.local/bin' "$HOME/.bashrc"; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
                printf '  * Added export PATH="%s:$PATH" to ~/.bashrc\n' "$HOME/.local/bin"
            fi
        fi
        if [[ -f "$HOME/.zshrc" ]]; then
            if ! grep -q 'export PATH=.*\.local/bin' "$HOME/.zshrc"; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
                printf '  * Added export PATH="%s:$PATH" to ~/.zshrc\n' "$HOME/.local/bin"
            fi
        fi
        ;;
    esac
fi

printf '\n[SUCCESS] TIFEA 1.0.0 installed successfully!\n'
printf 'Test it by running: tifea --help\n'
