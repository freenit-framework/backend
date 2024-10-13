from smtplib import SMTP

from freenit.config import getConfig

config = getConfig()


def sendmail(to, message):
    mail = config.mail
    server = SMTP(host=mail.server, port=mail.port)
    if mail.tls:
        server.ehlo()
        server.starttls()
        server.ehlo()
    server.login(mail.user, mail.password)
    server.sendmail(message["From"], to, message.as_string().encode("utf-8"))
