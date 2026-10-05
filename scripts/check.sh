#!/usr/bin/env bash
set -euo pipefail
export DO_NOT_TRACK=1
export DBT_SEND_ANONYMOUS_USAGE_STATS=false
uv run ruff check .
uv run ruff format --check .
uv run pytest --basetemp /tmp/fc-clubs-tests
uv run sqlfluff lint models tests/dbt macros
uv run python scripts/check_public_files.py
