#!/usr/bin/env bash
set -euo pipefail

# Clone upstream simulator dependencies at the exact commits used in the
# original research topic. These are kept out of .gitmodules so the public
# example repo stays small; a shallow clone at a specific commit keeps the
# download fast while preserving reproducibility.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST_DIR="${ROOT_DIR}/repos/extern"

mkdir -p "${DEST_DIR}"

clone_at_commit() {
    local url="$1"
    local commit="$2"
    local dest="$3"
    if [[ -d "${dest}/.git" ]]; then
        echo "Already present: ${dest}"
        return 0
    fi
    echo "Cloning ${url} at ${commit}..."
    # Shallow clone the branch tip, then fetch the exact commit and checkout.
    # If the commit is not reachable from the current tip, remove --depth=1.
    git clone --depth=1 "${url}" "${dest}"
    (
        cd "${dest}"
        git fetch --depth=1 origin "${commit}"
        git checkout "${commit}"
    )
}

clone_at_commit \
    https://github.com/Dao-AILab/flash-attention.git \
    002cce0a1068f8c07dfccb5a1d232b9a3276947c \
    "${DEST_DIR}/flash-attention"

clone_at_commit \
    https://github.com/accel-sim/accel-sim-framework.git \
    3016c658f810bdae9a14bf4534ee99e9945eedae \
    "${DEST_DIR}/accel-sim-framework"

echo "External dependencies ready at ${DEST_DIR}."
