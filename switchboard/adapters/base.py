from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any

from switchboard.core.models import ActionRequest


@dataclass
class AdapterResult:
    success: bool
    detail: str
    response: dict[str, Any]


class BaseAdapter(abc.ABC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    async def execute_action(self, request: ActionRequest) -> AdapterResult:
        """Execute the action against downstream system."""
