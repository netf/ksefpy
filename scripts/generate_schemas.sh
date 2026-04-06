#!/usr/bin/env bash
# generate_schemas.sh — Generate xsdata Python bindings from KSeF XSD schemas.
#
# Usage:
#   ./scripts/generate_schemas.sh [XSD_DIR] [OUTPUT_PKG]
#
# Arguments:
#   XSD_DIR     Directory containing .xsd files (default: schemas/xsd)
#   OUTPUT_PKG  Python package path for generated code (default: ksef/schemas/generated)
#
# Prerequisites:
#   uv run xsdata generate ...   (xsdata is a base dependency)
#
# Examples:
#   # Generate from default locations
#   ./scripts/generate_schemas.sh
#
#   # Generate from a custom XSD directory
#   ./scripts/generate_schemas.sh path/to/xsd ksef/schemas/fa3
#
# The generated package will contain one Python module per XSD file,
# plus a __init__.py that re-exports all dataclasses.
#
# After generation, import the classes like:
#   from ksef.schemas.generated.fa_2 import Faktura
#
set -euo pipefail

XSD_DIR="${1:-schemas/xsd}"
OUTPUT_PKG="${2:-ksef/schemas/generated}"

if [[ ! -d "$XSD_DIR" ]]; then
    echo "Error: XSD directory '$XSD_DIR' does not exist." >&2
    echo "Download KSeF XSD files from https://ksef.mf.gov.pl/static/wzor/ first." >&2
    exit 1
fi

echo "Generating xsdata bindings..."
echo "  Source : $XSD_DIR"
echo "  Output : $OUTPUT_PKG"

uv run xsdata generate \
    --package "$OUTPUT_PKG" \
    --print-level WARNING \
    "$XSD_DIR"

echo "Done. Generated files are in: $OUTPUT_PKG"
