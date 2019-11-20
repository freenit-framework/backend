from smtplib import SMTP


def sendmail(config, to, message):
    port = config['MAIL'].get('port', 587)
    ssl = config['MAIL'].get('ssl', True)
    host = config['MAIL'].get('host', None)
    username = config['MAIL'].get('username', None)
    password = config['MAIL'].get('password', None)
    if None not in [host, username, password]:
        server = SMTP(host=host, port=port)
        if ssl:
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(username, password)
        server.sendmail(
            message['From'],
            to,
            message.as_string().encode('utf-8')
        )
