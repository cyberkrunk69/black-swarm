import json
import time
from pathlib import Path

from domain_transfer_system import TaskRepresentation, DomainBridge, TransferMetrics
from benchmarks.transfer_learning_suite import run_all_benchmarks

def _log_metrics(metrics: TransferMetrics, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(metrics.summary()) + "\n")

def run_experiment() -> None:
    # Load benchmark scores (simulated)
    bench_results = run_all_benchmarks()

    for bench_name, scores in bench_results.items():
        src_domain, tgt_domain = bench_name.split("_to_")
        task = TaskRepresentation(
            domain=src_domain,
            name=bench_name,
            inputs={"dummy": "data"},
            outputs={"dummy": "data"},
            metadata={"benchmark": bench_name},
        )
        # Record source performance
        metrics = TransferMetrics(
            source_domain=src_domain,
            target_domain=tgt_domain,
            task_name=bench_name,
            source_score=scores["source_score"],
        )
        # Perform a bridge translation (may raise if not registered)
        try:
            translated = DomainBridge.translate(task, tgt_domain)
        except ValueError as e:
            print(f"[WARN] {e}")
            continue

        # Simulate target performance (use the benchmark's target score)
        metrics.stop(target_score=scores["target_score"])

        # Log
        log_file = Path("experiments/domain_transfer_test/metrics.log")
        _log_metrics(metrics, log_file)

        # Simple success criterion output
        improvement = metrics.improvement or 0.0
        print(
            f"{bench_name}: source={metrics.source_score:.2f}, "
            f"target={metrics.target_score:.2f}, "
            f"improvement={improvement*100:.1f}%"
        )

if __name__ == "__main__":
    start = time.time()
    run_experiment()
    print(f"Experiment completed in {time.time() - start:.2f}s")