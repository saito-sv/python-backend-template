"""Background tasks for the user domain."""

from antidote import inject

from app.exc import EntityNotFoundException
from task_queue import task

from .service import UserService


@task
@inject
async def send_welcome_email(
    user_id: str,
    user_service: UserService = inject.me(),
) -> None:
    try:
        user = await user_service.get_user(user_id)
    except EntityNotFoundException:
        return
    print(f"Sending welcome email to {user.email}")


@task(schedule=[{"cron": "0 2 * * *", "args": []}])
@inject
async def cleanup_inactive_users(
    user_service: UserService = inject.me(),
) -> None:
    inactive_users = await user_service.list_inactive_users()
    print(f"Found {len(inactive_users)} inactive users to process")
