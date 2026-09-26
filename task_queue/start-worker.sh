#!/bin/bash
set -euo pipefail

AUTORELOAD=${TASK_QUEUE_AUTORELOAD:-false}
LOG_LEVEL=${TASK_QUEUE_LOG_LEVEL:-INFO}
NUM_WORKERS=${TASK_QUEUE_NUM_WORKERS:-1}
TASKS_PER_WORKER=${TASK_QUEUE_TASKS_PER_WORKER:-50}
TASKS_PATTERN="app/**/tasks.py"

args=(
  worker task_queue.worker:broker -fsd
  --log-level "$LOG_LEVEL"
  --workers "$NUM_WORKERS"
  --max-async-tasks "$TASKS_PER_WORKER"
  -tp "$TASKS_PATTERN"
)
if [ "$AUTORELOAD" = "true" ]; then
  args+=(--reload)
fi

echo "Starting TaskIQ worker (workers=${NUM_WORKERS}, tasks/worker=${TASKS_PER_WORKER}, reload=${AUTORELOAD})"
exec uv run python -m taskiq "${args[@]}"
