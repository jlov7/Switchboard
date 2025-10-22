# Evaluation Harness (Stub)

This directory contains scaffolding for advanced agent evaluations inspired by **Graph2Eval**, **FreshBrew**, and **SWE-Bench-Pro**. The harness is intentionally lightweight so it can run inside constrained environments without shipping benchmark data.

## Layout

- `tasks/graph2eval_example.yaml` – placeholder multi-step tool-use scenario.
- `tasks/swe_bench_pro_stub.yaml` – outlines a contamination-resistant SWE-Bench-Pro style case.
- `runner.py` – CLI entry point that executes the scenarios against the Switchboard API and records pass/fail metrics.
- `utils.py` – shared metric helpers that focus on safety block/approval rates and latency.

## Next Steps

1. Replace the stub task definitions with sanitized public tasks or synthetic workloads.
2. Extend `runner.py` to stream telemetry into your preferred metrics lake (Prometheus, DataDog, etc.).
3. Integrate the harness with CI to catch regressions in policy enforcement, adapter resilience, and contamination handling.
