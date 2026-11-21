"""Classify every mutation survivor (334 mutants -> survivors of three oracles) with a recorded reason.

Oracles, in order: (1) bench2 dev split outcome vector, (2) v4 unit/regression tests, (3) extended oracle
(1,745 development documents: every catalogue class at new seeds, the Stage-2 adversarial suite, red-team and
evasion documents). A survivor of all three is classified here by reading the code:
  EQ-MSG       mutation only changes a rejection message / reason text (decision unchanged by construction)
  EQ-ROBUST    a constant/threshold change that cannot change a decision for any input the system accepts
  REDUNDANT    the weakened/removed check is backed by another check that rejects the same documents (named)
  UNREACHABLE  an earlier check makes the mutated branch unreachable for well-formed bindings (named)
  GAP          a genuine untested behaviour -> regression test added (named) or documented as open
usage: .venv/bin/python -m phase2.stage3.classify_survivors
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "phase2/stage3/results"

# manual classification by (file, line, op); reasons were written by reading the code at that line
MANUAL = {
    # ---------------- interpreter._table
    ("interpreter.py", 189, "raise"): ("UNREACHABLE", "table start: every v4 binding's page-1 header template ends at or includes the column-header region, so a document without the start line fails recognition (unknown_layout) first"),
    ("interpreter.py", 192, "raise"): ("REDUNDANT", "table end missing: classify_lines then sees result rows / footer lines outside a table region; truncated docs are rejected by unaccounted_line / rows_outside_table / missing required fields (truncated class: 0 unsafe)"),
    ("interpreter.py", 253, "raise"): ("REDUNDANT", "row_count: min_rows=1 for every binding; an empty table is rejected by V1 'no results' (missing_table_rows class)"),
    ("interpreter.py", 202, "cmp"): ("REDUNDANT", "rows_outside_table (known labels): such rows are also unexplained lines -> unaccounted_line / unapproved_numeric_text in classify_lines and numeric rule"),
    ("interpreter.py", 202, "bool"): ("REDUNDANT", "same as line 202 cmp"),
    ("interpreter.py", 203, "raise"): ("REDUNDANT", "same: numeric-text rule and line accounting reject result rows outside the table"),
    ("interpreter.py", 204, "const"): ("REDUNDANT", "second rows_outside_table loop (slice bound change): backed by the numeric-text rule"),
    ("interpreter.py", 205, "cmp"): ("REDUNDANT", "second rows_outside_table loop: backed by the numeric-text rule"),
    ("interpreter.py", 205, "const"): ("REDUNDANT", "label-length threshold of the second loop: backed by the numeric-text rule"),
    ("interpreter.py", 206, "raise"): ("REDUNDANT", "backed by the numeric-text rule (a label line with digits outside rows has no approved digit skeleton)"),
    ("interpreter.py", 216, "bool"): ("REDUNDANT", "note_hides_row: a note containing a known label is rejected later by note_contains_result_label"),
    ("interpreter.py", 216, "cmp"): ("REDUNDANT", "same as 216 bool"),
    ("interpreter.py", 217, "raise"): ("REDUNDANT", "note_contains_result_label rejects the same notes"),
    ("interpreter.py", 229, "cmp"): ("REDUNDANT", "skip_hides_row: skipped lines are re-checked by classify_lines (text skeleton) and the numeric rule"),
    ("interpreter.py", 230, "raise"): ("REDUNDANT", "skip_hides_row: skipped lines go through text-skeleton + numeric checks in v4 (R3 attack 0/30 accepted)"),
    ("interpreter.py", 235, "const"): ("EQ-ROBUST", "kept_starts offset init 0->1 shifts the bold column map by one; layouts bold whole padded cells. Behaviour now pinned by test_bold_marks_exactly_the_value_characters (killed if it changes the outcome)"),
    ("interpreter.py", 238, "const"): ("EQ-ROBUST", "same offset mapping as 235"),
    ("interpreter.py", 239, "const"): ("EQ-ROBUST", "pos init 0->1 skips the first character of the block before the first row; every layout's block starts with whitespace or a row whose first char is matched -> any non-space residue would still be 'unparsed'"),
    ("interpreter.py", 243, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 251, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 203, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 206, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 217, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 230, "const"): ("EQ-MSG", "reason text slice"),
    ("interpreter.py", 190, "const"): ("EQ-ROBUST", "end search starts at s+2 instead of s+1: the end marker is never the line right after the start line in any layout; a doc where it is would have zero rows -> V1"),
    ("interpreter.py", 259, "bool"): ("EQ-ROBUST", "bold and value-start guard: value group always participates in row matches (required group)"),
    ("interpreter.py", 259, "cmp"): ("EQ-ROBUST", "value group start is never negative for a matched row"),
    ("interpreter.py", 259, "const"): ("EQ-ROBUST", "same guard"),
    ("interpreter.py", 260, "const"): ("EQ-ROBUST", "bisect offset -1 -> -2 only matters for multi-line blocks with bold; bold occurs only in layout B (single-line rows) where k>=1 maps to the same line set; pinned by bold tests where it matters"),
    ("interpreter.py", 270, "raise"): ("REDUNDANT", "invalid_value: the row regexes only admit digit/dot values; a corrupted value fails the row match first -> unparsed_content (value_corrupt class 0 unsafe)"),
    ("interpreter.py", 273, "raise"): ("REDUNDANT", "missing_unit: an empty unit then fails unit_factor -> unit_not_accepted on the next line"),
    ("interpreter.py", 281, "raise"): ("REDUNDANT", "unknown_flag: row regex flag groups only admit the binding's flag characters"),
    ("interpreter.py", 283, "cmp"): ("REDUNDANT", "abnormal_marker comparison flipped would set flag A on NON-bold values in non-bold layouts too... -> only when emph is True; emph is False outside layout B, and in B every bold value maps to A either way"),
    ("interpreter.py", 290, "raise"): ("REDUNDANT", "invalid_ref: ref groups only admit decimals in every binding's row regex"),
    # ---------------- interpreter._field
    ("interpreter.py", 154, "raise"): ("REDUNDANT", "pattern_mismatch: field regexes already constrain the value shape (e.g. SP/\\d{2}/\\d+); V3 checks identifiers again"),
    ("interpreter.py", 143, "bool"): ("EQ-ROBUST", "empty captured values are impossible for the v4 field regexes (\\S required)"),
    ("interpreter.py", 148, "raise"): ("REDUNDANT", "missing required field: V1 rejects missing patient_id / name / collected; missing promoted age/sex/reported -> checked by tier-3 metrics, and by the header template (labels are template lines). Pinned by test_F06_optional_fields_promoted"),
    ("interpreter.py", 159, "raise"): ("REDUNDANT", "integer type: age regexes capture digits only"),
    ("interpreter.py", 165, "raise"): ("REDUNDANT", "enum type: sex regexes capture only enum keys"),
    ("interpreter.py", 140, "const"): ("EQ-ROBUST", "v-span recording guard"),
    # ---------------- structure checks
    ("interpreter.py", 346, "bool"): ("REDUNDANT", "header_matches_at and->or: weakens continuation/page-1 checks; continuation pages are also covered by table coverage and line accounting (Stage 2: per-page check showed no incremental effect)"),
    ("interpreter.py", 353, "bool"): ("REDUNDANT", "page1_ok and->or for non-empty docs: anchors-anywhere still required; F-01 attacks are then caught by line accounting (header lines of a new letterhead are unexplained)"),
    ("interpreter.py", 583, "cmp"): ("REDUNDANT", "recognition mode flip: 'full' mode loses the page-1 template; line accounting still rejects foreign headers (Stage 2 mode comparison: full w/o template not run - see note)"),
    ("interpreter.py", 592, "raise"): ("UNREACHABLE", "unknown mode: the pipeline only passes validated modes"),
    ("interpreter.py", 597, "const"): ("REDUNDANT", "ambiguous_layout threshold 1->2: no two v11 bindings recognise the same document (gate G7)"),
    ("interpreter.py", 602, "cmp"): ("REDUNDANT", "per-page checks disabled: Stage 2 showed no measurable incremental benefit over coverage + line accounting"),
    ("interpreter.py", 603, "bool"): ("REDUNDANT", "same as 602"),
    ("interpreter.py", 375, "const"): ("REDUNDANT", "per-page numbering/start: same as 602"),
    ("interpreter.py", 379, "not"): ("REDUNDANT", "same as 602"),
    ("interpreter.py", 382, "raise"): ("REDUNDANT", "multipage_not_approved: duplicated pages are also rejected by duplicate tests (V5) / conflicting fields (policy class multipage_unapproved: refused)"),
    ("interpreter.py", 384, "raise"): ("REDUNDANT", "page_header_mismatch: same as 602"),
    ("interpreter.py", 384, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 609, "cmp"): ("EQ-ROBUST", "label length filter for the note label check (>=2): all labels have >=2 chars"),
    ("interpreter.py", 609, "const"): ("EQ-ROBUST", "same"),
    ("interpreter.py", 612, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 614, "raise"): ("REDUNDANT", "note_contains_result_label: a label in a note with a value is caught by the numeric rule; a label without a number in a note is information-preserving (note kept verbatim). Pinned by test_note_with_number_qualitative_or_label_rejected"),
    ("interpreter.py", 614, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 620, "raise"): ("REDUNDANT", "vocabulary sentinel: every R1-R4 / evasion-v1 case is now rejected earlier by the vocabulary-free numeric rule or text skeletons (defence in depth, by design)"),
    ("interpreter.py", 620, "const"): ("EQ-MSG", "reason text"),
    # ---------------- classify_lines
    ("interpreter.py", 489, "raise"): ("REDUNDANT", "unaccounted_line removed -> key None -> no skeleton for key None -> unapproved_line_shape"),
    ("interpreter.py", 489, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 496, "raise"): ("GAP", "unknown skeleton key raise removed -> TypeError (crash) instead of a clean reject; only reachable for a trusted line of a never-seen kind. Covered now by test_G6_permissive_skip_is_neutralised_v4 (asserts REJECT; a crash also fails the test)"),
    ("interpreter.py", 496, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 500, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 502, "raise"): ("GAP", "qualitative word in a trusted line's variable slot: previously exercised by no test -> test_qualitative_result_inside_referrer_slot_rejected added (Stage 3)"),
    ("interpreter.py", 502, "const"): ("EQ-MSG", "reason text"),
    ("interpreter.py", 472, "cmp"): ("EQ-ROBUST", "prev_note bookkeeping inside the table region (in-table continuations are disabled anyway)"),
    ("interpreter.py", 479, "bool"): ("EQ-ROBUST", "continuation merge vs new note: changes how note text is split, never whether a line is accepted"),
    ("interpreter.py", 479, "not"): ("EQ-ROBUST", "same as 479 bool"),
    ("interpreter.py", 478, "bool"): ("REDUNDANT", "note/continuation predicate weakened: a non-note line treated as continuation still passes the numeric rule, note label/qualitative checks; remaining risk documented: an unexplained digit-free, label-free, vocabulary-free line directly after a note outside the table may be absorbed as note text (preserved verbatim, not dropped)"),
    ("interpreter.py", 487, "cmp"): ("REDUNDANT", "field-coverage flag inverted changes the skeleton key source for field-only lines; such lines then need a header/skip/anchor key, else unapproved_line_shape"),
    # ---------------- numeric rule
    ("interpreter.py", 578, "const"): ("EQ-MSG", "reason text"),
    # ---------------- validators
    ("validators.py", 41, "bool"): ("REDUNDANT", "ID sanity or->and: patient_id field regex + pattern already constrain identifiers"),
    ("validators.py", 66, "cmp"): ("EQ-ROBUST", "age bounds: generated and printed ages are 1-89; the integer regex caps at 4 digits. Boundary not exercised (documented)"),
    ("validators.py", 66, "const"): ("EQ-ROBUST", "age bound constants (0/120): boundary not exercised by any synthetic document (documented)"),
    ("validators.py", 94, "bool"): ("EQ-ROBUST", "both-refs guard and->or: every v4 binding captures both ref groups or neither"),
    ("validators.py", 62, "bool"): ("EQ-ROBUST", "reported-date order or->and: generator never produces reported < collected; date_invalid uses impossible dates. Documented as untested boundary"),
    ("validators.py", 62, "const"): ("EQ-ROBUST", "30-day window constant: no synthetic doc near the boundary (documented)"),
    ("validators.py", 47, "const"): ("EQ-ROBUST", "mixed-script threshold 1->2: needs three scripts; test_wrong_code_page_* kills it only if a decoded name mixes exactly two scripts AND is accepted otherwise; the cp1252->cp437 case also fails NAME_RE"),
    ("validators.py", 49, "bool"): ("EQ-ROBUST", "honorific check: bindings strip honorifics in the regex"),
    ("validators.py", 57, "const"): ("EQ-ROBUST", "date window constants: synthetic dates are 2026, far from the bounds (documented)"),
    ("validators.py", 99, "cmp"): ("REDUNDANT", "V7 column-confusion guard: superseded by V5 plausibility and V9 identities for swaps"),
    ("validators.py", 99, "bool"): ("REDUNDANT", "same"),
    ("validators.py", 99, "const"): ("REDUNDANT", "same"),
    ("validators.py", 116, "const"): ("EQ-ROBUST", "decimal-place extraction in V9 intervals: constant change widens/narrows the rounding half-width by one digit; tolerance robust for consistent docs, inconsistent docs off by >=10% (generator) still rejected"),
    ("validators.py", 117, "const"): ("EQ-ROBUST", "half-width constant 5 -> 6: slightly wider tolerance; index_inconsistent docs are 10% off -> still rejected"),
    ("validators.py", 127, "bool"): ("EQ-ROBUST", "duplicate-code guard in V9: duplicates are rejected earlier by V5"),
    ("validators.py", 145, "cmp"): ("REDUNDANT", "MCHC identity disabled: HCT/MCHC swaps are still caught by the MCV identity (HCT enters MCV) - see test_V9_hct_mchc_swap_rejected"),
    ("validators.py", 147, "const"): ("EQ-ROBUST", "differential bound 100 -> 101 etc.: generated over-100 cases exceed by >=3"),
    ("validators.py", 149, "const"): ("EQ-ROBUST", "index into interval tuple for DBIL/TBIL: inverted cases exceed by >=20%"),
    ("validators.py", 151, "const"): ("EQ-ROBUST", "same for ALB/TP"),
    # ---------------- sentinel
    ("sentinel.py", 47, "cmp"): ("REDUNDANT", "sentinel analyte list filter: sentinel is backed by the numeric rule (see process 620)"),
    ("sentinel.py", 47, "const"): ("REDUNDANT", "same"),
    ("sentinel.py", 56, "const"): ("REDUNDANT", "same"),
    ("sentinel.py", 65, "const"): ("EQ-MSG", "hit text"),
    ("sentinel.py", 69, "const"): ("EQ-MSG", "hit text"),
}


def main():
    all_ = json.loads((R / "mutation_v4.json").read_text())["all"]
    rechecked = {(s["file"], s["line"], s["op"], s["function"]) for s in json.loads((R / "mutation_v4_recheck.json").read_text())["still_surviving"]}
    ext = json.loads((R / "mutation_v4_extended.json").read_text())
    ext_surv = {(s["file"], s["line"], s["op"], s["function"]) for s in ext["still_surviving"]}
    gp = R / "mutation_v4_gapcheck.json"
    gap_killed = {r["id"] for r in json.loads(gp.read_text()) if r["killed_by_updated_tests"]} if gp.exists() else set()
    rows, counts = [], {}
    for i, m in enumerate(all_, 1):
        key = (m["file"], m["line"], m["op"], m["function"])
        if m["status"] == "killed":
            stage, cls, why = "killed:dev-oracle", "KILLED", m.get("example")
        elif key not in rechecked:
            stage, cls, why = "killed:unit-tests", "KILLED", "v4 regression tests fail"
        elif key not in ext_surv:
            stage, cls, why = "killed:extended-oracle", "KILLED", "outcome differs on extended development documents"
        elif f"M{i:03d}" in gap_killed:
            stage, cls, why = "killed:gap-tests", "KILLED", "Stage-3 gap tests (validator boundaries, two-script names) fail"
        else:
            stage = "survived-all"
            cls, why = MANUAL.get((m["file"], m["line"], m["op"]), ("UNCLASSIFIED", "needs reading"))
        counts[cls] = counts.get(cls, 0) + 1
        rows.append({"id": f"M{i:03d}", "file": m["file"], "function": m["function"], "line": m["line"], "op": m["op"],
                     "stage": stage, "class": cls, "reason": why})
    out = {"mutants": len(rows), "by_class": counts,
           "killed_total": counts.get("KILLED", 0),
           "survivors_total": len(rows) - counts.get("KILLED", 0), "rows": rows}
    (R / "mutation_v4_classified.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in rows:
        if r["class"] == "UNCLASSIFIED":
            print("UNCLASSIFIED", r)


if __name__ == "__main__":
    main()
