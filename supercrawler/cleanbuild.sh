#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find "$script_dir" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$script_dir" -type d -name '.pytest_cache' -prune -exec rm -rf {} +
find "$script_dir" -type d -name '.venv' -prune -exec rm -rf {} +
