from freenit.config import getConfig

config = getConfig()
git = config.get_model("git")

GitRepo = git.GitRepo
GitPermission = git.GitPermission
GitPushLog = git.GitPushLog
GitCommitTaskRef = git.GitCommitTaskRef
NotFoundError = git.NotFoundError
IntegrityError = git.IntegrityError
