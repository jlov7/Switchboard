from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter
from typing import Any, cast

import httpx
import yaml


async def run_task(client: httpx.AsyncClient, task: dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()
    response = await client.post("/route", json={"request": task["request"]})
    latency = perf_counter() - start
    result = {
        "name": task["name"],
        "latency_ms": latency * 1000,
        "status_code": response.status_code,
    }
    payload = response.json()
    result["payload"] = payload
    if response.status_code == 202:
        result["requires_approval"] = True
    elif response.status_code == 403:
        result["blocked"] = True
    else:
        result["executed"] = True
    return result


async def run_suite(api_url: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_url, timeout=15.0) as client:
        results = [await run_task(client, task) for task in tasks]
    summary = {
        "total": len(tasks),
        "executed": sum(1 for item in results if item.get("executed")),
        "blocked": sum(1 for item in results if item.get("blocked")),
        "requires_approval": sum(1 for item in results if item.get("requires_approval")),
        "results": results,
    }
    return summary


def load_tasks(path: Path) -> list[dict[str, Any]]:
    raw_obj = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = cast(dict[str, Any], raw_obj)
    tasks = raw.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("tasks entry must be a list")
    return cast(list[dict[str, Any]], tasks)


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    if dataset_path.suffix in {".yaml", ".yml"}:
        return load_tasks(dataset_path)
    samples: list[dict[str, Any]] = []
    with dataset_path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                samples.append(cast(dict[str, Any], json.loads(line)))
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Switchboard evaluation runner (stub)")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path("evals/tasks/graph2eval_example.yaml"),
        help="Path to task suite YAML",
    )
    parser.add_argument("--output", type=Path, default=Path("evals/results.json"))
    parser.add_argument(
        "--dataset",
        type=Path,
        help="Optional dataset file (YAML or JSONL) to append to the suite",
    )
    args = parser.parse_args()

    tasks = load_tasks(args.suite)
    if args.dataset:
        tasks.extend(load_dataset(args.dataset))
    summary = asyncio.run(run_suite(args.api_url, tasks))
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Completed suite. Results written to {args.output}")


if __name__ == "__main__":
    main()
