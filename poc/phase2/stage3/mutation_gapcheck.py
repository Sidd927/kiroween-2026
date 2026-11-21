"""Re-run selected survivors against the UPDATED v4 test suite (after the Stage-3 gap tests were added).
usage: .venv/bin/python -m phase2.stage3.mutation_gapcheck"""
import ast, json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase2.stage3.mutation_test import Mut, points, TARGETS
TARGET_LINES = {("validators.py", l) for l in (47, 57, 62, 66)} | {("interpreter.py", l) for l in (235, 238, 260, 496, 502, 148)}
cl = json.loads((ROOT / "phase2/stage3/results/mutation_v4_classified.json").read_text())
cand = [r for r in cl["rows"] if r["class"] != "KILLED" and (r["file"], r["line"]) in TARGET_LINES]
tmp = Path(tempfile.mkdtemp(prefix="sg_mutgap_"))
for d in ("spoolgeist_h", "bindings_h", "bench", "bench2", "tests_h", "tests", "data/corpus2", "bindings"):
    shutil.copytree(ROOT / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
(tmp / "phase2/stage3/results").mkdir(parents=True); (tmp / "phase2/__init__.py").touch()
res = []
for r in cand:
    src = (ROOT / "spoolgeist_h" / r["file"]).read_text()
    pts = [p for p in points(src, TARGETS[r["file"]]) if p[0] == r["op"] and p[1] == r["line"] and p[4] == r["function"]]
    killed = False
    for p in pts:
        tree = Mut(p[:4]).visit(ast.parse(src)); ast.fix_missing_locations(tree)
        (tmp / "spoolgeist_h" / r["file"]).write_text(ast.unparse(tree))
        out = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests_h/test_v4.py",
                              "tests_h/test_registry_gate_precision.py"], cwd=tmp, capture_output=True, text=True, timeout=600)
        (tmp / "spoolgeist_h" / r["file"]).write_text(src)
        killed |= out.returncode != 0
    res.append({**r, "killed_by_updated_tests": killed})
    print(r["id"], r["file"], r["line"], r["op"], "KILLED" if killed else "survives", flush=True)
shutil.rmtree(tmp)
(ROOT / "phase2/stage3/results/mutation_v4_gapcheck.json").write_text(json.dumps(res, indent=1))
print(json.dumps({"checked": len(res), "killed": sum(x["killed_by_updated_tests"] for x in res)}))
