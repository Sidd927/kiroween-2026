"""Extended oracle for mutants that survived both the dev-split oracle and the v4 unit tests.

Oracle documents (development material only; the sealed test split is NOT used):
  * every bench2 catalogue class x 6 layouts x 3 seeds at seed base 5,000,000 (development range)
  * the Stage-2 adversarial suite v1.1 (v1 generator)
  * the red-team attack documents R1-R4 (redteam_v3.py) and the evasion-v1 phrasings
A mutant is killed if any document's (status, results, identity) differs from the unmutated system.
usage: .venv/bin/python -m phase2.stage3.mutation_extended
"""
import ast, json, pickle, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase2.stage3.mutation_test import Mut, points, TARGETS

ORACLE = ROOT / "phase2/stage3/results/mutation_oracle_docs.pkl"
RUN = r'''
import sys, json, pickle
sys.path.insert(0, sys.argv[1])
from spoolgeist_h.pipeline import Pipeline
P = Pipeline(allow_agent_approval=True)
docs = pickle.load(open(sys.argv[2], "rb"))
out = []
for raw, cp in docs:
    try:
        oc = P.process_bytes(raw, cp)
        out.append([oc.status, None if oc.status != "ACCEPT" else sorted((x["code"], x["value"], x.get("flag", "")) for x in oc.record["results"]),
                    None if oc.status != "ACCEPT" else [oc.record.get(k) for k in ("patient_id", "patient_name", "collected", "patient_age", "patient_sex")]])
    except Exception as e:
        out.append(["CRASH:" + e.__class__.__name__, None, None])
print(json.dumps(out))
'''


def build_oracle():
    import random
    from bench2 import generator as B
    from bench import generator as G
    docs = []
    for li, lay in enumerate(B.LAYOUTS):
        for ci, cls in enumerate(B.VALID + B.POLICY + B.DEFECTS):
            k = 0
            for s in range(60):
                if k >= 3:
                    break
                d = B.build(lay, 5_000_000 + li * 100_000 + ci * 1000 + s, cls)
                if d:
                    docs.append((d.raw, d.queue_codepage)); k += 1
    from phase2.suites import adversarial as A
    for c in A.build_suite():
        docs.append((c["text"].encode(), None))
    from phase2.stage2 import redteam_v3 as RT
    for fn in RT.PROBES.values():
        for lay in "ABCDEF":
            for s in range(3):
                r, t = RT.doc(lay, 5_500_000 + s)
                m = fn(lay, r, t)
                if m:
                    docs.append((m.encode(), None))
    for ph in ["NA+ 138 mEq", "Serum Na 138", "138 mmol / L", "Hb nine point eight", "HIV REACTIVE", "HBsAg POSITIVE"]:
        r = B.make_report("A", random.Random(5_600_000))
        L = G.RENDER["A"](r, G.Opts()).split("\n")
        L.insert(B._end_line(L, "A") + 1, "Ref. By      : " + ph)
        docs.append(("\n".join(L).encode(), None))
        L2 = G.RENDER["A"](r, G.Opts()).split("\n")
        ref = next(j for j, l in enumerate(L2) if r.doctor.upper() in l.upper())
        L2[ref] = L2[ref].replace(r.doctor.upper(), ph.upper())
        docs.append(("\n".join(L2).encode(), None))
    pickle.dump(docs, open(ORACLE, "wb"))
    return len(docs)


def vec(root):
    r = subprocess.run([str(ROOT / ".venv/bin/python"), "-c", RUN, str(root), str(ORACLE)], capture_output=True, text=True, timeout=900)
    return json.loads(r.stdout) if r.returncode == 0 else None


if __name__ == "__main__":
    n = build_oracle()
    print("oracle documents:", n, flush=True)
    re = json.loads((ROOT / "phase2/stage3/results/mutation_v4_recheck.json").read_text())
    surv = re["still_surviving"]
    tmp = Path(tempfile.mkdtemp(prefix="sg_mutx_"))
    shutil.copytree(ROOT / "spoolgeist_h", tmp / "spoolgeist_h", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "bindings_h", tmp / "bindings_h")
    base = vec(tmp)
    out = []
    for k, s in enumerate(surv):
        f = s["file"]
        src = (ROOT / "spoolgeist_h" / f).read_text()
        pts = [p for p in points(src, TARGETS[f]) if p[0] == s["op"] and p[1] == s["line"] and p[4] == s["function"]]
        killed = False
        for p in pts:
            tree = Mut(p[:4]).visit(ast.parse(src)); ast.fix_missing_locations(tree)
            (tmp / "spoolgeist_h" / f).write_text(ast.unparse(tree))
            v = vec(tmp)
            (tmp / "spoolgeist_h" / f).write_text(src)
            diff = None if v is None else [i for i, (a, b) in enumerate(zip(base, v)) if a != b]
            if v is None or diff:
                killed = True
                s["extended_detail"] = "crash" if v is None else f"{len(diff)} docs differ"
                break
        s["killed_by_extended_oracle"] = killed
        out.append(s)
        print(k + 1, len(surv), "KILLED" if killed else "survives", f, s["function"], s["op"], s["line"], flush=True)
    shutil.rmtree(tmp)
    (ROOT / "phase2/stage3/results/mutation_v4_extended.json").write_text(json.dumps(
        {"oracle_docs": n, "checked": len(out), "killed": sum(o["killed_by_extended_oracle"] for o in out),
         "still_surviving": [o for o in out if not o["killed_by_extended_oracle"]]}, indent=1))
    print(json.dumps({"checked": len(out), "killed": sum(o["killed_by_extended_oracle"] for o in out)}))
