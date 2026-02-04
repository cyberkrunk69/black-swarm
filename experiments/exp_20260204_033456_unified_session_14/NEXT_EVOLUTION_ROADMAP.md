# NEXT_EVOLUTION_ROADMAP.md

## Objective
Allocate the next **$1** of compute budget to initiatives that will deliver the highest incremental impact on model performance, data quality, and product value.

---

## Prioritized Action Items

| Rank | Initiative | Compute Allocation | Expected Impact | Rationale |
|------|------------|-------------------|----------------|-----------|
| 1 | **Targeted Data Augmentation for Low‑Resource Domains** | $0.30 | +3–5% downstream task accuracy in under‑represented categories | Generates synthetic examples where real data is scarce, improving model robustness with minimal compute. |
| 2 | **Fine‑tune a 1B‑parameter adapter on high‑value user feedback** | $0.25 | +2–3% relevance in top‑K recommendations | Adapter layers are cheap to train; directly leverages recent user signals for rapid gains. |
| 3 | **Curriculum Learning Schedule for Long‑Context Handling** | $0.20 | +1.5–2% performance on extended‑context benchmarks | Structured training order reduces wasted compute and improves long‑range coherence. |
| 4 | **Efficient Hyper‑parameter Sweep using Bayesian Optimization** | $0.15 | +1–1.5% overall validation loss reduction | Focuses compute on the most promising hyper‑parameter regions instead of grid search. |
| 5 | **Model Distillation to a 500M‑parameter student** | $0.10 | +0.5% inference speed, comparable accuracy | Produces a lighter model for downstream deployment, freeing future compute for experimentation. |

---

## Detailed Plans

### 1. Targeted Data Augmentation
- **Method:** Use controlled text generation (e.g., prompt‑based GPT) to create 10k–20k high‑quality samples for domains with <1k real examples.
- **Compute:** Run on a single A100 for ~6 hours.
- **Metrics:** Track domain‑specific F1 and overall validation loss.

### 2. Adapter Fine‑tuning
- **Method:** Insert lightweight adapters (≈2% of model parameters) after each transformer block.
- **Dataset:** Recent user interaction logs (last 48 h) filtered for high‑engagement sessions.
- **Compute:** 2‑epoch fine‑tune on a single A100 (~4 h).

### 3. Curriculum Learning for Long Context
- **Curriculum:** Start with short sequences (128 tokens), progressively increase to 2048 tokens.
- **Schedule:** 10% of compute on each length bucket, using the same base learning rate.
- **Compute:** Approx. 8 h on a single A100.

### 4. Bayesian Hyper‑parameter Optimization
- **Parameters:** Learning rate, weight decay, dropout, sequence length.
- **Tooling:** Optuna with a budget of 15 trials, each trial ~30 min on a single GPU.
- **Goal:** Identify a Pareto‑optimal configuration for the next fine‑tuning run.

### 5. Model Distillation
- **Teacher:** Current 2B‑parameter checkpoint.
- **Student:** 500M‑parameter transformer with identical architecture depth.
- **Loss:** Combined KL‑divergence + task‑specific loss.
- **Compute:** 6 h on a single A100.

---

## Execution Timeline (Total ~ $1)

| Day | Activity |
|-----|----------|
| Day 1 | Set up data augmentation pipeline; start generation (3 h). |
| Day 2 | Begin adapter fine‑tuning (4 h) while augmentation finishes. |
| Day 3 | Run curriculum learning phase (8 h) in parallel with hyper‑parameter optimization. |
| Day 4 | Conduct Bayesian optimization trials (7.5 h total). |
| Day 5 | Perform model distillation (6 h). |
| Day 6 | Consolidate results, update documentation, and prepare next experiment proposal. |

---

## Success Criteria

- **Quantitative:** At least one of the top‑3 initiatives must deliver a measurable lift (≥1% absolute) on a held‑out validation set.
- **Qualitative:** Improved handling of low‑resource domains and longer contexts as observed in manual inspection.
- **Efficiency:** All compute stays within the $1 budget (≈ 100 GPU‑hours on an A100 at $10/hour).

---

## Next Steps After Completion

1. **Analyze** which initiative gave the highest ROI.
2. **Scale** the winning approach (e.g., increase augmentation volume or extend adapter training) with the next compute tranche.
3. **Iterate** on the curriculum schedule based on observed convergence patterns.
4. **Publish** findings internally and update the roadmap for the following $1 compute allocation.

--- 

*Prepared by the Execution Team, 2026‑02‑04.*