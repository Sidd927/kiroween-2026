"""AI rule generation + activation gate + bounded repair loop.

Flow for a new, unfamiliar layout:
  1. generate: LLM sees ONLY the 2 synthetic 'gen' samples + schema + dictionary -> candidate Binding
  2. static checks (schema, regex compile, required groups, codes exist, permissive-skip guard)
  3. gate on gen + dev documents (dev = operator-verified regression set with expected outputs)
  4. on failure: repair prompt with diagnostics (max 3 rounds)
  5. 'human approval' is SIMULATED in the PoC (recorded as such) -> status active, SHA-256 pinned
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from . import llm
from .dictionary import DICT
from .grid import normalize
from .interpreter import SCHEMA, process, recognise, static_check

ROOT = Path(__file__).resolve().parents[1]

INTERPRETER_RULES = """
How the deterministic interpreter executes your Binding (it is fail-closed; any failure rejects the whole document):
- Input is the normalised text of a printed report: printer control codes removed, form feeds turned into newlines,
  trailing spaces stripped, tabs expanded. Lines keep their original column positions.
- All regexes use the Python `regex` module, MULTILINE mode (^ and $ match at line boundaries). No DOTALL.
- Layout identification: the document belongs to this layout only if EVERY regex in layout.anchors matches somewhere.
  Anchors must be STATIC text present in every report of this layout (lab name, fixed labels, column headers) — never
  patient data, dates or results. They must be specific enough not to match other labs' reports.
- Header fields: each field regex is searched over the WHOLE text with finditer; the named group `v` is captured and
  whitespace-collapsed. If there is no match and the field is required -> reject. If matches give DIFFERENT values
  -> reject (ambiguous). Identical repeats (e.g. a page header repeated on page 2) are fine. `pattern` (optional) must
  FULLY match the captured value. type=date uses Python strptime with `format`; type=integer needs plain digits;
  type=enum maps through enum_map.
- Results table: the interpreter finds the first line matching `start`, then the first later line matching `end`
  (missing end -> reject as truncated). Lines strictly between them are kept unless a `skip_lines` regex matches the
  line. The kept lines are joined with "\\n" and `row` is applied with finditer. EVERY non-whitespace character of the
  kept text must be inside some row match, otherwise the document is rejected (so unexpected content is never
  silently dropped). `row` must have named groups label, value, unit and may have flag, ref_low, ref_high.
  A row match may span lines (write \\n explicitly). Several rows may share one line.
- For each row: label is whitespace-collapsed and must be a key of `labels` (exact string) -> canonical code.
  value must be a plain decimal like 13.5 or 7800 (no letters, no commas). unit must be non-empty and must be one of
  the accepted spellings for that code in the dictionary (exact string). flag text (if captured and non-empty) must be
  a key of `flags`. ref_low/ref_high, if captured, must be plain decimals. Row count must be within [min_rows, max_rows].
- Units must come from the document itself. Never hard-code a unit.
"""

TARGET_FIELDS = """
Target fields:
- patient_id   (required, string): the lab's patient / registration identifier as printed (labels such as Lab No, Reg No,
                UHID, MRN, Patient ID, Lab ID). Not the sample/accession number. Add a `pattern` describing its format.
- patient_name (required, string): the patient's name exactly as printed (keep the printed order and punctuation),
                EXCLUDING honorifics/titles such as MR., MRS., MS., SMT., SHRI, KUM., DR., BABY.
- patient_age  (optional, integer years) ; patient_sex (optional, enum -> "male"/"female")
- collected    (required, date): when the sample was collected/drawn. Capture date (and time if printed) and give the
                exact strptime format.
- reported     (optional, date): report date, if printed.
"""

GENERALISE = """
Your Binding will be applied to MANY future reports of the same layout that you have not seen. Expect differences in:
patient names (short or very long, multi-part, hyphenated), IDs, dates, numeric values (more or fewer digits, with or
without an abnormal flag), optional rows that may be absent, and the results table possibly continuing onto another
page with the page header and column header repeated. Do not over-fit to the sample values. Prefer patterns based on
the column separators/labels of the layout over exact column positions. Reports that are malformed, ambiguous or of a
different layout must be rejected, so keep the anchors, row pattern and label map strict.
"""


def dictionary_text() -> str:
    lines = []
    for code, s in DICT["tests"].items():
        lines.append(f"{code}: {s['display']} | accepted unit spellings: {', '.join(repr(u) for u in s['units'])}")
    return "\n".join(lines)


def gen_prompt(samples: List[str], layout_hint: str) -> str:
    sample_txt = "\n\n".join(f"<sample index=\"{i + 1}\">\n{s}\n</sample>" for i, s in enumerate(samples))
    return f"""You write a declarative parsing rule ("Binding") for ONE printed laboratory-report layout from an old
lab system. The Binding is JSON that must validate against this JSON Schema:

```json
{json.dumps(SCHEMA, indent=1)}
```
{INTERPRETER_RULES}
{TARGET_FIELDS}
Canonical test dictionary (labels map to these codes; units must be one of the accepted spellings):
{dictionary_text()}
{GENERALISE}
Use binding_id "{layout_hint}". Here are {len(samples)} synthetic sample reports of this layout (normalised text):

{sample_txt}

Return ONLY the Binding JSON object, nothing else."""


def repair_prompt(binding: dict, failures: List[dict], samples: List[str], layout_hint: str) -> str:
    fl = []
    for f in failures[:8]:
        fl.append(f"--- document {f['doc_id']} (expected: {f['expected']}; got: {f['status']})\n"
                  f"problem: {f['problem']}\n<document>\n{f['text']}\n</document>")
    return gen_prompt(samples, layout_hint).replace(
        "Return ONLY the Binding JSON object, nothing else.", "") + f"""
A previous version of the Binding was tested against operator-verified regression documents and FAILED.

Previous Binding:
```json
{json.dumps(binding, indent=1)}
```
Failures:
{chr(10).join(fl)}

Fix the Binding so that valid documents are extracted exactly and invalid/ambiguous ones are rejected.
Return ONLY the corrected Binding JSON object, nothing else."""


def describe_failure(doc: dict, oc, cls: str) -> str:
    from bench.score import field_checks
    if cls == "false_reject":
        return f"valid document was rejected: {oc.reasons}"
    if cls == "silent_error":
        chk = field_checks(oc.record, doc["truth"])
        bad = [k for k, v in chk.items() if k.startswith("crit:") and not v]
        exp = {k: doc["truth"].get(k.replace("crit:", "")) for k in bad if not k.startswith("crit:result")}
        got = {k: oc.record.get(k.replace("crit:", "")) for k in bad if not k.startswith("crit:result")}
        res_exp = [r for r in doc["truth"]["results"] if f"crit:result:{r['code']}" in bad]
        res_got = [r for r in oc.record["results"] if f"crit:result:{r['code']}" in bad or f"crit:result_extra:{r['code']}" in bad]
        return (f"accepted but WRONG. wrong fields={bad}; expected={exp} got={got}; "
                f"expected rows={[(r['label'], r['value'], r['unit']) for r in res_exp]} "
                f"got rows={[(r['label'], r['value'], r['unit']) for r in res_got]}")
    if cls == "unsafe_accept":
        return (f"document is invalid/ambiguous ({doc['perturbation'].replace('_', ' ')}) and must be rejected, "
                f"but it was accepted")
    return ""


def evaluate(binding: dict, docs: List[dict], others: List[dict] = ()) -> Tuple[Counter, List[dict]]:
    from bench.score import classify
    counts, failures = Counter(), []
    for d in docs:
        text = normalize(d["text"].encode()).text
        oc = process([binding], text)
        cls = classify(oc.status, oc.record, d)
        counts[(d["perturbation"] == "clean", cls)] += 1
        if cls in ("silent_error", "unsafe_accept", "false_reject"):
            failures.append({"doc_id": d["doc_id"], "expected": d["expected"], "status": oc.status,
                             "problem": describe_failure(d, oc, cls), "text": text, "cls": cls})
    for od in others:  # collision check: must not recognise other layouts' documents
        if recognise([binding], normalize(od["text"].encode()).text):
            failures.append({"doc_id": od["doc_id"], "expected": "not this layout", "status": "recognised",
                             "problem": "anchors also match a report from a DIFFERENT lab layout; make anchors more specific",
                             "text": normalize(od["text"].encode()).text, "cls": "collision"})
    return counts, failures


def gate_passes(counts: Counter, failures: List[dict], n_clean_dev: int) -> bool:
    unsafe = sum(1 for f in failures if f["cls"] in ("silent_error", "unsafe_accept", "collision"))
    clean_ok = counts[(True, "correct_accept")]
    return unsafe == 0 and clean_ok >= int(0.9 * n_clean_dev)


def generate_and_activate(layout: str, gen_docs: List[dict], dev_docs: List[dict], other_docs: List[dict],
                          max_repairs: int = 3, model: str = "sonnet") -> dict:
    samples = [normalize(d["text"].encode()).text for d in gen_docs]
    hint = f"lab-{layout.lower()}"
    history = []
    prompt = gen_prompt(samples, hint)
    binding = None
    for rnd in range(max_repairs + 1):
        resp = llm.call(prompt, samples, purpose=f"rulegen:{layout}:round{rnd}", model=model)
        try:
            binding = llm.extract_json(resp["text"])
        except Exception as e:
            history.append({"round": rnd, "error": f"unparseable JSON: {e}", "seconds": resp["seconds"]})
            prompt = gen_prompt(samples, hint) + "\nYour previous answer was not valid JSON. Return only JSON."
            continue
        errs = static_check(binding)
        if errs:
            failures = [{"doc_id": "static-check", "expected": "valid binding", "status": "invalid",
                         "problem": "; ".join(errs), "text": "(n/a)", "cls": "static"}]
            history.append({"round": rnd, "static_errors": errs, "seconds": resp["seconds"]})
            prompt = repair_prompt(binding, failures, samples, hint)
            continue
        counts, failures = evaluate(binding, gen_docs + dev_docs, other_docs)
        n_clean = sum(1 for d in gen_docs + dev_docs if d["perturbation"] == "clean")
        ok = gate_passes(counts, failures, n_clean)
        history.append({"round": rnd, "seconds": round(resp["seconds"], 1), "passed": ok,
                        "counts": {f"{'clean' if k[0] else 'perturbed'}:{k[1]}": v for k, v in counts.items()},
                        "failures": [{k: f[k] for k in ("doc_id", "cls", "problem")} for f in failures]})
        if ok:
            break
        # repair feedback: the dev docs are synthetic and operator-verified; the held-out TEST split is never shown
        llm.presend_guard([f["text"] for f in failures if f["text"] != "(n/a)"])
        prompt = repair_prompt(binding, failures, samples, hint)
    passed = bool(history and history[-1].get("passed"))
    result = {"layout": layout, "binding_id": hint, "activated": passed, "rounds_used": len(history) - 1,
              "history": history, "llm_calls": len(history)}
    if binding is not None:
        canon = json.dumps(binding, sort_keys=True).encode()
        result["sha256"] = hashlib.sha256(canon).hexdigest()
        result["status"] = "active" if passed else "rejected-candidate"
        result["approval"] = ("SIMULATED human approval (PoC): gate passed, binding reviewed by no human"
                              if passed else "not approved: gate failed")
        out = ROOT / "bindings" / f"{hint}.v1.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps({"_meta": {k: result[k] for k in ("status", "sha256", "approval", "rounds_used")},
                                   **binding}, indent=1))
    return result
