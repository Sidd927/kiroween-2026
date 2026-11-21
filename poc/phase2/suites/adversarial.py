"""Phase 2 adversarial regression suite (R-ANCHOR + brief §4.3).

Written BEFORE any Stage-2 fix and run first against the frozen v2.1 system ("before" state).
The suite uses only the frozen v2.1 generator (bench/generator.py) for rendering and ground truth, plus
text transforms defined here. It knows nothing about any binding.

Property under test (unchanged from the PoC, not weakened):
  * a document with a detectable defect must be REJECTED;
  * an ACCEPTED document must have every critical field exactly equal to ground truth.

Every case carries: layout, class, group (valid|invalid), expected, truth (valid only), truth_if_page1 (invalid
cases where a page-1 truth exists, used to report whether an unsafe accept also carried wrong data).

usage (from poc/):  .venv/bin/python -m phase2.suites.adversarial --system v2.1|v3 [--tag TAG]
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from bench import generator as G          # noqa: E402
from bench.score import field_checks      # noqa: E402

OUT = ROOT / "phase2" / "stage2" / "results"
LAYOUTS = list("ABCDEF")
N = 6   # documents per (layout, class)

# generator-knowledge keywords (suite side only; the system never sees these)
END_KW = {"A": "END OF REPORT", "B": "End of Report", "C": "-- END --", "D": "End of Report",
          "E": "Report generated", "F": "END OF REPORT"}
COLHDR_KW = {"A": "REFERENCE RANGE", "B": "Biological Ref.", "C": "Test / Method", "D": "PARAMETER",
             "E": "HAEMOGRAM", "F": "TEST NAME (UNITS)"}
LASTCOL_KW = {"A": "REFERENCE RANGE", "B": "Biological Ref.", "C": "Normal Range", "D": "FLAG",
              "E": "HAEMOGRAM", "F": "REF"}
TITLE_NEW = {"A": "SUNRISE DIAGNOSTICS & PATHOLOGY PVT. LTD.", "B": "CITY DIAGNOSTICS (A UNIT OF CDC HEALTHCARE)",
             "C": "MEHTA PATHCARE DIAGNOSTICS LLP", "D": "SHREE SAI HEALTH LABS (NEW FORMAT)",
             "E": "LIFELINE LABS - DIGITAL REPORT", "F": "MEDILINK LABORATORIES INC"}
FAKE = G.Result("XNA", "SERUM SODIUM", "138", "mmol/L", "135", "145", "", "ISE method")


# ----------------------------------------------------------------------------- helpers
def report(lay, seed, paged=False, **opts):
    rng = random.Random(seed)
    r = G.make_report(lay, rng)
    o = G.Opts(**opts)
    if paged:
        if lay not in G.PAGEABLE or len(r.results) < 4:
            return None
        o.page_break_after = rng.randint(2, len(r.results) - 2)
    return r, o, rng


def render(r, o):
    return G.RENDER[r.layout](r, o)


def crit_ok(rec, truth):
    return all(v for k, v in field_checks(rec, truth).items() if k.startswith("crit:"))


def row_lines(r, o, res):
    """Rendered lines for result list `res` in r's layout (lines present with res, absent without)."""
    r0, r1 = copy.deepcopy(r), copy.deepcopy(r)
    r0.results, r1.results = [], list(res)
    o2 = copy.deepcopy(o)
    o2.page_break_after = None
    base = Counter(render(r0, o2).split("\n"))
    out = []
    for ln in render(r1, o2).split("\n"):
        if base[ln] > 0:
            base[ln] -= 1
        else:
            out.append(ln)
    return out


def idx_kw(lines, kw):
    return next(i for i, l in enumerate(lines) if kw in l)


def first_row_end(lines, r):
    i = idx_kw(lines, r.results[0].label) if r.layout != "E" else idx_kw(lines, r.results[0].label + " ")
    return i + 2 if r.layout == "C" else i


TITLE = {"A": "SUNRISE PATHOLOGY LABORATORY", "B": "CITY DIAGNOSTIC CENTRE", "C": "DR. MEHTA'S CLINICAL LABORATORY",
         "D": "SHREE SAI DIAGNOSTICS", "E": "LIFELINE PATHOLOGY & IMAGING", "F": "MEDILINK REFERENCE LAB"}


def split_pages(text, lay):
    """Pages by form feed if present. The frozen generator's L() strips stand-alone "\f" lines, so layouts B, D
    and F print continuation pages WITHOUT a form feed (continuous paper); split those at the repeated header."""
    if "\f" in text:
        return text.split("\f"), "\f"
    lines = text.split("\n")
    occ = [i for i, l in enumerate(lines) if TITLE[lay] in l]
    if len(occ) < 2:
        return [text], "\n"
    first_nb = next(i for i, l in enumerate(lines) if l.strip())
    cut = occ[1] - (occ[0] - first_nb)
    return ["\n".join(lines[:cut]), "\n".join(lines[cut:])], "\n"


def replace_nth(text, old, new, n):
    pos = -1
    for _ in range(n):
        pos = text.find(old, pos + 1)
        if pos < 0:
            return None
    return text[:pos] + new + text[pos + len(old):]


def case(lay, cls, group, text, truth=None, truth_if_page1=None, seed=None, note=""):
    return {"id": f"{cls}:{lay}:{seed}", "layout": lay, "cls": cls, "group": group,
            "expected": "accept" if group == "valid" else "reject", "truth": truth,
            "truth_if_page1": truth_if_page1, "text": text, "note": note}


# ----------------------------------------------------------------------------- valid controls
def valid_cases():
    out = []
    for li, lay in enumerate(LAYOUTS):
        for ci, p in enumerate([None, "page_break", "col_shift", "crlf_trailing", "drop_optional", "long_name"]):
            k = 0
            for s in range(40):
                if k >= (2 * N if p is None else N):
                    break
                seed = 700_000 + li * 10_000 + ci * 100 + s
                rng = random.Random(seed)
                r = G.make_report(lay, rng)
                o, op = G.Opts(), None
                if p:
                    res = G.PERTURBATIONS[p](r, o, rng)
                    if res is None:
                        continue
                    r, o, _, op = res
                text = G.apply_text_op(render(r, o), op, r, rng)
                out.append(case(lay, f"V_{p or 'clean'}", "valid", text, truth=G.truth(r), seed=seed))
                k += 1
    return out


# ----------------------------------------------------------------------------- invalid / adversarial
def orig_unsafe_cases():
    """The 7 v2 property-test unsafe accepts (6 distinct docs + the digit_change twin), rebuilt exactly."""
    import test_property_abstain_or_correct as T
    specs = [(0, ["crlf_trailing", "page_break"], []), (519528913, ["col_shift", "page_break", "long_name"], []),
             (41255, ["page_break", "col_shift", "long_name"], []), (890454084, ["page_break"], ["static_char_damage"]),
             (541, ["crlf_trailing", "page_break"], ["digit_change"]), (541, ["crlf_trailing", "page_break"], []),
             (124145097, ["long_name", "crlf_trailing", "page_break"], []), (5208, ["page_break"], ["digit_change"])]
    out = []
    for seed, valid, fuzz in specs:
        d = T.build("A", seed, valid, "header_changed", fuzz)
        out.append(case("A", "X_orig_pbt_unsafe", "invalid", d["text"], truth_if_page1=d["truth_if_valid"],
                        seed=f"{seed}:{'+'.join(valid + fuzz)}"))
    return out


def invalid_cases():
    out = []
    builders = {}

    def reg(name):
        def deco(fn):
            builders[name] = fn
            return fn
        return deco

    @reg("X_new_header")
    def _(lay, seed):
        r, o, _ = report(lay, seed, new_header=True)
        return render(r, o), G.truth(r)

    @reg("X_new_header_old_continuation")
    def _(lay, seed):
        x = report(lay, seed, paged=True, new_header=True)
        if not x:
            return None
        r, o, _ = x
        t = render(r, o)
        # make the continuation page carry the OLD header for every pageable layout (A already does)
        r2, o2 = copy.deepcopy(r), copy.deepcopy(o)
        o2.new_header = False
        old, sep = split_pages(render(r2, o2), lay)
        new, _ = split_pages(t.replace(TITLE_NEW[lay], TITLE[lay]), lay)   # locate pages via the old title
        new[0] = new[0].replace(TITLE[lay], TITLE_NEW[lay])
        if len(old) < 2 or len(new) < 2:
            return None
        return sep.join([new[0]] + old[1:]), G.truth(r)

    # --- suite v1.1 (added after the first v3 mode comparison showed no case isolating per-page checks;
    #     run against v2.1 as well, see EXPERIMENT_LOG)
    @reg("X_new_header_on_continuation_only")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, _ = x
        old, sep = split_pages(render(r, o), lay)
        o2 = copy.deepcopy(o)
        o2.new_header = True
        new, _ = split_pages(render(r, o2).replace(TITLE_NEW[lay], TITLE[lay]), lay)
        if len(old) < 2 or len(new) < 2:
            return None
        return sep.join([old[0]] + [p.replace(TITLE[lay], TITLE_NEW[lay]) for p in new[1:]]), G.truth(r)

    @reg("X_foreign_page_inserted")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, _ = x
        pages, sep = split_pages(render(r, o), lay)
        if len(pages) < 2:
            return None
        rg, og, _ = report("G", seed + 3)
        return sep.join([pages[0], render(rg, og).rstrip("\f\n")] + pages[1:]), G.truth(r)

    @reg("X_title_replaced_page1_only")
    def _(lay, seed):
        x = report(lay, seed, paged=lay in G.PAGEABLE)
        if not x:
            return None
        r, o, _ = x
        t = render(r, o)
        title = {"A": "SUNRISE PATHOLOGY LABORATORY", "B": "CITY DIAGNOSTIC CENTRE", "C": "DR. MEHTA'S CLINICAL LABORATORY",
                 "D": "SHREE SAI DIAGNOSTICS", "E": "LIFELINE PATHOLOGY & IMAGING", "F": "MEDILINK REFERENCE LAB"}[lay]
        new = "NEW LIFE DIAGNOSTIC CENTRE"[:len(title)].ljust(len(title))
        return t.replace(title, new, 1), G.truth(r)

    @reg("X_old_header_page_appended")
    def _(lay, seed):
        r, o, _ = report(lay, seed, new_header=True)
        o2 = copy.deepcopy(o)
        o2.new_header = False
        old = render(r, o2).split("\n")
        k = idx_kw(old, COLHDR_KW[lay])
        return render(r, o).rstrip("\f\n") + "\n\f" + "\n".join(old[:k]), G.truth(r)

    @reg("X_foreign_with_old_header_page")
    def _(lay, seed):
        rg, og, _ = report("G", seed)
        r, o, _ = report(lay, seed + 1)
        old = render(r, o).split("\n")
        k = idx_kw(old, COLHDR_KW[lay])
        return render(rg, og).rstrip("\f\n") + "\n\f" + "\n".join(old[:k]), None

    @reg("X_page_order_swap")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, _ = x
        p, sep = split_pages(render(r, o), lay)
        if len(p) < 2:
            return None
        return sep.join([p[1], p[0]] + p[2:]), G.truth(r)

    @reg("X_conflicting_id_later_page")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, rng = x
        other = G.make_report(lay, random.Random(seed + 77)).patient_id
        t = replace_nth(render(r, o), r.patient_id, other, 2)
        return (t, G.truth(r)) if t else None

    @reg("X_conflicting_name_later_page")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, rng = x
        r2 = G.make_report(lay, random.Random(seed + 78))
        nm, nm2 = G.printed_name(r), G.printed_name(r2)
        if nm == nm2:
            return None
        t = replace_nth(render(r, o), nm, nm2, 2)
        return (t, G.truth(r)) if t else None

    @reg("X_repeated_row_identical")
    def _(lay, seed):
        r, o, rng = report(lay, seed)
        i = rng.randrange(len(r.results))
        r.results.insert(i + 1, copy.deepcopy(r.results[i]))
        return render(r, o), None

    @reg("X_repeated_row_on_continuation")
    def _(lay, seed):
        x = report(lay, seed, paged=True)
        if not x:
            return None
        r, o, _ = x
        b = o.page_break_after
        r.results.insert(b, copy.deepcopy(r.results[b - 1]))
        return render(r, o), None

    @reg("X_missing_table_rows")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        r.results = []
        return render(r, o), None

    @reg("X_extra_section_after_end_unknown_tests")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        lines = render(r, o).split("\n")
        i = idx_kw(lines, END_KW[lay])
        return "\n".join(lines[:i + 1] + ["ELECTROLYTES"] + row_lines(r, o, [FAKE]) + lines[i + 1:]), G.truth(r)

    @reg("X_extra_section_after_end_known_tests")
    def _(lay, seed):
        r, o, rng = report(lay, seed)
        x = copy.deepcopy(r.results[0])
        x.value = G.fmt_num(float(x.value) * 1.1 + 1, len(x.value.split(".")[1]) if "." in x.value else 0)
        lines = render(r, o).split("\n")
        i = idx_kw(lines, END_KW[lay])
        return "\n".join(lines[:i + 1] + ["REPEAT TEST"] + row_lines(r, o, [x]) + lines[i + 1:]), G.truth(r)

    @reg("X_extra_section_before_table_unknown_tests")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        lines = render(r, o).split("\n")
        i = idx_kw(lines, COLHDR_KW[lay])
        return "\n".join(lines[:i] + ["ELECTROLYTES"] + row_lines(r, o, [FAKE]) + [""] + lines[i:]), G.truth(r)

    @reg("X_columns_reordered")
    def _(lay, seed):
        r, o, _ = report(lay, seed, swap_value_ref=True)
        return render(r, o), G.truth(r)

    @reg("X_value_unit_swapped")
    def _(lay, seed):
        if lay == "F":
            return None   # unit is printed inside the test name; no value/unit adjacency to swap
        r, o, _ = report(lay, seed)
        t = render(r, o)
        n = 0
        for x in r.results:
            pat = re.compile(re.escape(x.value) + r"(\s+(?:[HL!*]\s+)?(?:\x1bF)?)" + re.escape(x.unit) + r"(?=\s|$)")
            t2 = pat.sub(lambda m: x.unit + m.group(1) + x.value, t, count=1)
            n += t2 != t
            t = t2
        return (t, G.truth(r)) if n else None

    @reg("X_truncated_column_header")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        lines = render(r, o).split("\n")
        kw = LASTCOL_KW[lay]
        i = idx_kw(lines, kw)
        j = lines[i].index(kw)
        lines[i] = (lines[i][:j] + kw[: max(1, len(kw) // 2)]).rstrip() if lay == "E" else lines[i][:j].rstrip()
        return "\n".join(lines), G.truth(r)

    @reg("X_missing_unit")
    def _(lay, seed):
        r, o, rng = report(lay, seed)
        res = G.p_unit_missing(r, o, rng)
        return render(r, o), None

    @reg("X_text_between_rows")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        lines = render(r, o).split("\n")
        i = first_row_end(lines, r)
        return "\n".join(lines[:i + 1] + ["Lot 4471 calibrated 12/03/2026"] + lines[i + 1:]), G.truth(r)

    @reg("X_unknown_result_between_rows")
    def _(lay, seed):
        r, o, _ = report(lay, seed)
        lines = render(r, o).split("\n")
        i = first_row_end(lines, r)
        return "\n".join(lines[:i + 1] + row_lines(r, o, [FAKE]) + lines[i + 1:]), G.truth(r)

    @reg("X_two_patients_one_job")
    def _(lay, seed):
        r1, o1, _ = report(lay, seed)
        r2, o2, _ = report(lay, seed + 5000)
        return render(r1, o1) + "\n" + render(r2, o2), G.truth(r1)

    @reg("X_same_patient_two_reports")
    def _(lay, seed):
        r1, o1, _ = report(lay, seed)
        r2, o2, _ = report(lay, seed + 6000)
        for k in ("patient_id", "title", "first", "last", "age", "sex"):
            setattr(r2, k, getattr(r1, k))
        return render(r1, o1) + "\n" + render(r2, o2), G.truth(r1)

    for li, lay in enumerate(LAYOUTS):
        for ci, (name, fn) in enumerate(builders.items()):
            k = 0
            for s in range(60):
                if k >= N:
                    break
                seed = 800_000 + li * 10_000 + ci * 100 + s
                res = fn(lay, seed)
                if res is None:
                    continue
                text, t1 = res
                out.append(case(lay, name, "invalid", text, truth_if_page1=t1, seed=seed))
                k += 1
    return out


def build_suite():
    return valid_cases() + orig_unsafe_cases() + invalid_cases()


# ----------------------------------------------------------------------------- systems
def system(name):
    if name == "v2.1":
        from bench.run_benchmark import load_bindings
        from spoolgeist import interpreter, llm
        from spoolgeist.grid import normalize
        llm.FORBID["enabled"] = True
        B = load_bindings()

        def run(text):
            oc = interpreter.process(B, normalize(text.encode()).text)
            return oc.status, oc.binding_id, oc.record, oc.reasons
        return run
    if name.startswith("v3"):
        mode = name.split(":", 1)[1] if ":" in name else "full"
        from spoolgeist_h import pipeline
        P = pipeline.Pipeline(recognition=mode, allow_agent_approval=True)

        def run(text):
            oc = P.process_bytes(text.encode())
            return oc.status, oc.binding_id, oc.record, oc.reasons
        return run
    raise SystemExit(name)


def evaluate(run, cases):
    rows = []
    for c in cases:
        t0 = time.perf_counter()
        status, bid, rec, reasons = run(c["text"])
        ms = (time.perf_counter() - t0) * 1000
        row = {"id": c["id"], "layout": c["layout"], "cls": c["cls"], "group": c["group"], "status": status,
               "binding": bid, "reason": (reasons or [""])[0][:120], "ms": round(ms, 3)}
        if c["group"] == "valid":
            row["outcome"] = ("correct_accept" if crit_ok(rec, c["truth"]) else "silent_error") if status == "ACCEPT" else "false_reject"
            if status == "ACCEPT":
                row["recognised_ok"] = bid == f"lab-{c['layout'].lower()}"
        else:
            if status == "ACCEPT":
                row["outcome"] = "unsafe_accept"
                row["data_matches_page1_truth"] = bool(c["truth_if_page1"]) and crit_ok(rec, c["truth_if_page1"])
            else:
                row["outcome"] = "correct_reject"
        rows.append(row)
    return rows


def summarise(rows):
    by = defaultdict(Counter)
    for r in rows:
        by[(r["group"], r["cls"])][r["outcome"]] += 1
        by[(r["group"], r["cls"])]["n"] += 1
        if r["outcome"] == "unsafe_accept" and not r.get("data_matches_page1_truth"):
            by[(r["group"], r["cls"])]["unsafe_accept_wrong_or_unknown_data"] += 1
    tot = Counter()
    for r in rows:
        tot[(r["group"], r["outcome"])] += 1
    return {"per_class": {f"{g}:{c}": dict(v) for (g, c), v in sorted(by.items())},
            "totals": {f"{g}:{o}": v for (g, o), v in sorted(tot.items())}}


def table(summary):
    lines = ["| class | n | correct | unsafe/silent | false reject |", "|---|---:|---:|---:|---:|"]
    for k, v in summary["per_class"].items():
        bad = v.get("unsafe_accept", 0) + v.get("silent_error", 0)
        good = v.get("correct_reject", 0) + v.get("correct_accept", 0)
        lines.append(f"| {k} | {v['n']} | {good} | {'**' + str(bad) + '**' if bad else 0} | {v.get('false_reject', 0)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", default="v2.1")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    cases = build_suite()
    rows = evaluate(system(a.system), cases)
    s = summarise(rows)
    s["system"], s["cases"] = a.system, len(cases)
    tag = a.tag or a.system.replace(":", "_")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"adv_{tag}_rows.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (OUT / f"adv_{tag}_summary.json").write_text(json.dumps(s, indent=1))
    (OUT / f"adv_{tag}_failures.json").write_text(json.dumps(
        [{**r, "text": next(c["text"] for c in cases if c["id"] == r["id"])} for r in rows
         if r["outcome"] in ("unsafe_accept", "silent_error")][:60], indent=1))
    print(table(s))
    print(json.dumps(s["totals"]))
