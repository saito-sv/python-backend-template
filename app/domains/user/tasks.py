"""Background tasks for the users domain.

Tasks are async functions decorated with @task that can be enqueued for background execution.
They use dependency injection via @inject decorator to access services and repositories.

This demonstrates that DI works in background tasks (not just FastAPI routes).
"""

from antidote import inject

from app.domains.user.service import UserService
from task_queue import task


@task
@inject
async def send_welcome_email(
    user_id: str,
    service: UserService = inject.me(),
) -> None:
    """
    Send a welcome email to a newly created user.

    This task uses dependency injection via @inject decorator.
    The UserService is automatically injected from Antidote.

    Usage:
        # Enqueue the task for async execution
        await send_welcome_email.kiq(user_id="usr_123...")
    """
    user = await service.get_user(user_id)
    if not user:
        return

    print(f"Sending welcome email to {user.email}")


@task
@inject
async def process_user_data(
    user_id: str,
    service: UserService = inject.me(),
) -> None:
    """
    Process user data in the background.

    This demonstrates a task that:
    - Uses dependency injection via @inject decorator
    - Performs business logic through the service layer
    - Can be enqueued from API endpoints or other tasks

    Usage:
        await process_user_data.kiq(user_id="usr_123...")
    """
    user = await service.get_user(user_id)
    if not user:
        return

    print(f"Processing data for user {user.email}")


@task(schedule=[{"cron": "0 2 * * *", "args": []}])
@inject
async def cleanup_inactive_users(
    service: UserService = inject.me(),
) -> None:
    """
    Clean up inactive users (scheduled task).

    This task runs daily at 2 AM UTC via cron schedule.
    Scheduled tasks are automatically executed by the TaskIQ worker.
    
    Demonstrates DI in scheduled cron tasks.
    """
    inactive_users = await service.repository.get_all(
        service.repository.is_active_filter(False)
    )
    count = len(inactive_users)

    print(f"Found {count} inactive users to process")


@task
@inject
async def _process_single_user(
    user_id: str,
    service: UserService = inject.me(),
) -> None:
    """
    Internal task for processing a single user.

    This demonstrates a private task (prefixed with _) that is called
    by other tasks but not directly from API endpoints.
    
    Uses DI just like public tasks.
    """
    await service.get_user(user_id)
