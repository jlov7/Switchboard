# Evaluation Harness

Switchboard ships with an extensible evaluation runner (`evals/runner.py`).

## Quick usage

```bash
python evals/runner.py --api-url http://localhost:8000 \
  --suite evals/tasks/graph2eval_example.yaml \
  --output evals/results.json
```

## Adding real datasets

The runner accepts `--dataset` pointing to a YAML task file or JSONL:

```bash
python evals/runner.py --suite evals/tasks/graph2eval_example.yaml \
  --dataset data/graph2eval_sample.jsonl
```

Each JSONL entry should look like:

```json
{"name": "ticket-update", "request": {"context": {...}, "tool_name": "jira", "tool_action": "update_issue", "arguments": {"data": {...}}}}
```

## Reporting

- Results: `evals/results.json`
- Coverage badge: `scripts/report_coverage.sh`
- Mutation report: `scripts/report_mutation.sh`

## Future ideas

- Integrate full Graph2Eval / SWE-Bench tasks via dataset option.
- Export metrics to Prometheus and surface in Grafana dashboard.

Sample dataset: `evals/datasets/graph2eval_sample.jsonl`.
