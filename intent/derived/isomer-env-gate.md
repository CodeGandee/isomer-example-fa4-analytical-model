# Isomer Environment Gate

## Source Intent

- `topic.intent.topic_env_requirements`: `intent/src/topic-env-gate.md`
- Research Topic: `flash-attention-4-whitebox-runtime-model`
- Runnable target: a Python 3.11+ analytical environment with NumPy, SymPy, SciPy, a Markdown renderer, and host `ncu` availability for validating the white-box runtime model.

## Gate Checklist

- [x] Python 3.11+ installed in the Topic Workspace Pixi environment.
- [x] NumPy, SymPy, SciPy, and a Markdown renderer are installed and importable.
- [x] Starter Python dependencies are installed per service policy.
- [x] Host `ncu` 2025.4.1 is reachable through recorded PATH wiring.
- [x] Topic Main Development Repository Isomer-managed namespace and agent guidance files are present.
- [x] Pixi manifest, lockfile, and environment prefix exist under the Topic Workspace.

## Runnable Target

- An operator can run `python` inside the Topic Workspace Pixi environment and import `numpy`, `sympy`, `scipy`, and `markdown`.
- An operator can run `ncu --version` through the recorded PATH wiring without relying on ambient shell state.

## Repo Requirements

- `topic.repos.main` (required): `<workspace>/repos/topic-main` exists. The Isomer-managed namespace and agent guidance files were ensured.
- Optional canonical external repos (`flash-attention`, `cutlass`) are not required by this gate and are not acquired.

## Inferred Source Warnings

- None.

## Projection Requirements

- None.

## Dependency Plan

- Python: 3.11 (source intent requires 3.11+).
- PyPI packages: `numpy`, `sympy`, `scipy`, `markdown`.
- Starter PyPI packages: `mdutils`, `ruff`, `mkdocs-material`, `mypy`, `attrs`, `omegaconf`, `imageio`, `matplotlib`, `jsonschema`, `jinja2` (`scipy` already listed above).
- External runtime wiring: `PATH` includes host `ncu` at `<NCU_PATH>`.
- Enclosure classification:
  - Pixi-managed: Python runtime and all PyPI packages.
  - Pixi-mediated external runtime wiring: host `ncu`.
- Package-specific rules: `no package-specific rule` for the listed packages.
- Resource classification: all install and verification operations are `light`.

## Resource Check Plan

- Classification source: `isomer-misc-bounded-run-tips` generic best-effort.
- All setup and verification operations are classified as `light` (Conda/PyPI installs and CLI version checks).
- No bounded real-path resource plan is required.

## Pixi Install Commands

```bash
pixi add --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml python=3.11
pixi add --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml --pypi numpy sympy scipy markdown mdutils ruff mkdocs-material mypy attrs omegaconf imageio matplotlib jsonschema jinja2
pixi install --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml --environment default
```

## Verification Commands

```bash
pixi run --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml --environment default python --version
pixi run --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml --environment default python -c "import numpy, sympy, scipy, markdown; print('imports ok')"
pixi run --manifest-path <PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml --environment default bash -lc 'export PATH=<USER_HOME>/.pixi/bin:$PATH && ncu --version'
```

## Expected Results

- Python reports a 3.11.x version.
- The import command prints `imports ok` without raising `ImportError`.
- `ncu --version` reports `Version 2025.4.1.0` (build 37053803).

## Blockers

- None at derivation time.

## Execution Log

- `pixi init` created `<PROJECT_ROOT>/isomer-content/topic-ws/flash-attention-4-whitebox-runtime-model/pixi.toml`.
- `isomer-cli project topic-main-guidance ensure --topic flash-attention-4-whitebox-runtime-model --yes` created `repos/topic-main/AGENTS.md` and `repos/topic-main/CLAUDE.md`.
- `pixi add --manifest-path pixi.toml python=3.11` succeeded.
- `pixi add --manifest-path pixi.toml --pypi numpy sympy scipy markdown mdutils ruff mkdocs-material mypy attrs omegaconf imageio matplotlib jsonschema jinja2` succeeded.
- `pixi install --manifest-path pixi.toml --environment default` succeeded.
- Verification passed:
  - `python --version` → `Python 3.11.15`
  - `python -c "import numpy, sympy, scipy, markdown"` → `imports ok: 2.4.6 1.14.0 1.17.1 3.10.2`
  - `ncu --version` via wired `PATH` → `Version 2025.4.1.0 (build 37053803)`
