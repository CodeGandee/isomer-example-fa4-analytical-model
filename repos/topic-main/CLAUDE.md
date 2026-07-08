<!-- BEGIN isomer-labs-topic-main-guidance v1 -->
```isomer-labs-topic-main-guidance
This repository is an Isomer Topic Main Development Repository.

This repository uses Pixi as the primary package manager and execution environment. Invoke Python through Pixi, for example: `pixi run --manifest-path <manifest_path> --environment <pixi_environment> python ...`.

Avoid system Python, ambient virtualenvs, plain `python`, plain `pip`, shell activation, and local `.venv` environments as the source of truth for topic work. Query Isomer for the correct `manifest_path` and `pixi_environment` instead of hardcoding them.

Use `isomer-cli` for topic-specific facts. Start with the small self summary, then query only the slice you need before acting:
- `isomer-cli --print-json project self show`
- `isomer-cli --print-json project self identity`
- `isomer-cli --print-json project self pixi`
- `isomer-cli --print-json project self env`
- `isomer-cli --print-json project self paths <semantic-label>`
- `isomer-cli --print-json project context show`
- `isomer-cli --print-json project paths get <semantic-label>`
- `isomer-cli --print-json project paths explain <semantic-label>`
- `isomer-cli --print-json project topics list`
- `isomer-cli --print-json project topic-actors list`


Do not hardcode or guess Research Topic ids, Topic Workspace paths, Topic Actor names, Agent Names, runtime paths, credentials, external repository paths, `manifest_path`, or `pixi_environment` from this file.

Prefer semantic labels over remembered paths, especially `topic.repos.main`, `topic.repos.main.isomer_managed`, `topic.repos.main.projections.readonly`, `topic.repos.main.projections.writable`, `topic.records`, `topic.runtime`, `topic.actors.workspace`, `agent.workspace`.

Do not edit Isomer runtime databases, credentials, generated path manifests, or owner-preserved records unless the operator explicitly asks.
```
<!-- END isomer-labs-topic-main-guidance v1 -->
