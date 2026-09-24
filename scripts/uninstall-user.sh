#!/usr/bin/env bash
set -euo pipefail
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_DIR="$DATA_HOME/json-registry-manager"
LINK="$HOME/.local/bin/jrm"

if [ -L "$LINK" ]; then
  TARGET="$(readlink -f "$LINK" || true)"
  case "$TARGET" in
    "$INSTALL_DIR"/*) rm -f "$LINK" ;;
  esac
fi
rm -rf "$INSTALL_DIR"
echo "JSON Registry Manager user installation removed."
