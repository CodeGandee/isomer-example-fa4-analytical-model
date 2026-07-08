
  Research Report

 Technical assessment and implementation plan — Adding Blackwell (SM100/SM120)  
                       support to Accel‑Sim and GPGPU‑Sim                       

Executive summary                                                               

Accel‑Sim and GPGPU‑Sim do not yet ship validated, upstream Blackwell simulation
models; Accel‑Sim has active tooling but reported toolchain issues around       
sm_120, and GPGPU‑Sim continues to support modern features such as TensorCores  
and SASS traces that are necessary to add Blackwell support. Official NVIDIA    
materials and CUTLASS document new fifth‑generation tensor cores with FP4/FP6   
formats and SM100 vs SM120 functional differences; however, several             
microarchitectural details (precise SASS encodings, exact latencies, numeric    
encodings of FP4/FP6) are not public in the available evidence and require      
measurement. The following assessment synthesizes available facts, lists        
concrete simulator changes, proposes default parameters and validation          
workloads, and provides a prioritized implementation checklist and measurement  
plan to close unknowns.                                                         

Inventory & status                                                              

 • Accel‑Sim: repository available and structured for frontend/performance      
   modeling but an open issue documents CUDA toolchain interactions where sm_120
   was undefined in CUDA 12.4 and caused errors; upgrading to CUDA 12.8 changes 
   the error to an exception, indicating toolchain and disassembly tool support 
   still evolving [1], [2].                                                     
 • GPGPU‑Sim: the project remains available and supports modern GPU features    
   including TensorCores and SASS trace execution; the distribution supports    
   running NVIDIA SASS traces and is designed to integrate with Accel‑Sim-style 
   frameworks [3], [4].                                                         
 • No other open‑source simulators with proven Blackwell support appear in the  
   provided findings.                                                           

Public Blackwell microarchitectural facts (relevant for modeling)               

 • SM topology and counts: Blackwell Ultra devices reported up to 160 SMs; each 
   SM contains 128 unified CUDA cores and four 5th‑generation Tensor Cores (so  
   total tensor cores ≈ 4×SMs on Ultra) [6], [7].                               
 • Memory, caches, and TMEM: Full GB20x (some Blackwell models) have 128 MB L2  
   in NVIDIA materials; HBM3e capacities and very high bandwidth (multi‑TB/s)   
   are reported for datacenter SKUs, while consumer SM12x parts use high‑speed  
   GDDR7 with lower bandwidth; SM100 (datacenter) exposes a per‑SM Tensor Memory
   (TMEM, reported sizes vary in community notes), while SM120 (consumer)       
   appears not to expose TMEM and lacks some warp‑group features [6], [9], [14].
 • Register file and warps: CUDA Blackwell tuning guide documents 64K 32‑bit    
   registers per SM, maximum concurrent warps per SM = 64 (CC 10.0 / SM100) and 
   48 (CC 12.0 / SM120), and shared memory carveouts and sizes differing by SKU 
   [8].                                                                         
 • SM functional unit changes: Blackwell unifies INT32 with FP32 cores (doubling
   integer throughput for many ops) and introduces TMEM and new tensor‑core     
   instruction classes (tcgen05/tcgen variants and extended mma.sync) with      
   different launch/cluster semantics between SM100 and SM12x [9], [7], [13].   
 • Reported/claimed throughput: NVIDIA materials report very large aggregate    
   tensor FLOPS (petaFLOPS class) for FP4/FP6 on datacenter Blackwell; community
   sources provide per‑SM and per‑GPU peak claims but microarchitectural timing 
   per instruction is not concretely enumerated in the evidence [6], [7], [9].  

SASS ISA and tensor‑core formats (what evidence shows and what is missing)      

 • New formats: Blackwell’s 5th‑generation Tensor Cores introduce native FP4 and
   FP6 tensor formats and new collective MMA/TMA op classes; CUTLASS has added  
   support for MXF8/MXF4 and MXF8/MXF6 mixed‑precision operations and           
   Blackwell‑specific MMA instructions in its codebase, indicating upstream     
   compiler/SDK support patterns [10], [11], [12].                              
 • Instruction/encoding facts: public evidence confirms the existence of new    
   tcgen05/tcgen‑style opcodes and extended mma.sync variants for SM12x;        
   however, exact SASS opcode encodings, bit‑level formats, instruction latency 
   and throughput per opcode, and numeric bit layouts (exponent/mantissa,       
   rounding, dynamic range) for FP4/FP6 are not specified in the provided       
   findings [8], [10].                                                          
 • Practical constraints: CUTLASS and Blackwell programming docs list GEMM      
   layout, cluster/launch and tensor alignment requirements, and new kernel     
   patterns (blockscaled MMA, cluster sizes, cp.async interactions) that affect 
   how tensor ops are scheduled and how memory and TMEM are used [11], [12].    

Evidence gaps: numeric encoding/specs for FP4/FP6 (bit layout, rounding,        
subnormal behavior), SASS opcode encodings and scheduling restrictions, and     
per‑opcode micro‑latencies/throughputs are not present in the findings.         

Concrete simulator modeling requirements                                        

High‑level required changes (applicable to both Accel‑Sim and GPGPU‑Sim):       

 • Instruction decoder / ISA: add new SASS op classes for Blackwell tensor ops  
   (tcgen05 / extended mma.sync) and FP4/FP6 operand types; support PTX→SASS    
   translation traces and update disassembly handling to accept sm_100/sm_120   
   toolchain outputs (CUDA 12.8 toolchain note) [1], [16], [10].                
 • Functional‑unit models: implement 5th‑gen TensorCore functional units        
   supporting FP4/FP6 accumulation semantics and mixed precision paths; model   
   unified INT32/FP32 core behavior and doubled integer throughput where        
   applicable [9], [7].                                                         
 • Memory/cache: add TMEM model (SM100 only) and configuration switches to      
   disable TMEM for SM120; update L1/L2 sizes and cache line sizes per SKU and  
   allow HBM vs GDDR bandwidth profiles and NVLink stats for multi‑GPU cases    
   [9], [14], [20].                                                             
 • Warp/scheduler and pipeline: support increased warp tracking (up to 12 wave  
   slots per partition reported) and new cluster/collective launches and        
   barriers used by Blackwell blockscaled MMA and TMA+cp.async kernels [17],    
   [11].                                                                        
 • Frontend/binary parsing: ensure SASS traces produced by nvdisasm/cuobjdump   
   with CUDA 12.8 are parsed by the simulator frontend; GPGPU‑Sim’s support for 
   SASS traces is a key integration point [3], [1].                             
 • Calibration parameters: expose per‑unit latency/throughput knobs and default 
   profiles for SM100 (datacenter) vs SM120 (consumer) SKUs (see suggested      
   defaults below).                                                             

Where to change: the available findings describe Accel‑Sim’s                    
frontend/performance model split and GPGPU‑Sim’s SASS trace capability but do   
not provide file paths; therefore specific file paths/modules are not available 
in the evidence and must be identified by inspecting the respective repositories
before coding [5], [3].                                                         

Suggested default parameters and assumptions (best‑effort, evidence‑based):     

 • SMs per device: configurable up to 160 for Ultra; default test profiles:     
   SM100‑Large (160 SMs, HBM3e, TMEM enabled), SM120‑Consumer (e.g., 148 SMs,   
   GDDR7, TMEM disabled) [6], [9], [14].                                        
 • Register file: 64K 32‑bit registers per SM; max warps per SM: 64 (SM100) / 48
   (SM120) [8].                                                                 
 • L2 cache: model ~64–128 MB die‑level L2, cache line 128 bytes; per‑SM shared 
   memory default 128 KB, with option up to 228 KB [9], [20], [8].              
 • Tensor core behavior: model FP4/FP6 tensor ops as fused‑MAC (FMA) units that 
   accumulate to at least FP16/FP32 precision internally (evidence confirms     
   mixed‑precision designs but not exact accumulator width); allow tuning of    
   per‑op latency/throughput knobs during calibration [10], [8].                

Validation & benchmarking plan                                                  

 • Toolchain and trace preparation: use CUDA 12.8 to generate SASS/PTX and      
   CUTLASS kernels targeting sm_100 and sm_120; update cuobjdump/nvdisasm       
   parsing in the simulator frontend to accept these outputs [1], [11], [12].   
 • Microbenchmarks: implement small SASS kernels exercising (a) single tensor op
   latencies (FMA chains), (b) FP4/FP6 GEMMs (CUTLASS blockscaled kernels), (c) 
   cp.async + TMA patterns, (d) TMEM read/write and WGMMA (SM100) patterns. Use 
   CUTLASS reference kernels and profiler‑guided examples for correctness [11], 
   [12].                                                                        
 • Validation metrics and counters: map simulator counters to NVIDIA profiler   
   outputs (e.g., warp occupancy, tensor core utilization, L2 hits/misses,      
   memory BW, SM‑level occupancy) and compare execution cycles and throughput   
   for microbenchmarks; GPGPU‑Sim’s SASS trace path and Accel‑Sim’s correlation 
   tool can be used to collect comparable statistics [3], [5], [12].            
 • Progressive calibration: start with functional correctness of SASS→sim       
   mapping, then tune latency/throughput knobs to match profiler counters and   
   kernel runtimes on real hardware.                                            

Practical artifacts referenced                                                  

 • Accel‑Sim framework repo and docs (framework and frontend model) [2], [5].   
 • GPGPU‑Sim distribution (SASS trace support) [3].                             
 • NVIDIA Blackwell architecture summary and tuning guide (official) [9], [8].  
 • CUTLASS Blackwell docs and profiler support (example kernels / blockscaled   
   MMA) [11], [12].                                                             
 • Community notes and microarchitectural analyses highlighting FP4/FP6 and     
   measurement needs [7], [13], [14].                                           

Risks, unknowns, and recommended measurements                                   

 • Unknowns: SASS opcode encodings and bit patterns for new tensor ops; exact   
   numeric formats and rounding rules for FP4/FP6; per‑instruction              
   latencies/throughputs; TMEM micro‑behavior and bandwidth/latency             
   characteristics. These are not specified in the findings and will limit      
   cycle‑accurate fidelity [8], [10].                                           
 • Recommended measurements on Blackwell hardware to close gaps:                
    • Generate and disassemble short SASS kernels that perform single tensor op 
      FMAs across FP4/FP6 and capture cuobjdump/nvdisasm output to extract op   
      names/encodings (use CUDA 12.8) [1], [11].                                
    • Microbenchmark instruction latency/throughput: launch dependency chains   
      and independent parallel tensor ops to infer latency and reciprocal       
      throughput (timing at kernel level while sweeping occupancy).             
    • TMEM profiling (SM100 only): run CUTLASS TMEM‑using GEMMs and measure     
      bandwidth and latency via profiler counters; collect L1/L2/TMEM access    
      counters.                                                                 
    • Record profiler outputs (tensor core utilization, l2 hit/miss, memory     
      throughput, warp‑stalls) for mapping to simulator counters during         
      calibration [3], [12].                                                    

Prioritized implementation checklist (minimum→full fidelity)                    

 1 Minimum viable: add SM100/SM120 device profiles (SM count, registers, shared 
   mem carveouts, L2 size), update frontend to accept CUDA 12.8 SASS outputs;   
   run simple FP32 kernels for smoke tests [1], [2], [5].                       
 2 Functional tensor core: implement tensor core emulation path for fused MMA   
   semantics, map new PTX/CUTLASS kernels to the emulator, validate functional  
   correctness with CUTLASS reference kernels [11], [12].                       
 3 Memory & TMEM: add TMEM model and per‑SKU enable/disable (SM100 vs SM120);   
   add HBM/GDDR bandwidth profiles and NVLink configuration knobs [9], [14].    
 4 Scheduler & cluster features: implement cluster/collective launch semantics, 
   warp‑group MMA where applicable (SM100), and adapt scheduler/wave tracking to
   reported slot counts [17], [13].                                             
 5 Calibration and performance tuning: run microbenchmarks, collect profiler    
   counters, and iteratively tune per‑op latencies and bandwidth numbers to     
   match hardware traces [3], [7].                                              
 6 Complete SASS ISA: after collecting disassembly traces, implement accurate   
   SASS encodings and scheduling constraints; update instruction decoder for    
   full SASS parity [1], [8].                                                   

Evidence gaps (summary)                                                         

 • Exact SASS opcode encodings and bit formats for Blackwell tensor             
   instructions.                                                                
 • Numeric representation details for FP4/FP6 (bit layout, exponent/mantissa,   
   rounding).                                                                   
 • Per‑opcode latency and throughput values for tensor ops and new special      
   units.                                                                       
 • Precise TMEM bandwidth/latency microcharacteristics.                         

Addressing these requires the measurements listed above.                        

Works Cited                                                                     

[1] https://github.com/accel-sim/accel-sim-framework/issues/385                 
[2] https://github.com/accel-sim/accel-sim-framework                            
[3] https://github.com/gpgpu-sim/gpgpu-sim_distribution                         
[4] https://gpgpu-sim.org                                                       
[5] https://mkhairy.github.io/Docs/Accel-Sim.pdf                                
[6]                                                                             
https://developer.nvidia.com/blog/inside-nvidia-blackwell-ultra-the-chip-powerin
g-the-ai-factory-era                                                            
[7] https://newsletter.semianalysis.com/p/dissecting-nvidia-blackwell-tensor    
[8] https://docs.nvidia.com/cuda/archive/12.8.0/pdf/Blackwell_Tuning_Guide.pdf  
[9]                                                                             
https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwe
ll-gpu-architecture.pdf                                                         
[10] https://docs.nvidia.com/cutlass/latest/overview.html                       
[11] https://docs.nvidia.com/cutlass/latest/media/docs/cpp/blackwell.html       
[12] https://docs.nvidia.com/cutlass/4.3.4/overview.html                        
[13]                                                                            
https://github.com/ShlokVFX/Mini-Attention/blob/main/notes/sm120_vs_sm100.md    
[14] https://backend.ai/blog/2026-02-is-dgx-spark-actually-a-blackwell          
[15] https://arxiv.org/html/2507.10789v2                                        
[16]                                                                            
https://forums.developer.nvidia.com/t/cuda-toolkit-12-8-what-gpu-is-sm-120/32212
8                                                                               
[17] https://chipsandcheese.com/p/blackwell-nvidias-massive-gpu                 
[18] https://emergentmind.com/topics/blackwell-gpu-architecture                 

                                  Sources (18)                                  
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #    ┃ Title                             ┃ URL                               ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ Compatibility Issue with RTX 5090 │ https://github.com/accel-sim/acc… │
│      │ (Blackwell) Using CUDA 12.4 and   │                                   │
│      │ 12.8 · Issue #385 ·               │                                   │
│      │ accel-sim/accel-sim-framework ·   │                                   │
│      │ GitHub                            │                                   │
│ 2    │ GPGPU-Sim                         │ https://gpgpu-sim.org             │
│ 3    │ GitHub -                          │ https://github.com/gpgpu-sim/gpg… │
│      │ gpgpu-sim/gpgpu-sim_distribution: │                                   │
│      │ GPGPU-Sim provides a detailed     │                                   │
│      │ simulation model of contemporary  │                                   │
│      │ NVIDIA GPUs running CUDA and/or   │                                   │
│      │ OpenCL workloads.  It includes    │                                   │
│      │ support for features such as      │                                   │
│      │ TensorCores and CUDA Dynamic      │                                   │
│      │ Parallelism as well as a          │                                   │
│      │ performance visualization tool,   │                                   │
│      │ AerialVisoin, and an integrated   │                                   │
│      │ energy model, GPUWattch. · GitHub │                                   │
│ 4    │ This is the top-level repository  │ https://github.com/accel-sim/acc… │
│      │ for the Accel-Sim framework. -    │                                   │
│      │ GitHub                            │                                   │
│ 5    │ [PDF] Accel-Sim: An Extensible    │ https://mkhairy.github.io/Docs/A… │
│      │ Simulation Framework for          │                                   │
│      │ Validated GPU ...                 │                                   │
│ 6    │ CUDA Toolkit 12.8 what GPU is     │ https://forums.developer.nvidia.… │
│      │ 'sm_120'?                         │                                   │
│ 7    │ Dissecting Nvidia Blackwell -     │ https://newsletter.semianalysis.… │
│      │ Tensor Cores, PTX Instructions,   │                                   │
│      │ SASS ...                          │                                   │
│ 8    │ Dissecting the NVIDIA Blackwell   │ https://arxiv.org/html/2507.1078… │
│      │ Architecture with Microbenchmarks │                                   │
│ 9    │ [PDF] NVIDIA RTX BLACKWELL GPU    │ https://images.nvidia.com/aem-da… │
│      │ ARCHITECTURE                      │                                   │
│ 10   │ Overview — NVIDIA CUTLASS         │ https://docs.nvidia.com/cutlass/… │
│      │ Documentation                     │                                   │
│ 11   │ Blackwell Specific — NVIDIA       │ https://docs.nvidia.com/cutlass/… │
│      │ CUTLASS Documentation             │                                   │
│ 12   │ Overview — NVIDIA CUTLASS         │ https://docs.nvidia.com/cutlass/… │
│      │ Documentation                     │                                   │
│ 13   │ Mini-Attention/notes/sm120_vs_sm… │ https://github.com/ShlokVFX/Mini… │
│      │ at main · shlokgpu/Mini-Attention │                                   │
│      │ · GitHub                          │                                   │
│ 14   │ Inside NVIDIA DGX Spark: Is DGX   │ https://www.backend.ai/blog/2026… │
│      │ Spark Actually Blackwell?         │                                   │
│ 15   │ [PDF] Blackwell Tuning Guide -    │ https://docs.nvidia.com/cuda/arc… │
│      │ NVIDIA Documentation              │                                   │
│ 16   │ Blackwell: Nvidia's Massive GPU - │ https://chipsandcheese.com/p/bla… │
│      │ Chips and Cheese                  │                                   │
│ 17   │ Inside NVIDIA Blackwell Ultra:    │ https://developer.nvidia.com/blo… │
│      │ The Chip Powering the AI Factory  │                                   │
│      │ Era                               │                                   │
│ 18   │ Blackwell GPU Architecture        │ https://www.emergentmind.com/top… │
└──────┴───────────────────────────────────┴───────────────────────────────────┘

───────────────────────────── 18 sources | 200.20s ─────────────────────────────
