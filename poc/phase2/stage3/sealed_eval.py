"""Sealed evaluation of the frozen v4 candidate (spec 02 section 2.3).

  --seal       draw a test seed with `secrets`, write it to phase2/stage3/sealed/test_seed.txt, and print its SHA-256
               (to be logged BEFORE the split is generated). Refuses if a seed already exists.
  --generate   check the v4 freeze, then generate data/corpus2/test from the sealed seed and record a corpus manifest
               (SHA-256 of every test document and of every ground truth).
  --run        check the freeze and the corpus manifest, then evaluate v4, the v3.2 snapshot and v2.1 on the test split.
"""
import argparse, glob, hashlib, json, secrets, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SEALED = ROOT / "phase2/stage3/sealed"
CMAN = ROOT / "phase2/stage3/test_corpus_manifest.json"
PY = str(ROOT / ".venv/bin/python")


def check_freeze():
    r = subprocess.run([PY, "-m", "phase2.stage3.freeze_v4", "--check"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("freeze check failed: " + (r.stderr or r.stdout)[-400:])
    print(r.stdout.strip())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--seal", action="store_true")
    g.add_argument("--generate", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    SEALED.mkdir(parents=True, exist_ok=True)
    f = SEALED / "test_seed.txt"
    if a.seal:
        if f.exists():
            raise SystemExit("a sealed seed already exists; never re-draw")
        seed = 10_000_000 + secrets.randbelow(80_000_000)
        f.write_text(str(seed))
        print("sealed seed SHA-256:", hashlib.sha256(str(seed).encode()).hexdigest())
    elif a.generate:
        check_freeze()
        from bench2 import generator as B
        if (ROOT / "data/corpus2/test").exists():
            raise SystemExit("test split already exists; never regenerate")
        seed = int(f.read_text())
        print(B.write_split(ROOT / "data/corpus2", "test", seed))
        docs = {}
        for p in sorted(glob.glob(str(ROOT / "data/corpus2/test/*/*.json"))):
            d = json.load(open(p))
            docs[str(Path(p).relative_to(ROOT))] = {"file_sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                                                    "truth_sha256": hashlib.sha256(json.dumps(d["truth"], sort_keys=True).encode()).hexdigest()}
        m = {"seed_sha256": hashlib.sha256(str(seed).encode()).hexdigest(), "n_docs": len(docs), "docs": docs}
        m["manifest_sha256"] = hashlib.sha256(json.dumps(docs, sort_keys=True).encode()).hexdigest()
        CMAN.write_text(json.dumps(m, indent=1))
        print("test corpus:", len(docs), "docs; manifest", m["manifest_sha256"][:16])
    else:
        check_freeze()
        m = json.loads(CMAN.read_text())
        for p, h in m["docs"].items():
            if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h["file_sha256"]:
                raise SystemExit(f"test corpus changed: {p}")
        for system, tag in (("current", "test_v4_frozen"), (str(ROOT / "phase2/stage2/snapshot_v3.2"), "test_v32"), ("v2.1", "test_v21")):
            sysarg = system if system in ("current", "v2.1") else f"snapshot:{system}"
            r = subprocess.run([PY, "-m", "bench2.evaluate", "--split", "test", "--system", sysarg, "--tag", tag],
                               cwd=ROOT, capture_output=True, text=True)
            print(f"== {tag}\n", r.stdout[-1500:], r.stderr[-600:])
