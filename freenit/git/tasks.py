from freenit.models.project import Board, Column, Task
from freenit.models.git import NotFoundError


async def task_project_id(task_id: int) -> int | None:
    """Return the project ID a kanban task belongs to."""
    try:
        task = await Task.objects.get(id=task_id)
    except NotFoundError:
        return None
    if task.column_id is None:
        return None
    try:
        column = await Column.objects.get(id=task.column_id)
    except NotFoundError:
        return None
    try:
        board = await Board.objects.get(id=column.board_id)
    except NotFoundError:
        return None
    return board.project_id


async def task_in_project(task_id: int, project_id: int) -> bool:
    return await task_project_id(task_id) == project_id
