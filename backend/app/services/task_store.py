"""In-memory task store for background task results"""

tasks: dict[str, dict] = {}


def get_task(task_id: str) -> dict | None:
    """Get task data by ID, returns None if not found."""
    return tasks.get(task_id)


def set_task(task_id: str, data: dict) -> None:
    """Set task data for given ID."""
    tasks[task_id] = data


def delete_task(task_id: str) -> None:
    """Delete task data for given ID."""
    tasks.pop(task_id, None)
