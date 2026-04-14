#!/usr/bin/env bash
# Run the ELT pipeline.
# Usage: /bin/bash services/pipeline/run_pipeline.sh
# Typically scheduled 2 hours after run_crawler.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT"
"$PYTHON_BIN" -m services.pipeline.main
