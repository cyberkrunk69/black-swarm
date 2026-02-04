# Embodiment & Physical World Grounding Design
**Experiment:** exp_20260203_235707_unified_session_33  
**Goal:** Provide a clear architectural blueprint that enables the AGI system to perceive, act, and learn in the physical world (or high‑fidelity simulation) while remaining compatible with the existing code‑base.

## 1. High‑Level Architecture
```
+-------------------+       +-------------------+       +-------------------+
|   Language Model  | <---> |   Embodiment     | <---> |   Simulator /    |
|   (Core AGI)      |       |   Interface      |       |   Robot API      |
+-------------------+       +-------------------+       +-------------------+
          ^                         ^                         ^
          |                         |                         |
   Planning &               Observation &                Action
   Reasoning                State Encoding                Execution
```

* **Core AGI** – unchanged; produces high‑level intents (e.g., “stack block A on B”).
* **Embodiment Interface** – abstract API (see `embodiment_interface_spec.py`) that translates intents into concrete actions, receives raw sensor data, and returns a normalized state representation.
* **Backend** – pluggable implementation:
  * **Simulation** – PyBullet / MuJoCo environment.
  * **Real‑world** – ROS‑based robot drivers, OpenAI Gym‑compatible wrappers, or vendor SDKs.

## 2. Core Components
| Component | Responsibility | Key Functions |
|-----------|----------------|---------------|
| `EmbodimentInterface` (abstract) | Define contract for perception, actuation, and feedback. | `reset()`, `step(action)`, `get_observation()`, `encode_state(obs)` |
| `SimulatorBackend` | Host a lightweight physics sim for rapid iteration. | Load URDF, step simulation, render RGB‑D. |
| `RobotBackend` | Bridge to real hardware (optional for now). | Connect to ROS, send joint commands, read joint states, camera streams. |
| `ActionPlannerAdapter` | Convert high‑level plans (e.g., “pick‑place”) into low‑level action sequences. | `plan_to_actions(plan)`. |
| `FeedbackLoop` | Close the sense‑plan‑act‑learn cycle. | Collect reward/metrics, trigger model updates. |

## 3. Data Flow
1. **Sense** – `EmbodimentInterface.get_observation()` returns raw sensor payload (RGB‑D, joint states, tactile).  
2. **Encode** – `encode_state(obs)` normalizes to a fixed‑size tensor (`state_dict`).  
3. **Plan** – Core AGI consumes `state_dict` and emits an intent.  
4. **Act** – `ActionPlannerAdapter` expands intent → list of primitive actions (`Action` objects).  
5. **Execute** – Backend `step(action)` applies actions; returns next observation & reward.  
6. **Learn** – Feedback stored for offline fine‑tuning or online RL updates.

## 4. Extensibility
* New simulators can be added by subclassing `SimulatorBackend`.  
* Real‑robot drivers are isolated behind `RobotBackend`; no changes to AGI logic.  
* Action space is defined as an enum (`GRIPPER_OPEN`, `GRIPPER_CLOSE`, `MOVE_JOINT`, `MOVE_EE_POS`).  

## 5. Success Metrics (Simulation)
| Metric | Target |
|--------|--------|
| Task Completion Rate (block stacking) | ≥ 90 % in 100 trials |
| Sample Efficiency | ≤ 2000 steps per successful stack |
| Sim‑to‑Real Gap (pose error) | ≤ 2 cm after domain randomization |

---

*Prepared by the Embodiment Design Team – 2026‑02‑04*