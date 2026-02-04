"""
experiments/domain_transfer_test/run_transfer_tests.py
-----------------------------------------------------

Simple driver that loads the benchmark suite, registers source skills,
attempts transfers, and prints the aggregated metrics.
"""

from domain_transfer_system import DomainBridge
from benchmarks.transfer_learning_suite import (
    code_to_math_benchmark,
    ui_to_arch_benchmark,
    debug_to_physics_benchmark,
)

def run_bridge(bridge: DomainBridge,
               benchmark_fn):
    src_task, src_skill, tgt_task, success_pred = benchmark_fn()
    bridge.register_skill(task_name=src_task.name,
                          raw_text=src_task.metadata.get('raw_text', ''),
                          skill_fn=src_skill)
    success, sim = bridge.attempt_transfer(target_task_name=tgt_task.name,
                                           target_raw=tgt_task.metadata.get('raw_text', ''),
                                           success_predicate=success_pred)
    print(f"[{bridge.source}->{bridge.target}] {src_task.name} → {tgt_task.name}: "
          f"Success={success}, Similarity={sim:.3f}")

def main():
    # 1. Code → Math
    bridge_cm = DomainBridge(source_domain="code", target_domain="math")
    run_bridge(bridge_cm, code_to_math_benchmark)

    # 2. UI → Architecture
    bridge_ua = DomainBridge(source_domain="ui", target_domain="architecture")
    run_bridge(bridge_ua, ui_to_arch_benchmark)

    # 3. Debugging → Physics
    bridge_dp = DomainBridge(source_domain="debugging", target_domain="physics")
    run_bridge(bridge_dp, debug_to_physics_benchmark)

    # Report aggregate metrics
    for bridge in (bridge_cm, bridge_ua, bridge_dp):
        print(f"\nMetrics for {bridge.source}->{bridge.target}:")
        print(f"  Success Rate: {bridge.metrics.success_rate*100:.1f}%")
        print(f"  Avg Similarity: {bridge.metrics.average_similarity:.3f}")

if __name__ == "__main__":
    main()