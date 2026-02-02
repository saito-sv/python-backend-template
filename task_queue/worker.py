"""TaskIQ worker entry point.

This module is used by the TaskIQ CLI to start worker processes.
The broker is imported here so it's available as 'broker' for the CLI.

Usage:
    uv run python -m taskiq worker task_queue.worker:broker -tp "app/**/tasks.py"
"""

from task_queue.task_broker import broker

__all__ = ["broker"]
