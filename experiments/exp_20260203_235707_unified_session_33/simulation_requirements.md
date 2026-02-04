# Simulation Requirements for Embodiment Test‑Bed

## 1. Core Packages
| Package | Version (tested) | Reason |
|---------|------------------|--------|
| Python | >=3.9,<3.13 | Compatibility with existing code |
| `pybullet` | 3.2.6 | Lightweight physics engine, easy URDF import |
| `mujoco` | 3.1.3 | High‑fidelity dynamics (optional) |
| `gymnasium` | 0.29.1 | Standard RL environment wrapper |
| `numpy` | 1.26.4 | Numerical operations |
| `opencv-python` | 4.9.0 | Image processing for visual grounding |
| `torch` | 2.3.0 | For any vision‑language‑action models used in the loop |
| `hydra-core` | 1.3.2 | Config management (optional) |

## 2. Environment Description
- **Name:** `BlockStackEnv-v0`
- **Observation Space:** Dict containing `rgb` (3×240×240 uint8), `depth` (1×240×240 float32), `joint_positions` (7‑dim float), optional `tactile`.
- **Action Space:** Discrete set of primitive actions (`MOVE_JOINT`, `GRIPPER_OPEN`, `GRIPPER_CLOSE`). Continuous parameters supplied via the `Action.parameters` dict.
- **Episode Length:** 200 steps (max) or until a successful stack is detected.

## 3. URDF Assets
- Simple 6‑DOF robot arm (e.g., Kuka iiwa) with parallel‑jaw gripper.
- Cubic blocks (size 0.05 m) with distinct colors for visual grounding.
- Table plane and static walls.

## 4. Domain Randomization (for sim‑to‑real transfer)
- Object textures & colors.
- Light direction/intensity.
- Joint friction coefficients.
- Camera pose jitter (±5 cm / ±5°).

## 5. Hardware (optional for later)
- **Robot:** Any ROS‑compatible 6‑DOF manipulator (e.g., UR5, Kuka iiwa).
- **Sensors:** RGB‑D camera (Intel RealSense D435), joint encoders (native), optional tactile skin.
- **Compute:** GPU (RTX 3080+) for vision‑language models; CPU ≥ 8 cores.

## 6. Build & Run Instructions (quick start)
```bash
# Create virtual env
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install deps
pip install -r requirements.txt   # generate this file from the table above

# Test environment
python -c "import gymnasium as gym; env = gym.make('BlockStackEnv-v0'); obs,_ = env.reset(); print(obs.keys())"
```

## 7. Success Metric Collection
- Episode reward = +1 for each correctly placed block, 0 otherwise.
- Pose error (L2) between target and final block position.
- Episode termination flag when stack height reaches 3 blocks.

*Prepared: 2026‑02‑04*