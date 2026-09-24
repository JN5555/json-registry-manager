#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_DIR="$DATA_HOME/json-registry-manager"
VENV="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"
LINK="$BIN_DIR/jrm"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.10+ first." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$BIN_DIR"
if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV/bin/python" -m pip install --upgrade "$ROOT_DIR"
ln -sfn "$VENV/bin/jrm" "$LINK"

printf '\nInstalled JSON Registry Manager.\n'
printf 'Command: %s\n' "$LINK"
"$LINK" --version

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    printf '\nNOTE: %s is not in PATH. Add this to ~/.bashrc:\n' "$BIN_DIR"
    printf 'export PATH="$HOME/.local/bin:$PATH"\n'
    ;;
esac
