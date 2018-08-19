#! /usr/bin/env python3
import smtplib
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

CONFIG_FILENAME = "server.ini"


def notify():
    conf = configparser.ConfigParser()

    conf.read(CONFIG_FILENAME)

    from_addr = conf['DEFAULT']['EmailUser']

    smtp_server = smtplib.SMTP(host=conf['DEFAULT']['EmailDomain'], port=conf['DEFAULT']['EmailSTARTTLSPort'])
    smtp_server.starttls()
    smtp_server.login(from_addr, conf['DEFAULT']['EmailPassword'])

    msg = MIMEMultipart()       # create a message

    # add in the actual person name to the message template
    message = f"Holy crap, the canary died! Time is {datetime.datetime.now()}"
    print(f"Message reads '{message}'")

    # setup the parameters of the message
    msg['From'] = from_addr
    msg['To'] = conf['DEFAULT']['EmailTarget']
    msg['Subject'] = conf['DEFAULT']['EmailSubject']

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # send the message via the server set up earlier.
    smtp_server.send_message(msg)

notify()