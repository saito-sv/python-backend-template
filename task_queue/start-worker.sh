#!/bin/bash

# TaskIQ worker startup script
# This script starts the TaskIQ worker process to handle background tasks

AUTORELOAD=${TASK_QUEUE_AUTORELOAD:-false}
LOG_LEVEL=${TASK_QUEUE_LOG_LEVEL:-INFO}
NUM_WORKERS=${TASK_QUEUE_NUM_WORKERS:-1}
TASKS_PER_WORKER=${TASK_QUEUE_TASKS_PER_WORKER:-50}

# Pattern to find task files
TASKS_PATTERN="app/**/tasks.py"

echo "Starting TaskIQ worker..."
echo "Looking for tasks in: ${TASKS_PATTERN}"
echo "Workers: ${NUM_WORKERS}"
echo "Tasks per worker: ${TASKS_PER_WORKER}"
echo "Log level: ${LOG_LEVEL}"
echo "Autoreload: ${AUTORELOAD}"

MAIN_COMMAND="uv run python -m taskiq worker task_queue.worker:broker -fsd --log-level ${LOG_LEVEL} --workers ${NUM_WORKERS} --max-async-tasks ${TASKS_PER_WORKER}"

if [ "$AUTORELOAD" = true ]; then
    echo "Running with autoreload enabled"
    ${MAIN_COMMAND} --reload -tp "${TASKS_PATTERN}"
else
    echo "Running without autoreload"
    ${MAIN_COMMAND} -tp "${TASKS_PATTERN}"
fi
