<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/decision/review-route-decision/v1
schema_ref: isomer:deepsci/record-format/schema/decision/review-route-decision/v1
payload_digest: sha256:c6179f7e5115c043ded3916cbe7a1fb39bc1dd03f5690bd7bc44a147ca59d8ae
-->
# Review Route Decision

Route the reviewed real-hardware FA4 B200 manuscript to finalize.


```json
{
  "decision": "finalize",
  "evidence_refs": [
    "artifact-ANALYSIS_CAMPAIGN_SUMMARY-320d852cdf6e",
    "artifact-ANALYSIS_CAMPAIGN_SUMMARY-e8fa897761c1"
  ],
  "next_skill": "isomer-deepsci-finalize",
  "reasoning": "Draft passes claim-evidence alignment; only minor textual checks remain. No new experiments required.",
  "status": "ready",
  "summary": "Route the reviewed real-hardware FA4 B200 manuscript to finalize.",
  "title": "Review Route Decision"
}
```