# TAR_Installer_For_Electron_Applications (TIFEA)

Transactional installer and package manager for Linux software tarballs (`.tar.gz`, `.tar.xz`).

## Overview

TIFEA installs prebuilt Electron and desktop software tarballs into standard system locations (`/opt/<appid>`). It generates Freedesktop-compliant `.desktop` files, manages Electron sandbox confinement (AppArmor, setuid, `--no-sandbox`), extracts bundled icons (including ASAR resources), registers `xdg-mime` handlers, and logs installation state in an atomic transaction ledger with LIFO rollback support.

## Project Structure

Standard Linux packaging layout:

```text
TAR_Installer_For_Electron_Applications/
├── bin/                          # Executable entry points (bin/tifea)
├── tifea/                        # Python package source
│   ├── __init__.py
│   ├── cli.py
│   ├── model.py
│   ├── detector/                 # Archive & icon detection logic
│   ├── distro/                   # Distribution & confinement checking
│   ├── executor/                 # Execution engine & manifest ledger
│   ├── planner/                  # Transaction planning
│   ├── rollback/                 # Rollback stack & uninstaller
│   ├── ui/                       # Console UI & progress renderers
│   └── verifier/                 # Integrity & system verification
├── data/                         # Non-code assets
│   ├── completions/              # Bash, Zsh, Fish completions
│   ├── man/                      # Man page (tifea.1)
│   └── metainfo/                 # AppStream metadata XML
├── tests/                        # Unit and integration test suite
├── pyproject.toml                # PEP 621 build configuration
├── Makefile                      # Standard POSIX build directives
├── tifea.spec                    # RPM Spec file for DNF/COPR
├── org.example.tifea.json        # Flatpak builder manifest
├── install.sh                    # System and user installation script
├── LICENSE
└── README.md
```

## Installation

### System-wide (Root)
```bash
sudo ./install.sh
```

### User-level (Non-root)
```bash
./install.sh
```

### Via Makefile
```bash
make install PREFIX=/usr/local
```

### Via Pip / Setuptools
```bash
python3 -m pip install .
```

## Command Usage

```bash
# Install tarball
tifea install /path/to/archive.tar.gz

# Dry-run mode
tifea install /path/to/archive.tar.gz --dry-run

# Reinstall existing application
tifea reinstall /path/to/archive.tar.gz

# Check installation integrity
tifea check /opt/appid /path/to/archive.tar.gz

# Repair broken links or desktop integration
tifea fix /opt/appid /path/to/archive.tar.gz

# List installed applications
tifea list

# Uninstall application
tifea uninstall appid
```

## Testing

```bash
make test
```

## Performance & Benchmarks

[benchmarks yet to be written]

## Packaging & Distribution Notes

- **DNF / RPM**: `tifea.spec` [COPR repository instructions yet to be written]
- **Flatpak**: `org.example.tifea.json` [Flathub submission details yet to be written]

## Contributing

[contribution guidelines yet to be written]

## License

PolyForm Noncommercial License 1.0.0. See [LICENSE](LICENSE).
