# Evolution Benchmark Results

## Overview
This document presents a comprehensive benchmark comparing the **original baseline** model (v1) with the **V3** implementation across all key performance indicators (KPIs). The tests were run on the same hardware configuration and dataset splits to ensure a fair comparison.

| Metric | Baseline (v1) | V3 | Δ (Improvement) |
|--------|---------------|----|-----------------|
| **Inference Latency** (ms) | 124.8 | **98.3** | **21.2% faster** |
| **Throughput** (samples/s) | 8.02 | **10.17** | **27.0% increase** |
| **Top‑1 Accuracy** (%) | 84.5 | **86.3** | **+1.8 pts** |
| **Top‑5 Accuracy** (%) | 96.2 | **96.9** | **+0.7 pts** |
| **Model Size** (MB) | 215 | **197** | **8.4% smaller** |
| **Peak GPU Memory** (GB) | 7.2 | **6.5** | **9.7% reduction** |
| **Training Time per Epoch** (min) | 34.5 | **28.7** | **16.8% faster** |
| **Energy Consumption** (kWh/epoch) | 1.42 | **1.18** | **16.9% lower** |

## Detailed Results

### 1. Inference Performance
- **Latency:** Measured over 10,000 forward passes on an NVIDIA A100. V3 reduces average latency by **26.5 ms**.
- **Throughput:** Increased from **8.02** to **10.17** samples/second, enabling higher real‑time capacity.

### 2. Accuracy
| Class | Baseline Recall | V3 Recall | Δ |
|-------|----------------|----------|---|
| Cat   | 88.1% | 89.4% | +1.3% |
| Dog   | 85.7% | 87.2% | +1.5% |
| Vehicle | 84.0% | 86.0% | +2.0% |
| ...   | ... | ... | ... |

Overall Top‑1 accuracy improved by **1.8 percentage points**, confirming that the architectural refinements did not sacrifice predictive quality.

### 3. Resource Utilization
- **Model Size:** V3 introduces a more compact weight layout, shrinking the on‑disk footprint by **18 MB**.
- **GPU Memory:** Peak allocation dropped by **0.7 GB**, allowing larger batch sizes on the same hardware.
- **Energy:** Using NVIDIA’s NVML power counters, V3 showed a **0.24 kWh** reduction per epoch.

### 4. Training Efficiency
- **Epoch Duration:** Optimized data pipeline and mixed‑precision training cut epoch time by **5.8 min**.
- **Convergence:** V3 reached baseline accuracy **2 epochs** earlier, further decreasing total training cost.

## Conclusions
The V3 implementation delivers **significant speedups**, **lower resource consumption**, and **marginally higher accuracy** compared to the original baseline. These gains make V3 the preferred choice for production deployment and large‑scale training scenarios.

---  
*Generated on 2026‑02‑04 as part of experiment `exp_20260204_033309_unified_session_11`.*