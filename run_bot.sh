#!/usr/bin/env bash
# run_bot.sh
# Usage: ./run_bot.sh <module> [args]
# Example: ./run_bot.sh cli.py run_reminders

set -euo pipefail

print_err() { printf '%s\n' "$*" >&2; }

if [ $# -lt 1 ]; then
  print_err "Usage: $0 <module> [args]"
  exit 2
fi

MODULE="$1"
shift
ARGS=("$@")

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
printf '[ruun_bot] Script directory: %s\n' "$SCRIPT_DIR"

# venv paths (POSIX)
VENV_BIN_DIR="$SCRIPT_DIR/.venv/bin"
printf '[ruun_bot] venv dir: %s\n' "$VENV_BIN_DIR"

if [ ! -d "$VENV_BIN_DIR" ]; then
  print_err "Virtual environment not found at $VENV_BIN_DIR. Please set up the virtual environment."
  exit 1
fi

ACTIVATE_SCRIPT="$VENV_BIN_DIR/activate"
printf '[ruun_bot] venv activation script: %s\n' "$ACTIVATE_SCRIPT"

if [ -f "$ACTIVATE_SCRIPT" ]; then
  printf '[ruun_bot] Activating venv...\n'
  # shellcheck source=/dev/null
  . "$ACTIVATE_SCRIPT"
else
  printf '[ruun_bot] Activation script not found; will use venv python directly.\n'
fi

VENV_PYTHON="$VENV_BIN_DIR/python"
printf '[ruun_bot] venv python: %s\n' "$VENV_PYTHON"

if [ ! -x "$VENV_PYTHON" ]; then
  print_err "Python venv not found at $VENV_PYTHON. Please set up the virtual environment."
  exit 1
fi

MODULE_PATH="$SCRIPT_DIR/$MODULE"
printf '[ruun_bot] Module: %s\n' "$MODULE"
printf '[ruun_bot] Args: %s\n' "${ARGS[*]}"

if [ ! -f "$MODULE_PATH" ]; then
  print_err "Module not found at $MODULE_PATH"
  exit 1
fi

printf '[ruun_bot] Running: %s %s %s\n' "$VENV_PYTHON" "$MODULE_PATH" "${ARGS[*]}"
exec "$VENV_PYTHON" "$MODULE_PATH" "${ARGS[@]}"
