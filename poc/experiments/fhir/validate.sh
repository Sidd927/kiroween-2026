#!/bin/bash
# usage: validate.sh generic|abdm <output-name> <files...>
# Runs the official HL7 FHIR validator. Java's user.home is redirected into poc/.tools so the package
# cache stays inside the PoC folder. Terminology checks use the default public server (tx.fhir.org).
set -u
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
T="$HERE/.tools"
MODE="$1"; OUT="$2"; shift 2
ARGS=(-version 4.0.1)
if [ "$MODE" = "abdm" ]; then ARGS+=(-ig ndhm.in#6.5.0); fi
"$T/jre/Contents/Home/bin/java" -Duser.home="$T/javahome" -jar "$T/validator_cli.jar" "${ARGS[@]}" "$@" -output "$HERE/runtime/fhir/$OUT.json" > "$HERE/runtime/fhir/$OUT.log" 2>&1
echo "exit=$?"
