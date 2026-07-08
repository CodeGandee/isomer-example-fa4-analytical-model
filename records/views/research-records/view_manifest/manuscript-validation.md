<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/paper/validation/manuscript-coverage/v1
schema_ref: isomer:deepsci/record-format/schema/paper/validation/manuscript-coverage/v1
payload_digest: sha256:fd9c003df7846d25baadbc8542a75a78e1880be52a46c59eacaa24b0ce568a0f
-->
# Manuscript Validation Report

Claim-evidence alignment check for the real-hardware FA4 B200 draft.


```json
{
  "blockers": [],
  "checks": {
    "bundle_readiness_check": "Draft, figures, references, and source CSVs are co-located in the bundle directory.",
    "citation_check": "References are carried over from the previous verified bibliography; no new unverified citations added.",
    "evidence_check": "All numerical claims trace to metrics.json rows or analysis-campaign-summary records from real B200 runs.",
    "figure_check": "Figures 1 and 2 are regenerated from refined_validation_predictions.csv and refined_query_predictions.csv; Figure 3 is the conceptual pipeline diagram.",
    "language_hygiene_check": "No operator/agent/route-control wording in manuscript prose."
  },
  "result": "pass",
  "status": "ready",
  "summary": "Claim-evidence alignment check for the real-hardware FA4 B200 draft.",
  "title": "Manuscript Validation Report"
}
```