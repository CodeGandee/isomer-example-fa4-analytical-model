# Topic Reset Checkpoint

Research Topic: `flash-attention-4-whitebox-runtime-model`
Topic Workspace: `flash-attention-4-whitebox-runtime-model`
Checkpoint: `topic-reset-checkpoint-flash-attention-4-whitebox-runtime-model-20aa73bf28b0`
Status: `ready`
Created: `2026-07-04T10:46:58Z`

Post-initialization/pre-research Topic Workspace reset checkpoint.

## Preserved State

- Lifecycle records: 5
- Structured payloads: 1
- Generated views: 0
- Artifact format registrations: 0
- Readiness records: 0

## Readiness Evidence

- Topic Workspace summary: `<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/isomer-topic-workspace-summary.md`
- Latest readiness: none recorded


## Reset Boundary

No Git operations are permitted by this checkpoint. Later preparation must update this checkpoint to survive reset.

```json
{
  "actor_ref": "operator",
  "blockers": [],
  "checkpoint_id": "topic-reset-checkpoint-flash-attention-4-whitebox-runtime-model-20aa73bf28b0",
  "created_at": "2026-07-04T10:46:58Z",
  "extensions": [],
  "no_git_operations": true,
  "preserved_artifact_format_registration_ids": [],
  "preserved_generated_view_paths": [],
  "preserved_readiness_record_ids": [],
  "preserved_record_ids": [
    "research-topic:flash-attention-4-whitebox-runtime-model",
    "topic-actor-operator-materialize-2026-07-04T10-45-23Z",
    "topic-actor-operator-register-2026-07-04T10-45-23Z",
    "topic-reset-checkpoint-flash-attention-4-whitebox-runtime-model-20aa73bf28b0",
    "topic-workspace:flash-attention-4-whitebox-runtime-model"
  ],
  "preserved_semantic_labels": [
    "topic.actors_root",
    "topic.agents_root",
    "topic.records",
    "topic.records.artifacts",
    "topic.records.logs",
    "topic.records.runs",
    "topic.records.tasks",
    "topic.records.views",
    "topic.repos.main",
    "topic.repos.main.isomer_managed",
    "topic.repos.main.projections.manifest",
    "topic.repos.main.projections.readonly",
    "topic.repos.main.projections.writable",
    "topic.repos.main.tmp",
    "topic.repos.main.tracked",
    "topic.repos.main.tracked.artifacts",
    "topic.repos.main.tracked.boundaries",
    "topic.repos.main.tracked.manifests",
    "topic.repos.main.tracked.runs",
    "topic.repos.main.tracked.shared",
    "topic.repos.main.tracked.tasks",
    "topic.repos.main.tracked.tools",
    "topic.repos.main.tracked.views",
    "topic.runtime",
    "topic.runtime.db",
    "topic.tmp",
    "topic.workspace",
    "topic.workspace.summary"
  ],
  "preserved_structured_payload_ids": [
    "topic-reset-checkpoint-flash-attention-4-whitebox-runtime-model-20aa73bf28b0"
  ],
  "research_topic_id": "flash-attention-4-whitebox-runtime-model",
  "runtime_high_watermarks": {
    "artifact_format_registrations": null,
    "lifecycle_records": "2026-07-04T10:45:23Z",
    "readiness_records": null,
    "structured_research_payloads": null
  },
  "semantic_path_inventory": [
    {
      "exists": true,
      "path": "<PROJECT_ROOT>",
      "source": "current directory",
      "surface": "project_root"
    },
    {
      "exists": true,
      "path": "<PROJECT_ROOT>/.isomer-labs",
      "source": "current directory",
      "surface": "project_config_directory"
    },
    {
      "exists": true,
      "path": "<PROJECT_ROOT>/.isomer-labs/manifest.toml",
      "source": "current directory",
      "surface": "project_manifest"
    },
    {
      "exists": true,
      "path": "<PROJECT_ROOT>/isomer-content",
      "source": "manifest",
      "surface": "isomer_content_root"
    },
    {
      "exists": true,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws",
      "source": "manifest",
      "surface": "topic_workspace_base"
    },
    {
      "compatibility_surface": "topic_workspace",
      "exists": true,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.workspace",
      "source": "Project Manifest",
      "surface": "topic_workspace"
    },
    {
      "exists": true,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos",
      "source": "default_profile",
      "surface": "repos"
    },
    {
      "compatibility_surface": "workspace_runtime_db",
      "durability": "durable",
      "exists": true,
      "owner": "runtime",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/state.sqlite",
      "path_kind": "file",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.runtime.db",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_runtime_file",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_runtime_file",
        "kind": "file",
        "lifecycle": "durable",
        "owner": "runtime",
        "path_kind": "file",
        "safety_policy": "topic_workspace_local",
        "visibility": "private"
      },
      "surface": "workspace_runtime_db"
    },
    {
      "compatibility_surface": "topic_tmp",
      "durability": "disposable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/tmp",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.tmp",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_disposable_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_disposable_dir",
        "kind": "directory",
        "lifecycle": "disposable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "private"
      },
      "surface": "topic_tmp"
    },
    {
      "compatibility_surface": "topic_main_repo",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo",
      "storage_profile_traits": {
        "context": "topic",
        "git_semantics": "repository",
        "id": "topic_repo",
        "kind": "repository",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "topic_main_repo"
    },
    {
      "compatibility_surface": "topic_main_tmp",
      "durability": "disposable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/tmp",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tmp",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_disposable_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_disposable_dir",
        "kind": "directory",
        "lifecycle": "disposable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "private"
      },
      "surface": "topic_main_tmp"
    },
    {
      "compatibility_surface": "topic_main_isomer_managed",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.isomer_managed",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_durable_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_durable_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "topic_main_isomer_managed"
    },
    {
      "compatibility_surface": "topic_main_tracked",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked"
    },
    {
      "compatibility_surface": "topic_main_tracked_shared",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/shared",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.shared",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_shared"
    },
    {
      "compatibility_surface": "topic_main_tracked_artifacts",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/artifacts",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.artifacts",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_artifacts"
    },
    {
      "compatibility_surface": "topic_main_tracked_tasks",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/tasks",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.tasks",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_tasks"
    },
    {
      "compatibility_surface": "topic_main_tracked_runs",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/runs",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.runs",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_runs"
    },
    {
      "compatibility_surface": "topic_main_tracked_views",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/views",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.views",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_views"
    },
    {
      "compatibility_surface": "topic_main_tracked_tools",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/tools",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.tools",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_tools"
    },
    {
      "compatibility_surface": "topic_main_tracked_boundaries",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/boundaries",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.boundaries",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_boundaries"
    },
    {
      "compatibility_surface": "topic_main_tracked_manifests",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/manifests",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.tracked.manifests",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_tracked_manifests"
    },
    {
      "compatibility_surface": "topic_main_projections_readonly",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/topic-owned/readonly/extern",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.projections.readonly",
      "sharing": "topic_read",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_readonly_projection_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_readonly_projection_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "topic_read"
      },
      "surface": "topic_main_projections_readonly"
    },
    {
      "compatibility_surface": "topic_main_projections_writable",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/topic-owned/writable/extern",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.projections.writable",
      "sharing": "topic_write",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_writable_projection_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_writable_projection_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_repo_local",
        "visibility": "topic_write"
      },
      "surface": "topic_main_projections_writable"
    },
    {
      "compatibility_surface": "topic_main_projections_manifest",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/repos/topic-main/isomer-managed/tracked/manifests/extern-projections.toml",
      "path_kind": "file",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.repos.main.projections.manifest",
      "sharing": "shared",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_repo_tracked_file",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_repo_tracked_file",
        "kind": "file",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "file",
        "safety_policy": "topic_repo_local",
        "visibility": "shared"
      },
      "surface": "topic_main_projections_manifest"
    },
    {
      "compatibility_surface": "agents",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/agents",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.agents_root",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_private_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_private_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "private"
      },
      "surface": "agents"
    },
    {
      "compatibility_surface": "actors",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/actors",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.actors_root",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_private_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_private_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "private"
      },
      "surface": "actors"
    },
    {
      "compatibility_surface": "records",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records"
    },
    {
      "compatibility_surface": "records_artifacts",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records.artifacts",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records_artifacts"
    },
    {
      "compatibility_surface": "records_tasks",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/tasks",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records.tasks",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records_tasks"
    },
    {
      "compatibility_surface": "records_runs",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/runs",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records.runs",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records_runs"
    },
    {
      "compatibility_surface": "records_views",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/views",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records.views",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records_views"
    },
    {
      "compatibility_surface": "records_logs",
      "durability": "durable",
      "exists": true,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/logs",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.records.logs",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_records_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_records_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      },
      "surface": "records_logs"
    },
    {
      "compatibility_surface": "runtime",
      "durability": "durable",
      "exists": true,
      "owner": "runtime",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/runtime",
      "path_kind": "directory",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.runtime",
      "sharing": "private",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_runtime_dir",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_runtime_dir",
        "kind": "directory",
        "lifecycle": "durable",
        "owner": "runtime",
        "path_kind": "directory",
        "safety_policy": "topic_workspace_local",
        "visibility": "private"
      },
      "surface": "runtime"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/intake",
      "source": "default_profile",
      "surface": "artifact_intake"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/baselines",
      "source": "default_profile",
      "surface": "artifact_baselines"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/experiments",
      "source": "default_profile",
      "surface": "artifact_experiments"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/analysis",
      "source": "default_profile",
      "surface": "artifact_analysis"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/figures",
      "source": "default_profile",
      "surface": "artifact_figures"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/paper",
      "source": "default_profile",
      "surface": "artifact_paper"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/decisions",
      "source": "default_profile",
      "surface": "artifact_decisions"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/evidence",
      "source": "default_profile",
      "surface": "artifact_evidence"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/findings",
      "source": "default_profile",
      "surface": "artifact_findings"
    },
    {
      "exists": false,
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/records/artifacts/handoffs",
      "source": "default_profile",
      "surface": "artifact_handoffs"
    },
    {
      "compatibility_surface": "topic_workspace_summary",
      "durability": "durable",
      "exists": false,
      "owner": "topic",
      "path": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/isomer-topic-workspace-summary.md",
      "path_kind": "file",
      "scope": "topic",
      "scope_ref": "topic_workspace:flash-attention-4-whitebox-runtime-model",
      "semantic_label": "topic.workspace.summary",
      "sharing": "topic",
      "source": "default_profile",
      "source_detail": "isomer-default.v1",
      "storage_profile": "topic_workspace_summary_file",
      "storage_profile_traits": {
        "context": "topic",
        "id": "topic_workspace_summary_file",
        "kind": "file",
        "lifecycle": "durable",
        "owner": "topic",
        "path_kind": "file",
        "safety_policy": "topic_workspace_local",
        "visibility": "topic"
      }
    }
  ],
  "source_readiness_evidence": null,
  "status": "ready",
  "summary": "Post-initialization/pre-research Topic Workspace reset checkpoint.",
  "summary_paths": [
    "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/isomer-topic-workspace-summary.md"
  ],
  "title": "Topic Reset Checkpoint",
  "topic_workspace_id": "flash-attention-4-whitebox-runtime-model",
  "topic_workspace_summary_ref": "<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/isomer-topic-workspace-summary.md",
  "workspace_runtime_schema_version": "isomer-workspace-runtime.v1"
}
```