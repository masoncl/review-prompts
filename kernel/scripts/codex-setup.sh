#!/bin/bash
#
# Compatibility wrapper for the repository-wide Codex installer.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

exec "$REPO_DIR/setup.sh" codex kernel
