from freenit.config import getConfig

config = getConfig()
ml = config.get_model("mailinglist")

MailingList = ml.MailingList
PendingSubscriber = ml.PendingSubscriber
ModerationMessage = ml.ModerationMessage
NotFoundError = ml.NotFoundError
IntegrityError = ml.IntegrityError
