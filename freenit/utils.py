from smtplib import SMTP


def sendmail(config, fromAddress, to, message):
    """
    from email.mime.text import MIMEText
    msg = MIMEText(
        rawmessage.format(
            fullname,
            content,
        ),
        'plain',
        'utf-8',
    )
    msg['From'] = 'meka@tilda.center'
    msg['Subject'] = 'Insurance'
    msg['To'] = to
    sendmail(
        current_app.config,
        'meka@tilda.center',
        [to],
        msg.as_string(),
    )
    """
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
        server.sendmail(fromAddress, to, message.encode('utf-8'))
