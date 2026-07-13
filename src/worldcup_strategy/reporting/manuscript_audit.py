"""Independent consistency and language audit for the pressing manuscript."""

import csv
import json
import re
from pathlib import Path

PAPER = Path("paper/pressing_score_state")
REPORTS = Path("outputs/reports")
PROHIBITED = (
    "caused by",
    "causal effect",
    "impact of score state",
    "score state made teams press",
    "trailing led teams to regain possession",
    "first study ever",
    "no prior research has",
)


def audit() -> dict[str, object]:
    """Audit claim linkage, causal language, placeholders, and limitations."""
    tex_files = [PAPER / "main.tex", *sorted((PAPER / "sections").glob("*.tex"))]
    manuscript = "\n".join(path.read_text() for path in tex_files)
    with (PAPER / "RESULTS_SOURCE_MAP.csv").open() as handle:
        claims = list(csv.DictReader(handle))
    missing_sources = [
        row["claim_id"]
        for row in claims
        if row["claim_type"] not in {"background", "interpretation"}
        and not row["supporting_data_file"].strip()
    ]
    missing_files = [
        row["claim_id"]
        for row in claims
        if row["supporting_data_file"].strip()
        and not Path(row["supporting_data_file"].strip()).exists()
    ]
    causal = [phrase for phrase in PROHIBITED if phrase in manuscript.lower()]
    placeholder_keys = sorted(set(re.findall(r"VERIFY_[A-Z0-9_]+", manuscript)))
    required_limitations = (
        "observational",
        "endogenous",
        "one international tournament",
        "provider-defined",
        "two-second",
        "five-second",
        "event-derived",
        "incomplete",
        "continuous tracking",
        "team fixed effects",
        "64 matches",
        "rank deficiency",
        "not uniformly recomputed",
        "generalize",
    )
    missing_limitations = [term for term in required_limitations if term not in manuscript.lower()]
    both_contrasts = all(
        phrase in manuscript
        for phrase in (
            "Trailing versus drawing",
            "Leading versus drawing",
            "IntensityTrailingEffect",
            "IntensityLeadingEffect",
            "EfficiencyTrailingEffect",
            "EfficiencyLeadingEffect",
        )
    )
    claim_report = {
        "total_claims": len(claims),
        "claims_linked_to_generated_evidence": len(claims)
        - len(missing_sources)
        - len(missing_files),
        "unsupported_empirical_claim_ids": sorted(set(missing_sources + missing_files)),
        "both_primary_contrasts_reported": both_contrasts,
        "citation_placeholders": placeholder_keys,
        "citation_placeholder_count": len(placeholder_keys),
        "missing_required_limitations": missing_limitations,
        "valid": not missing_sources
        and not missing_files
        and both_contrasts
        and not missing_limitations,
    }
    language_report = {
        "prohibited_phrases": causal,
        "finding_count": len(causal),
        "valid": not causal,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "pressing_manuscript_claim_audit.json").write_text(
        json.dumps(claim_report, indent=2) + "\n"
    )
    (REPORTS / "pressing_manuscript_causal_language_audit.json").write_text(
        json.dumps(language_report, indent=2) + "\n"
    )
    return {"claim_audit": claim_report, "causal_language_audit": language_report}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
