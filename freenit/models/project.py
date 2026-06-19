from freenit.config import getConfig

config = getConfig()
project = config.get_model("project")

Project = project.Project
Board = project.Board
Column = project.Column
Task = project.Task
Project = project.Project
Board = project.Board
Column = project.Column
Task = project.Task
ProjectGroup = project.ProjectGroup
ProjectGroupPermission = project.ProjectGroupPermission
ProjectMember = project.ProjectMember
ProjectOptional = project.ProjectOptional
BoardOptional = project.BoardOptional
ColumnOptional = project.ColumnOptional
TaskOptional = project.TaskOptional
ProjectGroupOptional = project.ProjectGroupOptional
NotFoundError = project.NotFoundError
IntegrityError = project.IntegrityError
