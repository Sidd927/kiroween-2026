"""Mutation testing of the v4 safety checks (spec 02 section 6). Custom AST mutator, no external tool.

Targets: validators.py, sentinel.py and the structure / extraction checks in interpreter.py.
Operators: comparison flip, boolean and<->or, removal of `not`, `raise` -> `pass`, integer constant +1.
Each mutant is applied to a TEMPORARY copy of spoolgeist_h + bindings_h (the real files are never touched) and the
bench2 dev split is processed. Killed = any document's outcome differs from the unmutated baseline (or a crash).
Safety-relevant survivors and 'mutants that create unsafe/silent accepts' are reported separately.

usage: .venv/bin/python -m phase2.stage3.mutation_test [--limit N]
"""
from __future__ import annotations

import argparse
import ast
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "phase2" / "stage3" / "results"
TARGETS = {
    "validators.py": None,                                    # whole module
    "sentinel.py": None,
    "interpreter.py": {"_field", "_table", "matches_layout", "page1_ok", "check_pages", "classify_lines", "line_key",
                       "numeric_text_check", "numeric_skeleton", "checked_lines", "masked_line", "recognise_v3",
                       "process", "execute", "is_note_start", "header_matches_at"},
}
FLIP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
        ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}

RUNNER = r'''
import sys, json, base64, glob
sys.path.insert(0, sys.argv[1])
from spoolgeist_h.pipeline import Pipeline
P = Pipeline(allow_agent_approval=True)
out = []
for p in sorted(glob.glob(sys.argv[2] + "/data/corpus2/dev/*/*.json")):
    d = json.load(open(p))
    try:
        oc = P.process_bytes(base64.b64decode(d["raw_b64"]), d["queue_codepage"])
        out.append([d["doc_id"], oc.status, None if oc.status != "ACCEPT" else sorted((x["code"], x["value"]) for x in oc.record["results"]),
                    None if oc.status != "ACCEPT" else [oc.record.get("patient_id"), oc.record.get("patient_name"), oc.record.get("collected")]])
    except Exception as e:
        out.append([d["doc_id"], "CRASH:" + e.__class__.__name__, None, None])
print(json.dumps(out))
'''


def points(src: str, funcs):
    tree = ast.parse(src)
    pts = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or (funcs is not None and fn.name not in funcs):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Compare):
                for k, op in enumerate(node.ops):
                    if type(op) in FLIP:
                        pts.append(("cmp", node.lineno, node.col_offset, k, fn.name))
            elif isinstance(node, ast.BoolOp):
                pts.append(("bool", node.lineno, node.col_offset, 0, fn.name))
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                pts.append(("not", node.lineno, node.col_offset, 0, fn.name))
            elif isinstance(node, ast.Raise):
                pts.append(("raise", node.lineno, node.col_offset, 0, fn.name))
            elif isinstance(node, ast.Constant) and type(node.value) is int and not isinstance(node.value, bool):
                pts.append(("const", node.lineno, node.col_offset, 0, fn.name))
    return pts


class Mut(ast.NodeTransformer):
    def __init__(self, pt):
        self.pt = pt

    def hit(self, node, kind):
        return self.pt[0] == kind and getattr(node, "lineno", None) == self.pt[1] and getattr(node, "col_offset", None) == self.pt[2]

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self.hit(node, "cmp"):
            node.ops[self.pt[3]] = FLIP[type(node.ops[self.pt[3]])]()
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if self.hit(node, "bool"):
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if self.hit(node, "not"):
            return node.operand
        return node

    def visit_Raise(self, node):
        if self.hit(node, "raise"):
            return ast.copy_location(ast.Pass(), node)
        return node

    def visit_Constant(self, node):
        if self.hit(node, "const"):
            return ast.copy_location(ast.Constant(node.value + 1), node)
        return node


def run_vector(pkg_root: Path):
    p = subprocess.run([sys.executable, "-c", RUNNER, str(pkg_root), str(ROOT)], capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        return None, p.stderr.strip().splitlines()[-1][:160] if p.stderr.strip() else "error"
    return json.loads(p.stdout), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="sg_mut_"))
    shutil.copytree(ROOT / "spoolgeist_h", tmp / "spoolgeist_h", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "bindings_h", tmp / "bindings_h")
    truth = {}
    for p in (ROOT / "data/corpus2/dev").glob("*/*.json"):
        d = json.loads(p.read_text())
        truth[d["doc_id"]] = d
    base, err = run_vector(tmp)
    assert base is not None, err
    base_map = {r[0]: r for r in base}
    all_pts = []
    for f, funcs in TARGETS.items():
        src = (ROOT / "spoolgeist_h" / f).read_text()
        all_pts += [(f,) + p for p in points(src, funcs)]
    rng = random.Random(a.seed)
    if a.limit and len(all_pts) > a.limit:
        all_pts = rng.sample(all_pts, a.limit)
    results = []
    for k, (f, kind, line, col, idx, fn) in enumerate(all_pts):
        src = (ROOT / "spoolgeist_h" / f).read_text()
        tree = Mut((kind, line, col, idx)).visit(ast.parse(src))
        ast.fix_missing_locations(tree)
        (tmp / "spoolgeist_h" / f).write_text(ast.unparse(tree))
        vec, err = run_vector(tmp)
        (tmp / "spoolgeist_h" / f).write_text(src)
        r = {"file": f, "function": fn, "op": kind, "line": line}
        if vec is None:
            r.update(status="killed", by="import/crash", detail=err)
        else:
            diff = [x for x in vec if base_map.get(x[0]) != x]
            unsafe = []
            for x in diff:
                d = truth[x[0]]
                if x[1] == "ACCEPT" and d["expected"] == "reject" and d["group"] != "policy":
                    unsafe.append(x[0])
                elif x[1] == "ACCEPT" and d["group"] == "valid":
                    exp = sorted((y["code"], y["value"]) for y in d["truth"]["results"])
                    if x[2] != exp or x[3] != [d["truth"]["patient_id"], x[3][1], d["truth"]["collected"]]:
                        unsafe.append(x[0] + "(silent)")
            r.update(status="killed" if diff else "survived", n_diff=len(diff), creates_unsafe_or_silent=len(unsafe),
                     example=unsafe[:2] or [x[0] for x in diff[:2]])
        results.append(r)
        print(k + 1, len(all_pts), r["status"], f, fn, kind, line, flush=True)
    shutil.rmtree(tmp)
    killed = sum(1 for r in results if r["status"] == "killed")
    summary = {"mutants": len(results), "killed": killed, "survived": len(results) - killed,
               "kill_rate": round(killed / len(results), 3) if results else None,
               "killed_mutants_that_would_create_unsafe_or_silent_accepts": sum(1 for r in results if r.get("creates_unsafe_or_silent")),
               "by_file": {f: {"n": sum(1 for r in results if r["file"] == f),
                               "killed": sum(1 for r in results if r["file"] == f and r["status"] == "killed")} for f in TARGETS},
               "survivors": [r for r in results if r["status"] == "survived"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mutation_v4.json").write_text(json.dumps({"summary": summary, "all": results}, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "survivors"}, indent=1))


if __name__ == "__main__":
    main()
