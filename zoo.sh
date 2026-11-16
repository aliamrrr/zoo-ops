#!/usr/bin/env sh
# Zoo Ops for macOS, Linux and WSL. Sets itself up on the first run, then runs a zoo command.
#
#   ./zoo.sh               choose a mode, then play
#   ./zoo.sh play hard     play a mode directly: classic, hard or hardpp
#   ./zoo.sh test 3        run the tests of level 3
#   ./zoo.sh --help        every command
set -eu
cd "$(dirname "$0")"

VENV=.venv
STAMP="$VENV/.zoo-installed"
case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN*) VENV_PY="$VENV/Scripts/python.exe" ;;  # Git Bash on Windows
  *) VENV_PY="$VENV/bin/python" ;;
esac

find_python() {
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

if [ ! -x "$VENV_PY" ]; then
  if ! PYTHON=$(find_python); then
    echo "Zoo Ops needs Python 3.11 or newer." >&2
    echo "  macOS:          brew install python@3.12   (or https://www.python.org/downloads/)" >&2
    echo "  Ubuntu / WSL:   sudo apt install python3 python3-venv" >&2
    echo "  Or play without Python: docker compose up" >&2
    exit 1
  fi
  echo "Setting up Zoo Ops with $("$PYTHON" --version) (first run only)..."
  if ! "$PYTHON" -m venv "$VENV"; then
    echo "Could not create the virtual environment." >&2
    echo "  Ubuntu / Debian / WSL: sudo apt install python3-venv" >&2
    rm -rf "$VENV"
    exit 1
  fi
fi

# Install on the first run, and again whenever pyproject.toml changes (after a git pull).
if [ ! -f "$STAMP" ] || [ pyproject.toml -nt "$STAMP" ]; then
  echo "Installing the game's dependencies (about a minute)..."
  if ! { "$VENV_PY" -m pip install --upgrade pip &&
         "$VENV_PY" -m pip install --editable .; } >"$VENV/install.log" 2>&1; then
    cat "$VENV/install.log" >&2
    echo "The install failed (log above, also in $VENV/install.log)." >&2
    exit 1
  fi
  touch "$STAMP"
fi

exec "$VENV_PY" -m zoo "$@"
