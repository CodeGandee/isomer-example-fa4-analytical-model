<!-- isomer-structured-research-record
format_profile_ref: isomer:deepsci/record-format/profile/report/scout-minimum-unknowns/v2
schema_ref: isomer:deepsci/record-format/schema/report/scout-minimum-unknowns/v2
payload_digest: sha256:7d88e4eba7cdf52f0bc39cf8b9b7b2886c76b35554836d40517c97e19a4dedcd
-->
# Scout Minimum Unknowns

Unresolved route-changing questions for the Flash Attention 4 white-box runtime model.


```json
{
  "metadata": {
    "consumer": "isomer-deepsci-scout, literature discovery, evaluation contract drafting, baseline shortlist drafting.",
    "placeholder": "<SCOUT_MINIMUM_UNKNOWNS>",
    "producer": "isomer-deepsci-scout",
    "skill": "isomer-deepsci-scout"
  },
  "sections": {
    "revisit_scout_if": [
      "Operator rejects proposed accuracy threshold or split.",
      "FA4 tile/occupancy details cannot be sourced or measured."
    ],
    "route_impact": "These questions affect baseline model construction and validation plan but do not block routing to isomer-deepsci-baseline.",
    "unknowns": [
      "B200 sustained HBM bandwidth and L2 transaction parameters.",
      "FA4 default tile sizes, warpgroup assignment, and 2-CTA mode per precision.",
      "TMA latency and TMEM allocation constraints per SM.",
      "Fraction of exponentials emulated and conditional-rescaling threshold tau.",
      "Primary accuracy threshold and validation split."
    ]
  },
  "status": "ready",
  "summary": "Unresolved route-changing questions for the Flash Attention 4 white-box runtime model.",
  "title": "Scout Minimum Unknowns"
}
```