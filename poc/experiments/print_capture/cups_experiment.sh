#!/bin/bash
# Real OS spooler test on macOS: CUPS raw queue -> socket://127.0.0.1:9100 -> Spoolgeist listener -> fake printer.
# Adds a TEMPORARY queue "spoolgeist-poc" and always removes it on exit.
set -u
cd "$(dirname "$0")/../.."
RT=runtime/print_capture_cups; rm -rf "$RT"; mkdir -p "$RT"
PY=.venv/bin/python
Q=spoolgeist-poc
cleanup() {
  kill $LPID $PPID2 2>/dev/null
  lpadmin -x "$Q" 2>/dev/null && echo "[cleanup] queue $Q removed"
  lpstat -p "$Q" >/dev/null 2>&1 && echo "[cleanup] WARNING queue still present" || echo "[cleanup] verified: queue absent"
}
trap cleanup EXIT
start_listener() { $PY -m spoolgeist.capture --port 9100 --forward 127.0.0.1:9101 --spool "$RT/spool" >> "$RT/listener.log" 2>&1 & LPID=$!; sleep 1.5; }
$PY experiments/print_capture/fake_printer.py --port 9101 --out "$RT/fake_printer" >> "$RT/printer.log" 2>&1 & PPID2=$!
start_listener

echo "== add queue"; lpadmin -p "$Q" -E -v socket://127.0.0.1:9100 -m raw 2>&1 || lpadmin -p "$Q" -E -v socket://127.0.0.1:9100 2>&1
lpstat -v "$Q"
$PY -c "import json;open('$RT/A.txt','wb').write(json.load(open('data/corpus/test/A/A-11001-clean.json'))['text'].encode())"
$PY -c "import json;open('$RT/B.txt','wb').write(json.load(open('data/corpus/test/B/B-21001-clean.json'))['text'].encode())"
$PY -c "import json;open('$RT/C.txt','wb').write(json.load(open('data/corpus/test/C/C-31001-clean.json'))['text'].encode())"
shasum -a 256 "$RT"/A.txt "$RT"/B.txt "$RT"/C.txt | tee "$RT/source_sha256.txt"

echo "== C1 normal print via CUPS (layout A, plain text)"; lp -d "$Q" -o raw "$RT/A.txt"; sleep 4
echo "== C1b ESC/P job via CUPS (layout B)"; lp -d "$Q" -o raw "$RT/B.txt"; sleep 4
lpstat -W completed -o "$Q" | tail -3

echo "== C2 listener OFFLINE, then print (layout C)"; kill $LPID; sleep 1
lp -d "$Q" -o raw "$RT/C.txt"; sleep 6
echo "-- queue state while listener offline:"; lpstat -p "$Q" -l; lpstat -o "$Q"
echo "-- restarting listener at $(date +%T)"; start_listener
for i in $(seq 1 30); do sleep 2; if ! lpstat -o "$Q" | grep -q "$Q"; then echo "-- queue drained after ~$((i*2))s"; break; fi; done
lpstat -o "$Q"; sleep 3
echo "== results"
grep -h '"event": "job_captured"' "$RT"/spool/events.jsonl
grep -h '"event": "job_processed"' "$RT"/spool/events.jsonl
cat "$RT"/fake_printer/printed.jsonl
