#!/usr/bin/env bash
# Build the vendored Tanaka solvers into solvers/bin/.
#
# The original sources predate GCC's -fno-common default; they declare globals
# in headers, so they must be compiled with -fcommon. The IP solver needs Boost
# and Gurobi and is skipped unless both are available.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/solvers"
BIN="$SRC/bin"
mkdir -p "$BIN"

# -fcommon restores the pre-GCC-10 tentative-definition behaviour these sources
# rely on, passed via DEFS so each Makefile keeps its own CFLAGS.
build_c() {
  local dir="$1" target="$2" out="$3"
  echo ">> building $out"
  make -C "$SRC/$dir" clean >/dev/null 2>&1 || true
  make -C "$SRC/$dir" DEFS="-fcommon" "$target"
  cp "$SRC/$dir/$target" "$BIN/$out"
}

build_c tanaka_restricted_distinct_1.3   rbrp_bb  tanaka_restricted_distinct_1.3
build_c tanaka_restricted_distinct_1.11  brp_bb   tanaka_restricted_distinct_1.11
build_c tanaka_unrestricted_distinct_1.01 ubrp_bb tanaka_unrestricted_distinct_1.01
build_c tanaka_restricted_duplicate_1.02 brp_bb   tanaka_restricted_duplicate_1.02

# Jin & Tanaka (2023), vendored from github.com/jinboszu/ucrp-idbb. Upstream
# builds with CMake; the vendored Makefile mirrors it so no CMake is needed.
echo ">> building jin_tanaka_unrestricted_distinct_jt23"
make -C "$SRC/ucrp_idbb_jt23" clean >/dev/null 2>&1 || true
make -C "$SRC/ucrp_idbb_jt23" main-solve
cp "$SRC/ucrp_idbb_jt23/main-solve" "$BIN/jin_tanaka_unrestricted_distinct_jt23"

if [ -n "${GUROBI_ROOT:-}" ] && pkg-config --exists boost 2>/dev/null; then
  echo ">> building IP solver (Gurobi detected)"
  make -C "$SRC/tanaka_restricted_distinct_ip_1.0" || true
  [ -f "$SRC/tanaka_restricted_distinct_ip_1.0/rbrp_ip" ] && \
    cp "$SRC/tanaka_restricted_distinct_ip_1.0/rbrp_ip" "$BIN/tanaka_restricted_distinct_ip_1.0"
else
  echo ">> skipping IP solver (set GUROBI_ROOT and install Boost to build it)"
fi

echo ">> binaries:"
ls -1 "$BIN"
