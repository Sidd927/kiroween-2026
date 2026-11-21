"""Accepted record -> FHIR R4 document Bundle.

Two variants are produced from the same record:
  generic : plain FHIR R4 resources, no profile claims (validated against the base R4 spec only)
  abdm    : the same resources claiming ABDM (ndhm.in 6.5.0) profiles in meta.profile
            (validated against the ABDM IG with the official HL7 validator)
Neither variant implies ABDM sandbox integration or certification.

Values are never invented. Where an ABDM profile REQUIRES an element the printed report does not
contain (DiagnosticReport.conclusion), an explicit, clearly-labelled placeholder is used and listed
in KNOWN_LIMITATIONS.md.
"""
from __future__ import annotations

import base64
import json
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict

from .dictionary import DICT

NS = uuid.UUID("6f1c1d2e-5b7a-4c1e-9a43-2d3f5e6a7b8c")
P = "https://nrces.in/ndhm/fhir/r4/StructureDefinition/"
SITES = {  # site configuration per binding (synthetic labs)
    "lab-a": "Sunrise Pathology Laboratory (synthetic)", "lab-b": "City Diagnostic Centre (synthetic)",
    "lab-c": "Dr. Mehta's Clinical Laboratory (synthetic)", "lab-d": "Shree Sai Diagnostics (synthetic)",
    "lab-e": "Lifeline Pathology & Imaging (synthetic)", "lab-f": "Medilink Reference Lab (synthetic)",
}
SITE_TZ = "+05:30"   # site configuration (set by the facility admin), NOT inferred from the document
NO_CONCLUSION = ("No conclusion was printed on the source report. Results were machine-transcribed by "
                 "Spoolgeist (PoC) from a legacy print job; see presentedForm for the original text.")


def _dec(d) -> str:
    return f"__DEC__{format(Decimal(str(d)), 'f')}__"


def _uid(*parts) -> str:
    return f"urn:uuid:{uuid.uuid5(NS, '|'.join(map(str, parts)))}"


def build_bundle(rec: dict, source_text: str, job_sha256: str, abdm: bool) -> str:
    bid = rec["binding_id"]
    site = SITES.get(bid, bid)
    ids = {k: _uid(job_sha256, k) for k in ("patient", "org", "dr", "comp")}
    prof = (lambda name: {"profile": [P + name]}) if abdm else (lambda name: None)

    def meta(name):
        m = prof(name)
        return {"meta": m} if m else {}

    patient = {"resourceType": "Patient", **meta("Patient"),
               "identifier": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                                     "code": "MR", "display": "Medical record number"}]},
                               "system": f"urn:spoolgeist:poc:{bid}:patient-id", "value": rec["patient_id"]}],
               "name": [{"text": rec["patient_name"]}]}
    if rec.get("patient_sex"):
        patient["gender"] = rec["patient_sex"]
    org = {"resourceType": "Organization", **meta("Organization"),
           "identifier": [{"type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                                 "code": "PRN", "display": "Provider number"}]},
                           "system": "urn:spoolgeist:poc:site-id", "value": bid}],
           "name": site}
    # printed reports carry no timezone; FHIR requires one when a time is present -> use the configured site TZ
    eff = (rec["collected_dt"] + SITE_TZ) if rec.get("collected_dt") else rec["collected"]
    obs_entries, obs_refs = [], []
    for i, x in enumerate(rec["results"]):
        spec = DICT["tests"][x["code"]]
        oid = _uid(job_sha256, "obs", i)
        obs = {"resourceType": "Observation", **meta("Observation"), "status": "final",
               "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                         "code": "laboratory", "display": "Laboratory"}]}],
               "code": {"coding": [{"system": "http://loinc.org", "code": spec["loinc"], "display": spec["display"]}],
                        "text": x["label"]},
               "subject": {"reference": ids["patient"]},
               "effectiveDateTime": eff,
               "performer": [{"reference": ids["org"]}],
               "valueQuantity": {"value": _dec(x["value_canonical"]), "unit": spec["ucum"],
                                 "system": "http://unitsofmeasure.org", "code": spec["ucum"]}}
        if x.get("ref_low") and x.get("ref_high"):
            f = Decimal(str(spec["units"][x["unit"]]))
            q = lambda v: {"value": _dec(Decimal(v) * f), "unit": spec["ucum"], "system": "http://unitsofmeasure.org", "code": spec["ucum"]}
            obs["referenceRange"] = [{"low": q(x["ref_low"]), "high": q(x["ref_high"]),
                                      "text": f"{x['ref_low']}-{x['ref_high']} {x['unit']} (as printed)"}]
        if x.get("flag"):
            code = {"H": ("H", "High"), "L": ("L", "Low"), "A": ("A", "Abnormal")}[x["flag"]]
            obs["interpretation"] = [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                                  "code": code[0], "display": code[1]}]}]
        obs_entries.append({"fullUrl": oid, "resource": obs})
        obs_refs.append({"reference": oid})
    dr = {"resourceType": "DiagnosticReport", **meta("DiagnosticReportLab"), "status": "final",
          "category": [{"coding": [{"system": "http://snomed.info/sct", "code": "15220000", "display": "Laboratory test"}]}],
          "code": {"coding": [{"system": "http://loinc.org", "code": "11502-2", "display": "Laboratory report"}],
                   "text": "Laboratory report (transcribed from legacy print job)"},
          "subject": {"reference": ids["patient"]},
          "effectiveDateTime": eff,
          "performer": [{"reference": ids["org"]}],
          "resultsInterpreter": [{"reference": ids["org"]}],
          "result": obs_refs,
          "conclusion": NO_CONCLUSION,
          "presentedForm": [{"contentType": "text/plain; charset=utf-8",
                             "data": base64.b64encode(source_text.encode()).decode(),
                             "title": f"Original printed report (print job sha256 {job_sha256[:16]}...)"}]}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    comp = {"resourceType": "Composition", **meta("DiagnosticReportRecord"), "status": "final",
            "type": {"coding": [{"system": "http://snomed.info/sct", "code": "721981007", "display": "Diagnostic studies report"}],
                     "text": "Diagnostic Report"},
            "subject": {"reference": ids["patient"]}, "date": now,
            "author": [{"reference": ids["org"]}], "title": "Diagnostic Report - Laboratory",
            "custodian": {"reference": ids["org"]},
            "section": [{"title": "Laboratory results",
                         "code": {"coding": [{"system": "http://snomed.info/sct", "code": "721981007", "display": "Diagnostic studies report"}]},
                         "entry": [{"reference": ids["dr"], "type": "DiagnosticReport"}]}]}
    bundle = {"resourceType": "Bundle", **({"meta": {"versionId": "1", "profile": [P + "DocumentBundle"]}} if abdm else {"meta": {"versionId": "1"}}),
              "identifier": {"system": "urn:spoolgeist:poc:bundle", "value": job_sha256},
              "type": "document", "timestamp": now,
              "entry": [{"fullUrl": ids["comp"], "resource": comp},
                        {"fullUrl": ids["patient"], "resource": patient},
                        {"fullUrl": ids["org"], "resource": org},
                        {"fullUrl": ids["dr"], "resource": dr}] + obs_entries}
    s = json.dumps(bundle, indent=1, ensure_ascii=False)
    return re.sub(r'"__DEC__(-?[0-9.E+]+)__"', r"\1", s)
