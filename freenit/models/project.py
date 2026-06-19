from freenit.config import getConfig

config = getConfig()
project = config.get_model("project")

Project = project.Project
Board = project.Board
Column = project.Column
Task = project.Task
ProjectOptional = project.ProjectOptional
BoardOptional = project.BoardOptional
ColumnOptional = project.ColumnOptional
TaskOptional = project.TaskOptional
NotFoundError = project.NotFoundError
IntegrityError = project.IntegrityError
