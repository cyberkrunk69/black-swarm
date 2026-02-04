"""
meta_learning_demo.py

A tiny meta‑learning illustration using Model‑Agnostic Meta‑Learning (MAML)
style updates on a synthetic regression task.  The code shows:

* Generation of a family of simple sine‑wave tasks.
* A shared linear model (weight, bias) that is quickly adapted to each
  task with a few gradient steps.
* Evaluation of cross‑task transfer (meta‑learning) vs. training from
  scratch.

The implementation is deliberately lightweight and uses only NumPy.
"""

import numpy as np
from typing import List, Tuple


# ---------- Synthetic task generation ----------
def generate_sine_task(amplitude: float, phase: float, noise_std: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """Return (x, y) pairs for a sine wave with given amplitude & phase."""
    x = np.linspace(-5, 5, 50)
    y = amplitude * np.sin(x + phase) + np.random.normal(0, noise_std, size=x.shape)
    return x, y


def sample_task_family(num_tasks: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Create a list of regression datasets representing different tasks."""
    tasks = []
    rng = np.random.default_rng(42)
    for _ in range(num_tasks):
        amp = rng.uniform(0.5, 2.0)
        ph = rng.uniform(0, np.pi)
        tasks.append(generate_sine_task(amp, ph))
    return tasks


# ---------- Simple linear model ----------
class LinearModel:
    """y = w * x + b"""

    def __init__(self):
        self.w = np.random.randn()
        self.b = np.random.randn()

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.w * x + self.b

    def loss(self, x: np.ndarray, y: np.ndarray) -> float:
        preds = self.predict(x)
        return np.mean((preds - y) ** 2)

    def grad(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """Return gradients dL/dw, dL/db."""
        preds = self.predict(x)
        error = preds - y
        dw = 2 * np.mean(error * x)
        db = 2 * np.mean(error)
        return dw, db

    def sgd_step(self, x: np.ndarray, y: np.ndarray, lr: float = 0.01):
        dw, db = self.grad(x, y)
        self.w -= lr * dw
        self.b -= lr * db


# ---------- Meta‑learning (MAML‑style) ----------
def maml_adapt(
    model: LinearModel,
    x_support: np.ndarray,
    y_support: np.ndarray,
    inner_lr: float = 0.01,
    inner_steps: int = 5,
) -> LinearModel:
    """
    Perform a few inner‑loop gradient updates on the support set.
    Returns a *new* model instance representing the adapted parameters.
    """
    adapted = LinearModel()
    adapted.w, adapted.b = model.w, model.b  # copy parameters

    for _ in range(inner_steps):
        adapted.sgd_step(x_support, y_support, lr=inner_lr)
    return adapted


def meta_train(
    tasks: List[Tuple[np.ndarray, np.ndarray]],
    meta_lr: float = 0.001,
    inner_lr: float = 0.01,
    inner_steps: int = 5,
    epochs: int = 200,
) -> LinearModel:
    """
    Very small MAML loop:
    * Sample a task.
    * Split into support / query.
    * Compute adapted model on support.
    * Compute query loss w.r.t. original parameters.
    * Gradient‑step the original parameters.
    """
    # Initialise meta‑parameters
    meta_model = LinearModel()

    for epoch in range(epochs):
        # Randomly pick a task
        x, y = tasks[np.random.randint(len(tasks))]
        # 70/30 split
        split = int(0.7 * len(x))
        x_supp, y_supp = x[:split], y[:split]
        x_query, y_query = x[split:], y[split:]

        # Adaptation
        adapted = maml_adapt(meta_model, x_supp, y_supp, inner_lr, inner_steps)

        # Compute query loss and its gradient w.r.t. meta parameters
        # For a linear model the gradient can be derived analytically;
        # here we approximate with a finite‑difference step for brevity.
        eps = 1e-5
        original_w, original_b = meta_model.w, meta_model.b

        # Perturb w
        meta_model.w = original_w + eps
        loss_plus = adapted.loss(x_query, y_query)
        meta_model.w = original_w - eps
        loss_minus = adapted.loss(x_query, y_query)
        dw = (loss_plus - loss_minus) / (2 * eps)

        # Perturb b
        meta_model.w = original_w  # restore
        meta_model.b = original_b + eps
        loss_plus = adapted.loss(x_query, y_query)
        meta_model.b = original_b - eps
        loss_minus = adapted.loss(x_query, y_query)
        db = (loss_plus - loss_minus) / (2 * eps)

        # Gradient descent on meta parameters
        meta_model.w = original_w - meta_lr * dw
        meta_model.b = original_b - meta_lr * db

    return meta_model


def evaluate(model: LinearModel, task: Tuple[np.ndarray, np.ndarray]) -> float:
    x, y = task
    return model.loss(x, y)


if __name__ == "__main__":
    # ---- Demo workflow ----
    np.random.seed(0)
    task_family = sample_task_family(num_tasks=8)

    # Train meta‑learner
    meta_model = meta_train(task_family, epochs=300)

    # Compare adaptation speed on a *new* unseen task
    unseen_task = generate_sine_task(amplitude=1.5, phase=0.8)

    # 1) Train from scratch (baseline)
    scratch = LinearModel()
    for _ in range(100):
        scratch.sgd_step(*unseen_task, lr=0.01)
    baseline_loss = evaluate(scratch, unseen_task)

    # 2) Meta‑learned quick adaptation
    adapted = maml_adapt(meta_model, *unseen_task, inner_lr=0.01, inner_steps=5)
    adapted_loss = evaluate(adapted, unseen_task)

    print(f"Baseline (100 SGD steps) loss: {baseline_loss:.4f}")
    print(f"Meta‑adapted (5 inner steps) loss: {adapted_loss:.4f}")