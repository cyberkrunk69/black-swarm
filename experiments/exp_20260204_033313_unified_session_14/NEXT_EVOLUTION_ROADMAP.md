# NEXT_EVOLUTION_ROADMAP.md

## Objective
Allocate the next **$1** of compute (≈ $1 ≈ ≈ 0.5 CPU‑hours on typical cloud spot pricing) to experiments that deliver the highest expected impact on model performance, data quality, and system robustness.

---

## Prioritized Spend Plan

| Priority | Allocation | Compute Estimate | Expected Impact | Rationale |
|----------|------------|------------------|----------------|-----------|
| **1** | **Prompt Engineering & Few‑Shot Templates** | 0.15 CPU‑h (≈ 9 min) | Immediate boost in downstream task accuracy (≈ 2‑4 % absolute) | Low‑cost, high‑gain; iterates over prompt variations, chain‑of‑thought, and self‑consistency tricks. |
| **2** | **Data Augmentation (Synthetic QA Generation)** | 0.20 CPU‑h (≈ 12 min) | Improves coverage of rare entities & edge cases (+≈ 1 % F1) | Uses the current model to generate high‑quality synthetic examples for under‑represented topics. |
| **3** | **Curriculum Learning Mini‑Run** | 0.25 CPU‑h (≈ 15 min) | Faster convergence on fine‑tuning, reducing overall training time by ~10 % | Re‑order existing fine‑tuning data from easy → hard; requires only a short warm‑up pass. |
| **4** | **Evaluation Suite Expansion** | 0.10 CPU‑h (≈ 6 min) | More reliable ROI measurement; catches regressions early | Add 2–3 targeted benchmark sets (e.g., adversarial robustness, factuality). |
| **5** | **Hyper‑parameter Micro‑Search (Learning‑rate & Batch‑size)** | 0.15 CPU‑h (≈ 9 min) | Fine‑tune performance (+≈ 0.5 % BLEU/ROUGE) | Grid search over a tiny range using the same data split; leverages early‑stopping. |
| **6** | **Logging & Artifact Versioning** | 0.05 CPU‑h (≈ 3 min) | Improves reproducibility and future cost‑benefit analysis | Capture experiment metadata in a lightweight JSON log; negligible compute. |

**Total:** ~0.90 CPU‑hours ≈ **$1** (allowing a small buffer for overhead).

---

## Execution Steps

1. **Prompt Engineering**  
   - Run a script that iterates over 20 prompt variants.  
   - Record per‑variant validation scores.  
   - Select top‑3 for downstream tasks.

2. **Synthetic QA Generation**  
   - Sample 500 seed questions from the low‑frequency bucket.  
   - Use the current model with temperature 0.7 to generate answers.  
   - Filter with a simple heuristic (length, token overlap) and add to training set.

3. **Curriculum Learning Warm‑up**  
   - Sort existing fine‑tuning data by loss difficulty (computed from a quick forward pass).  
   - Perform a single epoch over the ordered data.

4. **Evaluation Suite Expansion**  
   - Pull two adversarial benchmark datasets from the public repo.  
   - Run inference on a held‑out subset (≈ 200 examples each).

5. **Micro‑search**  
   - Try learning‑rates {2e‑5, 3e‑5, 5e‑5} and batch sizes {16, 32}.  
   - Run 2‑epoch quick fine‑tune for each combo; keep best.

6. **Logging**  
   - Append a JSON entry with timestamp, commit hash, compute spent, and metric deltas.

---

## Expected Timeline (Wall‑clock)

| Step | Wall‑clock |
|------|------------|
| Prompt Engineering | ~5 min |
| Synthetic QA Generation | ~7 min |
| Curriculum Warm‑up | ~5 min |
| Evaluation Expansion | ~4 min |
| Hyper‑parameter Search | ~5 min |
| Logging | <1 min |
| **Total** | **≈ 27 min** (well within the $1 compute budget) |

---

## Success Criteria

- **Metric uplift**: ≥ 2 % absolute improvement on primary task metric (e.g., F1/ROUGE).  
- **Robustness gain**: No regression on existing benchmarks; ≥ 1 % gain on new adversarial set.  
- **Reproducibility**: All experiments logged; artifacts versioned for future scaling.

---

## Next Steps After $1 Spend

If the above spend yields the expected uplift, allocate the next tranche of compute to:

1. **Scaling synthetic data generation** (order of magnitude more samples).  
2. **Full hyper‑parameter sweep** using Bayesian optimization.  
3. **Model distillation** to create a smaller, faster inference variant.  

--- 

*Prepared by the EXECUTION worker for experiment **exp_20260204_033313_unified_session_14** on 2026‑02‑04.*