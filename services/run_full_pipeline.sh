#!/usr/bin/env bash
# Run the full ProductHunter data flow:
#   crawl -> CSV staging + LLM normalization -> migrate normalized data
#
# Usage:
#   /bin/bash services/run_full_pipeline.sh
#
# Optional environment variables:
#   PYTHON_BIN=python3
#   SKIP_CRAWL=1
#   SKIP_PIPELINE=1
#   SKIP_MIGRATE=1
#   STRICT_CSV=1
#   EXPECTED_CSV_FILES="cellphones_products.csv fptshop_products.csv"
#   LOG_DIR=services/logs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python}"
CRAWLER_OUTPUT_DIR="$REPO_ROOT/services/crawler/output"
EXPECTED_CSV_FILES="${EXPECTED_CSV_FILES:-fptshop_products.csv phongvu_products.csv cellphones_products.csv}"
RUN_ID="${RUN_ID:-$(date '+%Y%m%d_%H%M%S')}"
RESOLVED_LOG_DIR=""

resolve_log_dir() {
    if [[ -z "${LOG_DIR:-}" ]]; then
        return
    fi

    if [[ "$LOG_DIR" == /* ]]; then
        RESOLVED_LOG_DIR="$LOG_DIR"
    else
        RESOLVED_LOG_DIR="$REPO_ROOT/$LOG_DIR"
    fi
    mkdir -p "$RESOLVED_LOG_DIR"
}

elapsed_seconds() {
    local started_at="$1"
    local finished_at
    finished_at="$(date +%s)"
    echo "$((finished_at - started_at))s"
}

run_stage() {
    local key="$1"
    local label="$2"
    shift 2

    local started_at
    started_at="$(date +%s)"

    echo
    echo "============================================================"
    echo "[full-pipeline] START $label"
    echo "============================================================"

    if [[ -n "$RESOLVED_LOG_DIR" ]]; then
        local log_file="$RESOLVED_LOG_DIR/${RUN_ID}_${key}.log"
        "$@" 2>&1 | tee "$log_file"
        echo "[full-pipeline] Log written: $log_file"
    else
        "$@"
    fi

    echo "[full-pipeline] DONE $label in $(elapsed_seconds "$started_at")"
}

validate_expected_csvs() {
    if [[ "${STRICT_CSV:-0}" != "1" ]]; then
        return
    fi

    local missing=()
    local csv_name
    for csv_name in $EXPECTED_CSV_FILES; do
        if [[ ! -s "$CRAWLER_OUTPUT_DIR/$csv_name" ]]; then
            missing+=("$csv_name")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        echo "[full-pipeline] Missing expected crawler CSV files:"
        printf '  - %s\n' "${missing[@]}"
        echo "[full-pipeline] Set EXPECTED_CSV_FILES to match enabled crawlers, or run without STRICT_CSV=1."
        return 1
    fi
}

main() {
    resolve_log_dir

    cd "$REPO_ROOT"
    export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

    local started_at
    started_at="$(date +%s)"

    echo "[full-pipeline] Repo root: $REPO_ROOT"
    echo "[full-pipeline] Python: $PYTHON_BIN"
    echo "[full-pipeline] Run ID: $RUN_ID"

    if [[ "${SKIP_CRAWL:-0}" == "1" ]]; then
        echo "[full-pipeline] SKIP_CRAWL=1, reusing existing crawler CSV files."
    else
        run_stage "01_crawl" "crawler" "$PYTHON_BIN" -m services.crawler.main
    fi

    validate_expected_csvs

    if [[ "${SKIP_PIPELINE:-0}" == "1" ]]; then
        echo "[full-pipeline] SKIP_PIPELINE=1, skipping CSV staging and LLM normalization."
    else
        run_stage "02_pipeline" "CSV staging + LLM normalization" "$PYTHON_BIN" -m services.pipeline.main
    fi

    if [[ "${SKIP_MIGRATE:-0}" == "1" ]]; then
        echo "[full-pipeline] SKIP_MIGRATE=1, skipping normalized-data migration."
    else
        run_stage "03_migrate" "normalized-data migration" "$PYTHON_BIN" -m services.pipeline.migrate_normalized_data
    fi

    echo
    echo "============================================================"
    echo "[full-pipeline] ALL DONE in $(elapsed_seconds "$started_at")"
    echo "============================================================"
}

main "$@"
