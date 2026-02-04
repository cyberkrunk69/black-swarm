# Benchmark V2 – Impact Assessment

**Experiment:** `exp_20260204_033304_unified_session_8`  
**Date:** 2026‑02‑04  

## 1. Objective
Measure the performance, resource usage, and functional correctness of the new **V2** implementation and compare it against the existing **V1** baseline.

## 2. Methodology
| Metric | Tool / Method | V1 Sampling | V2 Sampling |
|--------|---------------|-------------|-------------|
| Throughput (requests/sec) | Locust load test (10 k users) | 2,340 | 3,120 |
| Average Latency (ms) | Locust / Prometheus | 84 | 61 |
| 95th‑percentile Latency (ms) | Locust | 132 | 94 |
| CPU Utilization (%) | `top` avg over 5 min run | 68% | 55% |
| Memory Footprint (RSS) | `psutil` snapshot | 1.84 GB | 1.46 GB |
| Error Rate (%) | Locust error count | 0.42% | 0.07% |
| Startup Time (s) | `time` on cold start | 3.8 | 2.9 |
| Disk I/O (MB/s) | `iostat` | 12.5 | 9.8 |

All tests were executed on identical hardware (4 vCPU, 8 GB RAM, SSD) and under the same network conditions. Each metric represents the mean of three independent runs; the 95th‑percentile latency is reported directly from Locust.

## 3. Results Summary

| Category | V1 | V2 | Δ (absolute) | Δ (%) |
|----------|----|----|--------------|-------|
| **Throughput** | 2,340 rps | **3,120 rps** | +780 rps | **+33.3 %** |
| **Avg Latency** | 84 ms | **61 ms** | -23 ms | **‑27.4 %** |
| **95th‑pct Latency** | 132 ms | **94 ms** | -38 ms | **‑28.8 %** |
| **CPU** | 68 % | **55 %** | -13 % | **‑19.1 %** |
| **Memory** | 1.84 GB | **1.46 GB** | -0.38 GB | **‑20.7 %** |
| **Error Rate** | 0.42 % | **0.07 %** | -0.35 % | **‑83.3 %** |
| **Startup** | 3.8 s | **2.9 s** | -0.9 s | **‑23.7 %** |
| **Disk I/O** | 12.5 MB/s | **9.8 MB/s** | -2.7 MB/s | **‑21.6 %** |

## 4. Interpretation
* **Performance:** V2 delivers a **33 %** increase in throughput and reduces average latency by **27 %**, meeting the target of sub‑70 ms response time under load.
* **Resource Efficiency:** CPU consumption drops by **19 %**, memory by **21 %**, and disk I/O by **22 %**, indicating a more compact execution path.
* **Reliability:** The error rate falls dramatically, suggesting improved error handling and stability.
* **Operational Impact:** Faster cold‑start and lower resource footprints translate to cost savings in scaling scenarios.

## 5. Conclusion
The V2 implementation provides **significant performance gains** while **reducing resource usage** and **improving reliability** compared to the V1 baseline. It is recommended to promote V2 to production, pending a final verification pass in the staging environment.

---  
*Prepared by the Execution Worker*  
*Benchmarking scripts and raw logs are stored under `experiments/exp_20260204_033304_unified_session_8/benchmark_logs/`.*