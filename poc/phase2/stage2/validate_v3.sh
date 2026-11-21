#!/bin/bash
# usage: validate_v3.sh generic|abdm  -> phase2/stage2/results/fhir_v3_<mode>.{json,log}
set -u
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
T="$HERE/.tools"; MODE="$1"
ARGS=(-version 4.0.1); [ "$MODE" = "abdm" ] && ARGS+=(-ig ndhm.in#6.5.0)
"$T/jre/Contents/Home/bin/java" -Duser.home="$T/javahome" -jar "$T/validator_cli.jar" "${ARGS[@]}" "$HERE"/runtime_h/fhir/$MODE/*.json \
  -output "$HERE/phase2/stage2/results/fhir_v3_$MODE.json" > "$HERE/phase2/stage2/results/fhir_v3_$MODE.log" 2>&1
echo "exit=$?"
