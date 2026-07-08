<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/pipeline-terminal-report/v1
schema_ref: isomer:deepsci/record-format/schema/report/pipeline-terminal-report/v1
payload_digest: sha256:0e4bdca4d04bfe6288340a36ef524a0a02eeae3fc2c3a58b927b68d957350c2a
-->
# Pipeline Terminal Report — submission-pass

Generated from a structured JSON payload.


```json
{
  "body": "{\n  \"pipeline_id\": \"submission-pass\",\n  \"status\": \"complete\",\n  \"stages_run\": [\n    {\n      \"stage_id\": \"audit\",\n      \"skill\": \"isomer-deepsci-review\",\n      \"status\": \"complete\",\n      \"artifacts_in\": [\n        \"artifact-PAPER_BUNDLE_CHECKPOINT-3ea4159c97ba\"\n      ],\n      \"artifacts_out\": [\n        \"artifact-REVIEW_REPORT-d7b43af5dbff\",\n        \"decision_record-REVIEW_ROUTE_DECISION-91f4063a629b\"\n      ],\n      \"route_decision\": \"finalize\",\n      \"notes\": \"Existing review report confirms route decision finalize; no new experiments required.\"\n    },\n    {\n      \"stage_id\": \"data_statement\",\n      \"skill\": \"isomer-deepsci-nature-data\",\n      \"status\": \"complete\",\n      \"artifacts_in\": [\n        \"artifact-PAPER_BUNDLE_CHECKPOINT-3ea4159c97ba\"\n      ],\n      \"artifacts_out\": [\n        \"artifact-DATA_AVAILABILITY_STATEMENT-9649d66c\"\n      ],\n      \"route_decision\": null,\n      \"notes\": \"General data-availability statement produced because venue is unspecified; no blocker.\"\n    },\n    {\n      \"stage_id\": \"close\",\n      \"skill\": \"isomer-deepsci-finalize\",\n      \"status\": \"complete\",\n      \"artifacts_in\": [\n        \"artifact-REVIEW_REPORT-d7b43af5dbff\",\n        \"artifact-DATA_AVAILABILITY_STATEMENT-9649d66c\",\n        \"artifact-PAPER_BUNDLE_CHECKPOINT-3ea4159c97ba\"\n      ],\n      \"artifacts_out\": [\n        \"artifact-CLAIM_LEDGER-17563d6f\",\n        \"artifact-FINAL_LIMITATIONS_REPORT-dc8749c0\",\n        \"artifact-FINAL_SUMMARY-fc75b922\",\n        \"artifact-RESUME_PACKET-e14f7a3d\",\n        \"decision_record-CLOSURE_DECISION-4b441b63\"\n      ],\n      \"route_decision\": \"park\",\n      \"notes\": \"Closure decision is park pending public repository deposit and venue confirmation.\"\n    }\n  ],\n  \"final_artifact\": \"artifact-FINAL_SUMMARY-fc75b922\",\n  \"recommended_next\": \"park\",\n  \"blocker\": null,\n  \"resume_point\": null\n}",
  "title": "Pipeline Terminal Report \u2014 submission-pass"
}
```