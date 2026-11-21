"""Re-check the survivors of mutation_test.py against the v4 unit/regression tests (tests_h/test_v4.py and
test_registry_gate_precision.py) in a TEMPORARY copy of the project (real files untouched).
usage: .venv/bin/python -m phase2.stage3.mutation_recheck"""
import ast, json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase2.stage3.mutation_test import Mut, points, TARGETS

res = json.loads((ROOT / "phase2/stage3/results/mutation_v4.json").read_text())
surv = res["summary"]["survivors"]
tmp = Path(tempfile.mkdtemp(prefix="sg_mutre_"))
for d in ("spoolgeist_h", "bindings_h", "bench", "bench2", "tests_h", "tests", "data/corpus2", "bindings"):
    shutil.copytree(ROOT / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
(tmp / "phase2/stage3/results").mkdir(parents=True)
(tmp / "phase2/__init__.py").touch()
out = []
for k, s in enumerate(surv):
    f = s["file"]
    src = (ROOT / "spoolgeist_h" / f).read_text()
    pts = [p for p in points(src, TARGETS[f]) if p[0] == s["op"] and p[1] == s["line"] and p[4] == s["function"]]
    killed_any, detail = False, []
    for p in pts:     # all mutants sharing (op, line, function); usually exactly one
        tree = Mut(p[:4]).visit(ast.parse(src)); ast.fix_missing_locations(tree)
        (tmp / "spoolgeist_h" / f).write_text(ast.unparse(tree))
        r = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                            "tests_h/test_v4.py", "tests_h/test_registry_gate_precision.py"], cwd=tmp, capture_output=True, text=True, timeout=600)
        (tmp / "spoolgeist_h" / f).write_text(src)
        killed = r.returncode != 0
        killed_any |= killed
        detail.append((r.stdout.strip().splitlines() or [""])[-1][:120])
    out.append({**s, "killed_by_tests": killed_any, "tests_detail": detail})
    print(k + 1, len(surv), "KILLED" if killed_any else "still survives", f, s["function"], s["op"], s["line"], flush=True)
shutil.rmtree(tmp)
still = [o for o in out if not o["killed_by_tests"]]
(ROOT / "phase2/stage3/results/mutation_v4_recheck.json").write_text(json.dumps({"rechecked": len(out), "killed_by_tests": len(out) - len(still), "still_surviving": still}, indent=1))
print(json.dumps({"rechecked": len(out), "killed_by_tests": len(out) - len(still), "still_surviving": len(still)}))
