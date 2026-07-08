# Confusion Analysis

This note summarizes what the `flash-attention-4-whitebox-runtime-model` chatlog analysis shows about patterns that misled the agent and required explicit user correction. The main source is `merged-timeline.md` in this directory.

## Summary

The recurring pattern is that the agent often accepts a nearby proxy for success: emulator accuracy instead of real B200 validation, coarse NCU bottleneck labels instead of component/path proof, build success instead of rendered-paper inspection, and a failed run instead of experiment evidence. The sections below organize those corrections by the three work surfaces the user kept sharpening: analytical-model definition, experimentation, and paper writing.

```text
proxy success -> agent declares progress -> user tightens reality check
     |                    |                           |
     |                    v                           v
emulator MAPE       "fixed" PDF              real B200 / page image /
coarse NCU label    generated artifact       exact hardware component
```

## Correction Map

| Misleading cue | Agent tendency | User correction |
| --- | --- | --- |
| Emulator has ground truth | Report accuracy-like confidence | Require real B200 validation for accuracy claims |
| NCU says compute-bound | Treat bottleneck as explained | Ask for exact saturated component and blocking path |
| Build command finishes | Assume PDF or figure is fixed | Inspect rendered page and preserve semantics |
| Run fails or is slow | Treat experiment as infeasible | Diagnose the measurement path before rejecting the experiment |
| Simulator repo exists | Focus on running simulator | Use simulator as architecture/modeling reference |
| Formula works in code | Use code identifiers in paper math | Use concise symbols and define notation near use |

## User Prompts That Built the Analytical Model

The chatlog also shows a separate, constructive thread: the user repeatedly refined what the analytical model was supposed to be. This matters because many corrections were not isolated fixes; they were attempts to pull the agent toward a sharper model contract.

### Core Model Contract

The initial topic prompt in Event 002 defines the core model: a white-box Flash Attention 4 runtime model that predicts milliseconds from input, follows the GPU internal execution model, avoids complex black-box fitting, identifies bottlenecks, and bases analysis on hardware rather than per-input kernel execution.

Events 004, 006, and 007 make that contract concrete. The user adds NCU because the model must reach SM/cache level, sets NVIDIA B200 as the target GPU, and requires B200 architecture, execution flow, hardware specifics, closed-form formulas for each model part, probabilistic handling for random effects such as cache misses, and prior literature/source study on GPU runtime modeling.

Event 012 then clarifies the validation target: the model should compare measured versus predicted results, and some stages should predict NCU counter trends, not only end-to-end runtime.

### Real-Hardware Validation Contract

Events 026 through 029 define the evidence bar. The user asks for theoretical model output versus actual runs, challenges emulator-only error with “without actually run something on b200, how do you know the error,” tightens the topic requirement to theoretical-vs-actual data, and asks the agent to investigate why a kernel run was treated as too slow.

This thread recurs later in Events 031, 033, 048, 052, 093, 094, and 096. The user asks to verify NCU availability, continue experiments, push inputs to saturate hardware resources, account for busy-GPU measurement noise, design reviewer-facing saturation experiments, collect hard evidence, and run multiple focused passes where mismatches drive model refinement.

### Hardware-Flow and Mini-Simulator Direction

Events 038, 040, and 042 shift the model from a formula bundle toward an explainable execution model. The user says the paper does not explain how latency is computed from input, asks the agent to study AccelSim internals, and then states the target more precisely: the analytical model should be mini-simulator-like and cycle-level, but still mathematical rather than a full simulator.

The key user requirement in Event 042 is data movement sequencing: do not treat data movement as a coarse bandwidth term. Model how data is sliced into parts, how each part moves from one hardware component to another, and how that sequence contributes to latency.

Events 056, 057, 061, 065, 066, 067, and 068 extend this direction. The user asks to clone AccelSim, check Hopper/Blackwell coverage, clarify that AccelSim should be used as an architectural reference rather than actually run, search for Blackwell simulation materials, download papers, update the analytical model to map to hardware execution flow, and run three rounds of increasingly detailed execution-flow modeling.

### Bottleneck, Saturated Component, and Blocking Path

Events 075, 077, and 078 ask how the paper proves the model works, compare the three candidate models, and ask which model best identifies bottlenecks from input.

Event 079 is the strongest correction: compute-bound versus memory-bound is too coarse. The user requires the exact saturated hardware component and the execution path that blocks progress. Event 080 then revises the research intent so the analytical model predicts not only runtime but also saturated component and blocking path.

Events 081, 103, and 105 shape the paper around this scientific claim. The most relevant model becomes the proposed method, alternatives move to the appendix, detailed appendix evidence must include triggering inputs, predicted per-stage runtime, NCU measurement method, collected metrics, metric values, and why the measurements match the analytical prediction, and the proof is important enough to promote into the main experiment section.

### Mathematical and Operational Presentation

Event 043 asks for a GPU hardware component execution-system diagram, which is part of making the model inspectable rather than only code-backed.

Event 088 asks the agent to replace code-like formula names with concise mathematical symbols and define notation near usage. This is more than style: it makes the analytical model readable as math rather than as program output.

### Condensed Model Contract

Taken together, these prompts define the expected model as:

1. A B200-targeted white-box analytical model for Flash Attention 4 forward runtime.
2. A hardware-execution-flow model with closed-form or bounded probabilistic terms.
3. A mini-simulator-style decomposition that tracks component stages, data movement, and sequencing without becoming a full event-driven simulator.
4. A predictor of runtime, saturated hardware component, and blocking execution path.
5. A model validated against real B200 timings and NCU counter evidence, not emulator-only ground truth.
6. A publishable mathematical description with clear symbols, local notation definitions, rendered diagrams, and detailed evidence tables.

## User Prompts That Shaped Experimentation

The experimentation thread is related to the model thread but deserves its own section. The user repeatedly pushed the agent from plausible validation toward real, controlled, hardware-grounded evidence.

### Real Hardware Over Proxy Ground Truth

Events 026 through 028 form the strongest correction. The user asks for theoretical model output versus actual runs, challenges the agent with “without actually run something on b200, how do you know the error,” and then tightens the topic requirement so the work must include theoretical-vs-actual run data.

The correction is that emulator-generated ground truth may test internal consistency, but it does not establish real B200 prediction error. Any accuracy claim must name its evidence class and cannot imply real-hardware validation without measured B200 timings.

### Diagnose Failed Runs Before Declaring Infeasibility

In Event 029, the user points out that an attention kernel should not take something like 25 minutes and asks the agent to find what blocks the run. The important correction is that a failed setup path was being mistaken for evidence that the real-hardware experiment was infeasible.

The correction is that failed or slow experiments should trigger measurement-path diagnosis before the agent concludes that a real-hardware experiment is infeasible. A failed first run is not evidence that the experiment cannot be done.

### NCU as Concrete Counter Evidence

Events 004, 012, and 031 define NCU as an experimental requirement. The user first adds NCU because the model reaches SM/cache level, then clarifies that some stages should predict NCU counter trends, and later asks the agent to verify that NCU is usable.

The correction is that NCU should not be treated as a vague profiler label. It must provide concrete metric names, counter values, counter-to-component mapping, and a stated relationship to each model claim.

### Targeted Saturation Experiments

Events 048, 093, 094, and 096 define the desired experiment shape. The user asks to push inputs to the GPU limit, saturate compute/storage/memory/bandwidth resources, prove that the model can predict bottlenecks, design reviewer-facing experiments that saturate each part of the critical path, collect hard evidence, and run multiple rounds where each round focuses on one node.

The correction is that experiments should be adversarial and diagnostic, not passive validation over arbitrary inputs. Each round should choose shapes intended to stress a target component or path, predict the saturated node before measurement, collect matching NCU evidence, and explain mismatches.

### Auditable Experiment Reporting

Events 103, 105, and 106 define how the evidence must be reported. The user asks for appendix detail about which inputs trigger saturation, how the model predicts each stage runtime, how NCU is measured, what metrics are collected, the metric values, and why the measurement matches the analytical prediction. The user then asks to promote the proof into the main experiment section and later corrects the NCU activity figure layout.

The correction is that experimental evidence must be auditable. It should not be buried, summarized vaguely, or shown in unreadable figures. Core proof belongs in the main experiment narrative, with detailed tables and readable visualizations.

### Condensed Experiment Contract

Taken together, these prompts define the expected experiment discipline as:

1. Run real Flash Attention 4 on B200 when making real accuracy claims.
2. Collect both runtime and NCU counter evidence.
3. Use targeted input shapes to saturate each critical-path node.
4. Compare predicted runtime, saturated component, and blocking path against measured evidence.
5. Keep calibration, validation, and query sets honest.
6. Diagnose failed measurement paths before declaring a run infeasible.
7. Treat mismatches as model-improvement signals, not failures to hide.
8. Report commands, metrics, values, mappings, and rationale clearly enough for reviewer audit.

## User Prompts That Shaped Paper Writing

The paper-writing prompts show a third thread: the user was not asking only for a generated PDF. They repeatedly corrected the agent toward a paper that communicates the analytical model, proves the central claims, uses the right venue conventions, and is inspectable as a rendered artifact.

### Drafting and Paper Workflow

Events 021 and 035 start the paper workflow: the user asks to finalize and write a paper, then later asks the pipeline to proceed to write or update the PDF paper and pick a workflow. Event 036 corrects the build tool choice by asking to use Tectonic instead.

Events 044 and 069 ask whether the PDF or paper PDF was actually updated. The correction is that paper generation must produce an actual updated reading artifact, not only an intermediate draft claim.

### Rendered-PDF Inspection and Formatting

Events 037, 046, 047, 071, 073, 092, 104, and 106 show that successful PDF builds are not enough. The user asks the agent to read the PDF, fix clipped figures, check a specific page when the claimed fix was wrong, repair chaotic or cluttered figures, find text overlaps, fix appendix overflow, and improve the NCU activity figure layout.

The correction is that the agent must inspect the rendered PDF pages that the reader sees. Build success, regenerated SVG/PDF files, or source edits do not prove the artifact is readable.

### Paper Structure and Venue Conventions

Event 081 restructures the paper around the research goal: the model most relevant to predicting saturated component and blocking path should become the proposed method, while other models move to the appendix as alternatives.

Events 083, 087, and 091 push venue formatting. The user asks for IEEE double-column style, considers PAMI style, asks whether the PAMI LaTeX template was downloaded, and then requires the official PAMI template.

The correction is that paper structure should follow the scientific claim, and venue/template requirements should be concrete artifacts, not approximate styling.

### Explaining the Analytical Model in the Paper

Event 038 is a direct communication failure: the user says the paper does not explain how the math model computes latency from input. Event 043 asks for a GPU hardware component execution-system diagram. Event 075 asks how the paper proves the analytical model's effectiveness. Event 088 asks the agent to replace long programming-variable-like formula names with concise math symbols and define notation near usage.

The correction is that a paper cannot merely point to code or list results. It must show the computation path from input to prediction, use mathematical notation, explain symbols locally, and provide diagrams that make the hardware execution model inspectable.

### Experimental Evidence in the Paper

Events 093, 094, 103, 105, and 107 define how experimental proof belongs in the paper. The user frames a reviewer challenge, asks for hard evidence in appendix and main text, requests detailed appendix information about saturation-triggering inputs, per-stage predictions, NCU measurement method, metrics, metric values, and matching rationale, then asks to promote Appendix D into the main experiment section and explain table columns in the main text.

The correction is that central proof cannot be buried or summarized. The paper must make the evidence auditable in the main narrative, with detailed tables, readable figures, and explicit column/metric definitions.

### Condensed Paper-Writing Contract

Taken together, these prompts define the expected paper discipline as:

1. Build the paper with the requested toolchain and venue template.
2. Inspect rendered PDF pages, not only source files or build logs.
3. Explain how input becomes predicted latency, saturated component, and blocking path.
4. Use mathematical symbols and define notation near use.
5. Keep the most goal-relevant model in the main method and move alternatives to appendix.
6. Put central correctness evidence in the main experiment section.
7. Make figures and tables readable, semantically connected, and explained in text.
8. Include enough experimental detail for a reviewer to audit inputs, metrics, values, and model-evidence matching.

## Design Implications for GPU Analytical Modeling Callbacks

The user-plugin should guard against these failure modes with four strong gates.

1. Evidence class gate: emulator, simulator, synthetic, NCU, microbenchmark, and real hardware evidence must stay separate. Accuracy claims require the matching evidence class.
2. Component/path gate: compute-vs-memory labels are insufficient when the topic asks for saturated hardware component and blocking execution path.
3. Harness gate: failed or slow GPU runs require measurement-path diagnosis before the agent may conclude the experiment is infeasible.
4. Artifact inspection gate: paper, figure, and table updates require rendered-output inspection, not only source edits or successful builds.

## Practical Prompt Reminder

Before closing a GPU analytical-modeling turn, the agent should ask:

1. Is this claim based on real hardware, NCU, emulator, simulator, synthetic data, or analytical proxy?
2. Does the model predict a concrete saturated component and blocking path, or only a coarse label?
3. If a run failed or was slow, did I inspect why the measurement path failed?
4. If I changed a paper artifact, did I inspect the rendered page that the user will read?
5. If I used a simulator source, am I learning architecture/modeling structure rather than overclaiming simulator support for the target GPU?
