#!/usr/bin/env bash
#
# Copyright 2026 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Run the real toolkit over a given `doc-source.json` and `ui-tests.json`, outside any workflow: `normalize-docs`,
# `normalize-tests` and `coverage-matrix`, each through `main.py` as the action runs it, in a venv of its own built
# from `requirements.txt` alone; then re-read every output with `read_artifact` and print what ran and what came out.
# The configuration is `.env.local` (copy `.env.local.example`). See DEVELOPER.md § Local Integration Run.
#
#   ./local-integration.sh            # check, build the venv, run the three commands, validate and report
#   ./local-integration.sh --check    # check Python, git, the configuration and both inputs; nothing else
#
# Runs in bash 3.2 or later: Linux, macOS, or Git Bash on Windows.

set -euo pipefail

ME="local-integration.sh"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ENV_FILE=".env.local"
# The script's own venv, never the developer's `.venv`: it holds `requirements.txt` and nothing else, so a runtime
# requirement missing from that file fails here as it would on a runner.
VENV=".venv-local-integration"

# Every setting `.env.local` may hold; a line with any other key is ignored and reported by its number only.
KEYS="DOC_INPUT TESTS_INPUT VIEW OUT_DIR PYTHON"
REQUIRED="DOC_INPUT TESTS_INPUT"

die() { printf '%s: %s\n' "$ME" "$*" >&2; exit 1; }
note() { printf '%s: %s\n' "$ME" "$*" >&2; }
is_key() { local key; for key in $KEYS; do [ "$key" = "$1" ] && return 0; done; return 1; }

# Echo a command, each argument quoted where the shell would need it, then run it.
run() {
  local line="+" arg
  for arg in "$@"; do
    case "$arg" in
      "" | *[!A-Za-z0-9_./:=@,+-]*) line="$line '${arg//\'/\'\\\'\'}'" ;;
      *) line="$line $arg" ;;
    esac
  done
  printf '%s\n' "$line" >&2
  "$@"
}

usage() {
  cat <<EOF
usage: ./$ME [--check]

Runs normalize-docs, normalize-tests and coverage-matrix over the two files configured in $ENV_FILE (copy
.env.local.example), validates each output with read_artifact and prints a report.

  --check   verify Python, git, the configuration and both inputs; create no venv, run nothing
EOF
}

CHECK_ONLY=false
case "${1-}" in
  "") ;;
  --check) CHECK_ONLY=true ;;
  -h | --help) usage; exit 0 ;;
  *) die "unknown argument '$1'; usage: ./$ME [--check]" ;;
esac
[ $# -le 1 ] || die "too many arguments; usage: ./$ME [--check]"

# The toolkit reads no credential: every command reads local files and calls no API. Drop the token names an
# operator's shell may carry, so nothing this script starts can print or write one.
unset GITHUB_TOKEN GH_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN
# Every action input comes from `.env.local`; none is inherited from the shell, where `main.py` would read it.
for name in $(compgen -e); do
  case "$name" in INPUT_*) unset "$name" ;; esac
done

# --- Configuration -------------------------------------------------------------------------------------------
# Read as data, never sourced: a sourced file runs whatever it holds and would put any token it carries into the
# environment of every command below.
for key in $KEYS; do printf -v "CFG_$key" '%s' ""; done
[ -f "$ENV_FILE" ] || die "$ENV_FILE not found; copy .env.local.example to $ENV_FILE"
line_no=0
while IFS= read -r line || [ -n "$line" ]; do
  line_no=$((line_no + 1))
  line="${line%$'\r'}"
  line="${line#"${line%%[![:space:]]*}"}"
  case "$line" in "" | "#"*) continue ;; esac
  line="${line#export }"
  key="${line%%=*}"
  # A line is reported by its number only, never by its text: it may be a pasted secret, and a base64 one ending in
  # `=` padding reads as a key.
  [[ "$line" == *=* && "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "$ENV_FILE:$line_no: not a KEY=value line"
  value="${line#*=}"
  value="${value%"${value##*[![:space:]]}"}"
  case "$value" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
  esac
  if is_key "$key"; then
    printf -v "CFG_$key" '%s' "$value"
  else
    note "$ENV_FILE:$line_no: ignored, not a setting of this script"
  fi
done < "$ENV_FILE"

for key in $REQUIRED; do
  var="CFG_$key"
  [ -n "${!var}" ] || die "$key is not set in $ENV_FILE"
done
CFG_VIEW="${CFG_VIEW:-inner}"
case "$CFG_VIEW" in
  inner | release) ;;
  *) die "VIEW '$CFG_VIEW' is not inner or release" ;;
esac
CFG_OUT_DIR="${CFG_OUT_DIR:-./output}"

# A configured path: `~/` is the home directory, and a relative one resolves against this repository's root.
resolve() {
  case "$1" in
    "~/"*) printf '%s\n' "$HOME/${1#"~/"}" ;;
    /* | [A-Za-z]:[/\\]*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "$ROOT/${1#./}" ;;
  esac
}

# An existing directory's absolute path in the form the venv's Python reads. Git Bash's `pwd -W` gives `C:/...`;
# elsewhere `-W` is an error, and plain `pwd` is already right.
native_dir() { (cd "$1" && { pwd -W 2>/dev/null || pwd; }); }

# --- Checks (also the whole of --check) ----------------------------------------------------------------------
# The interpreter: `PYTHON` when set, else `python3`, else `python` - the order `action.yml` resolves it in.
PY="${CFG_PYTHON:-$(command -v python3 || command -v python || true)}"
[ -n "$PY" ] || die "needs Python >= 3.10, and neither python3 nor python is on PATH; set PYTHON in $ENV_FILE"
PY_VERSION="$("$PY" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null | tr -d '\r')" \
  || die "needs Python >= 3.10, and '$PY' does not run; set PYTHON in $ENV_FILE"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || die "needs Python >= 3.10, and '$PY' is $PY_VERSION; set PYTHON in $ENV_FILE"

# The header reads this repository's commit.
command -v git >/dev/null 2>&1 || die "git is not on PATH"

# A configured input file's absolute path, in the form the venv's Python reads.
input_file() {  # input_file KEY
  local var="CFG_$1" path
  path="$(resolve "${!var}")"
  [ -e "$path" ] || die "$1 not found: $path"
  [ -f "$path" ] || die "$1 is not a file: $path"
  printf '%s/%s\n' "$(native_dir "$(dirname "$path")")" "$(basename "$path")"
}
DOC_INPUT="$(input_file DOC_INPUT)"
TESTS_INPUT="$(input_file TESTS_INPUT)"

OUT="$(resolve "$CFG_OUT_DIR")"
[ ! -e "$OUT" ] || [ -d "$OUT" ] || die "OUT_DIR is not a directory: $OUT"

if [ "$CHECK_ONLY" = true ]; then
  printf '%s: check passed - Python %s (%s), git, %s, DOC_INPUT %s, TESTS_INPUT %s, VIEW %s\n' \
    "$ME" "$PY_VERSION" "$PY" "$ENV_FILE" "$DOC_INPUT" "$TESTS_INPUT" "$CFG_VIEW"
  exit 0
fi

# --- The venv, as `action.yml` builds its own --------------------------------------------------------------------
# The install must land in the venv and nowhere else: these redirect pip's target, install into another interpreter,
# or prepend to `sys.path`. Unset, not set empty: pip reads its own variables as configuration values.
unset PIP_TARGET PIP_PREFIX PIP_USER PIP_ROOT PIP_PYTHON PYTHONPATH

venv_python() {
  if [ -x "$VENV/bin/python" ]; then
    printf '%s\n' "$VENV/bin/python"
  elif [ -x "$VENV/Scripts/python.exe" ]; then
    printf '%s\n' "$VENV/Scripts/python.exe"
  else
    return 1
  fi
}

# Reuse the venv only when the interpreter now configured built it, from the `requirements.txt` now in the tree.
# A requirement dropped from the file would otherwise stay installed, and the run would hide what it should show.
IDENTITY='import sys; print(sys.base_prefix, sys.version_info[:3])'
WANT="$("$PY" -c "$IDENTITY")"
HAVE=""
if VPY="$(venv_python)" && cmp -s requirements.txt "$VENV/requirements.txt"; then
  HAVE="$("$VPY" -c "$IDENTITY" 2>/dev/null || true)"
fi
if [ "$HAVE" != "$WANT" ]; then
  run rm -rf "$VENV"
  run "$PY" -m venv "$VENV" || die "'$PY -m venv' failed; install the venv module"
  VPY="$(venv_python)" || die "'$PY -m venv' made no interpreter under $VENV/bin or $VENV/Scripts"
fi
# From this repository's root: `requirements.txt` names `./packages/...`, which pip reads against the directory it
# runs in.
run "$VPY" -m pip install --disable-pip-version-check -r requirements.txt
# pip's own config files can still redirect the install while pip exits 0; the import `action.yml` checks, through
# the venv's interpreter, reports it here, where it happened.
run "$VPY" -E -c 'import living_doc_cli.main' \
  || die "the requirements did not land in $VENV; check pip's configuration for a 'target' or 'prefix' setting"
run cp requirements.txt "$VENV/requirements.txt"

# --- What runs ---------------------------------------------------------------------------------------------------
commit_of() {  # commit_of DIR: its HEAD, marked when tracked files differ from it
  local sha
  sha="$(git -C "$1" rev-parse HEAD 2>/dev/null)" || { echo "unknown (not a git checkout)"; return 0; }
  if [ -n "$(git -C "$1" status --porcelain --untracked-files=no 2>/dev/null)" ]; then
    sha="$sha (uncommitted changes)"
  fi
  printf '%s\n' "$sha"
}

UTILITIES_VERSION="$("$VPY" -E -c 'from importlib.metadata import version; print(version("living-doc-utilities"))' \
  | tr -d '\r')"
VENV_PY_VERSION="$("$VPY" -E -c 'import platform; print(platform.python_version())' | tr -d '\r')"
run mkdir -p "$OUT"
OUTPUT_ROOT="$(native_dir "$OUT")/toolkit"
# A command that fails stops the run, which would leave a later command's previous output beside it. Clear all three
# first: the output holds this run's files and nothing older.
run rm -rf "$OUT/toolkit/normalize-docs" "$OUT/toolkit/normalize-tests" "$OUT/toolkit/coverage-matrix"

cat <<EOF
== $ME
toolkit:               $(commit_of "$ROOT")
living-doc-utilities:  $UTILITIES_VERSION
python:                $VENV_PY_VERSION ($VPY)
documentation input:   $DOC_INPUT
tests input:           $TESTS_INPUT
view:                  $CFG_VIEW
output:                $OUTPUT_ROOT
EOF

# `main.py` writes the `output-path` action output to `$GITHUB_OUTPUT`, which only a runner provides.
GITHUB_OUTPUT_FILE="$VENV/github-output.txt"

now_ms() { "$VPY" -E -c 'import time; print(int(time.time() * 1000))' | tr -d '\r'; }

# Run one command as the action does - `main.py` with `-E`, the command's own inputs alone, each in its environment -
# then validate and report its output against the files it read, its `input` and `tests-input`.
toolkit() {  # toolkit COMMAND CONTRACT OUTPUT INPUT_NAME=VALUE...
  local command="$1" contract="$2" output="$3" assignment started finished status=0
  shift 3
  local inputs=()
  for assignment in "$@"; do
    case "$assignment" in INPUT_INPUT=* | INPUT_TESTS_INPUT=*) inputs+=("${assignment#*=}") ;; esac
  done
  echo
  echo "== $command"
  : > "$GITHUB_OUTPUT_FILE"
  started="$(now_ms)"
  run env GITHUB_OUTPUT="$GITHUB_OUTPUT_FILE" INPUT_COMMAND="$command" INPUT_OUTPUT="$output" "$@" \
    "$VPY" -E main.py || status=$?
  finished="$(now_ms)"
  [ "$status" -eq 0 ] || die "the toolkit failed in '$command' (exit $status); its log is above"
  run "$VPY" -E -X utf8 -m tools.local_integration report "$output" "$contract" "$((finished - started))" \
    "${inputs[@]}" || die "the '$command' output failed validation"
}

toolkit normalize-docs generator-ready "$OUTPUT_ROOT/normalize-docs/generator-ready.json" \
  INPUT_INPUT="$DOC_INPUT" INPUT_VIEW="$CFG_VIEW"
toolkit normalize-tests ui-test-catalog "$OUTPUT_ROOT/normalize-tests/ui-test-catalog.json" \
  INPUT_INPUT="$TESTS_INPUT"
toolkit coverage-matrix coverage-matrix "$OUTPUT_ROOT/coverage-matrix/coverage-matrix.json" \
  INPUT_INPUT="$DOC_INPUT" INPUT_TESTS_INPUT="$TESTS_INPUT" INPUT_VIEW="$CFG_VIEW"

echo
echo "$ME: the three outputs are written and valid under $OUTPUT_ROOT"
