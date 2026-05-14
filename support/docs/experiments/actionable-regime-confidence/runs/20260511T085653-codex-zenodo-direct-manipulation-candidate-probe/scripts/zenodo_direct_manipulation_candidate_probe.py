#!/usr/bin/env python3
import json
from pathlib import Path


RUN_ID = "20260511T085653+0800-codex-zenodo-direct-manipulation-candidate-probe"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "zenodo-probe"
CHECKS = ROOT / "checks"

# Bounded Zenodo metadata readback from the unauthenticated probe candidates.
# These are compact metadata facts only; raw files are not downloaded.
RECORDS = [
    {
        "record_id": "5026154",
        "url": "https://zenodo.org/records/5026154",
        "title": "Data from: Market forces influence helping behaviour in cooperatively breeding paper wasps",
        "file_hints": ["Market Manipulation video data.xlsx", "Market Manipulation main data.xlsx", "Market Manipulation relatedness data.xlsx"],
        "decision": "rejected_non_financial_biological_market",
    },
    {
        "record_id": "4580200",
        "url": "https://zenodo.org/records/4580200",
        "title": "VERA Spoofing PalmVein",
        "file_hints": [],
        "decision": "rejected_non_financial_biometric_spoofing",
    },
    {
        "record_id": "16955639",
        "url": "https://zenodo.org/records/16955639",
        "title": "HuBERT Ensemble Models for Singing Voice Deepfake Detection",
        "file_hints": ["HuBERT_Ensemble_Models_for_Singing_Voice_Deepfake_Detection.pdf"],
        "decision": "rejected_non_financial_voice_deepfake",
    },
    {
        "record_id": "19653452",
        "url": "https://zenodo.org/records/19653452",
        "title": "Chapter 8: Market Manipulation, Insider Trading, and Regulatory Effectiveness: A Comparative Study of South Africa, the USA, and the UK",
        "file_hints": ["Chapter 8 Market Manipulation, Insider Trading and Regulatory Effectiveness A Comparative Study of South Africa the USA and the UK.docx"],
        "decision": "rejected_policy_chapter_no_rows",
    },
    {
        "record_id": "8202936",
        "url": "https://zenodo.org/records/8202936",
        "title": "MARitime SIMulated (MARSIM) Dataset for GPS Spoofing Detection",
        "file_hints": ["README.md", "dataset.tar.bz2", "parameter_space.png"],
        "decision": "rejected_non_financial_gps_spoofing",
    },
    {
        "record_id": "17226688",
        "url": "https://zenodo.org/records/17226688",
        "title": "Data Collection & Requirements",
        "file_hints": ["data_collection_v6.xlsx"],
        "decision": "rejected_dataset_catalog_not_market_rows",
    },
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    result = {
        "run_id": RUN_ID,
        "objective": "Verify Zenodo sidecar manipulation candidates from unauthenticated source probe.",
        "records_inspected": len(RECORDS),
        "accepted_direct_manipulation_sources": 0,
        "accepted_label_rows_materialized": 0,
        "records": RECORDS,
        "gate_result": "blocked_zenodo_candidates_false_positive_or_no_rows",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": "Do not spend more cycles on these six Zenodo records; obtain a true financial market manipulation dataset with timestamped positive/negative rows or authenticated Dune export.",
    }
    (OUT / "zenodo_direct_manipulation_candidate_probe.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Zenodo Direct Manipulation Candidate Probe",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Result",
        "",
        "- Zenodo records inspected: `6`.",
        "- Accepted direct `Manipulation` sources: `0`.",
        "- Accepted label rows materialized: `0`.",
        f"- Gate result: `{result['gate_result']}`.",
        "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        "",
        "## Records",
        "",
        "| Record | Title | Decision | File hints |",
        "|---|---|---|---|",
    ]
    for r in RECORDS:
        files = ", ".join(r["file_hints"])
        lines.append(f"| [`{r['record_id']}`]({r['url']}) | {r['title']} | `{r['decision']}` | {files} |")
    lines.extend(["", "## Next Action", "", result["next_action"], ""])
    (OUT / "zenodo_direct_manipulation_candidate_probe.md").write_text("\n".join(lines), encoding="utf-8")

    assertions = [
        "records_inspected=6",
        "accepted_direct_manipulation_sources=0",
        "accepted_label_rows_materialized=0",
        f"gate_result={result['gate_result']}",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
    ]
    (CHECKS / "zenodo_direct_manipulation_candidate_probe_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
