"""Stand-in for a physical RAW/9100 printer: accepts jobs and stores the exact bytes it received.
This is a TEST RECEIVER, not a printer. No paper is involved.
usage: python experiments/print_capture/fake_printer.py --port 9101 --out runtime/fake_printer
"""
import argparse
import asyncio
import hashlib
import json
import time
from pathlib import Path


async def main(port: int, out: Path):
    out.mkdir(parents=True, exist_ok=True)

    async def handle(r, w):
        data = await r.read()
        sha = hashlib.sha256(data).hexdigest()
        name = time.strftime("%H%M%S-") + sha[:12]
        (out / f"{name}.prn").write_bytes(data)
        line = json.dumps({"t": round(time.time(), 3), "event": "printed", "bytes": len(data), "sha256": sha})
        print(line, flush=True)
        with (out / "printed.jsonl").open("a") as f:
            f.write(line + "\n")
        w.close()

    srv = await asyncio.start_server(handle, "127.0.0.1", port)
    print(json.dumps({"event": "fake_printer_listening", "port": port}), flush=True)
    async with srv:
        await srv.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9101)
    ap.add_argument("--out", default="runtime/fake_printer")
    a = ap.parse_args()
    asyncio.run(main(a.port, Path(a.out)))
