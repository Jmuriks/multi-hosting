#!/bin/bash

main_dir="$(dirname "$(realpath -e "$0")")"

venv_python="$main_dir/.venv/bin/python"

"$venv_python" "$main_dir/main.py" "$@" 
