# Integration Roadmap – Embodiment Layer for the AGI System

## Overview
This roadmap outlines concrete milestones to integrate the **Embodiment Interface** (see `embodiment_interface_spec.py`) with the existing AGI code‑base and to validate it in simulation before any hardware deployment.

| Phase | Milestone | Description | Owner | ETA |
|-------|-----------|-------------|-------|-----|
| **0** | Repo Preparation | Add `experiments/exp_20260203_235707_unified_session_33/` folder, commit spec files. | DevOps | 2026‑02‑04 |
| **1** | Simulator Backend Prototype | Implement `sim_backend.py` that subclasses `EmbodimentInterface` using PyBullet. Provide `reset`, `step`, `encode_state`. | Simulation Engineer | 2026‑02‑10 |
| **2** | Core AGI Hook | Extend the AGI inference loop (`core_agent.py` placeholder) to call `EmbodimentInterface.get_observation()` → `encode_state` → feed to language model → receive intent → use `ActionPlannerAdapter`. | Core Team | 2026‑02‑14 |
| **3** | Simple Task Validation | Run 100 episodes of the **block stacking** task, collect success rate, reward curves. Adjust domain randomization. | QA / RL Engineer | 2026‑02‑21 |
| **4** | Vision‑Language‑Action (VLA) Integration | Plug a pre‑trained VLA model (e.g., Flamingo‑VLA) to generate low‑level actions directly from visual observations. Compare against planner baseline. | Perception Team | 2026‑02‑28 |
| **5** | Sim‑to‑Real Transfer Prep | Add ROS wrapper (`ros_backend.py`) implementing the same abstract API. Validate on a **virtual ROS bridge** (Gazebo). | Robotics Engineer | 2026‑03‑07 |
| **6** | Real‑World Pilot (Optional) | Deploy on a UR5 with RealSense camera. Run 20 manual episodes, log pose error. | Field Engineer | 2026‑03‑21 |
| **7** | Feedback Loop & Online Learning | Store `(state, action, reward, next_state)` tuples; fine‑tune the language model via RLHF or PPO. | Research Lead | 2026‑04‑01 |
| **8** | Documentation & Release | Consolidate design docs, API docs, example notebooks. Tag release `embodiment_v0.1`. | Docs Team | 2026‑04‑07 |

## Dependency Mapping
- **Embodiment Interface** → `embodiment_interface_spec.py` (design only).  
- **Simulator Backend** → `pybullet`, `gymnasium`.  
- **Action Planner** → Existing planning module (`planner.py`) – adapt to accept `State` objects.  
- **Vision Module** → `torchvision`, optional CLIP/VLA models.  
- **Real Robot** → ROS Noetic/ROS2 Foxy, `ros_control`, `moveit2`.  

## Cost & Feasibility
| Item | Approx. Cost (USD) | Comments |
|------|-------------------|----------|
| Development time (4 engineers, 2 months) | $80,000 | Salaries only |
| Cloud GPU compute (training VLA) | $2,000 | Spot instances |
| PyBullet / MuJoCo licenses | $0–$1,500 | MuJoCo free for research, commercial may need license |
| Robot hardware (UR5 + RealSense) | $12,000 | If not already owned |
| ROS & simulation tools | $0 | Open source |
| Misc. (cabling, safety cages) | $1,500 | Safety compliance |

**Total (simulation‑only)** ≈ **$82k**  
**Full hardware path** ≈ **$95k** – well within typical R&D budget.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Sim‑to‑Real gap too large | Failure on hardware | Use extensive domain randomization; consider system identification. |
| API mismatch with future modules | Integration delays | Keep interface minimal and versioned; use semantic versioning. |
| Real‑time constraints (latency) | Unstable control | Benchmark step latency; offload heavy vision to async thread. |
| Safety on real robot | Damage / injury | Enforce `safety_*.py` checks; add a watchdog that halts on out‑of‑bounds commands. |

## Success Criteria (final)
- **Simulation:** ≥90 % task success across 500 randomized episodes.  
- **Transfer:** Pose error ≤2 cm when running the same policy on the real robot (if hardware available).  
- **Code Quality:** 90 % test coverage on `EmbodimentInterface` implementations, static type checking passes.  

*Roadmap authored by the Embodiment Integration Team – 2026‑02‑04*