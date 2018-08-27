#! /usr/bin/env python3

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import List, Optional
import configparser
import datetime
import smtplib
import socket
import threading
import time

lock = threading.Condition()
shared_list: List[str] = []
threads_run = False
shared_timestamp: Optional[datetime.datetime] = None

CONFIG_FILENAME = "server.ini"

conf = configparser.ConfigParser()
conf.read(CONFIG_FILENAME)
TIMEOUT_IN_SECONDS = int(conf['DEFAULT']['TimeoutInSeconds'])


class CanaryStates(Enum):
    CANARY_ALIVE = 1
    CANARY_DEAD = 2
    CANARY_NEVER_SEEN = 3


def log(message):
    print(f"canary_server\t{datetime.datetime.now()}\t{message}")


class Listener(threading.Thread):
    def __init__(self, clientsocket: socket.socket, address, daemon=False) -> None:
        super(Listener, self).__init__(daemon=True)
        log("Starting listener thread...")
        self.socket = clientsocket
        self.address = address
        self.buffer = ""

    def __del__(self):
        self.socket.close()

    def run(self):
        global threads_run
        global shared_timestamp

        while threads_run:
            _ = self.socket.recv(64)

            shared_timestamp = datetime.datetime.now()

        self.socket.close()


class Notifier(threading.Thread):
    def __init__(self) -> None:
        super(Notifier, self).__init__()
        log("Starting notifier...")
        self.canary_alive = False

    @staticmethod
    def notify(text="", subject=""):
        """
        Adapted from https://medium.freecodecamp.org/send-emails-using-code-4fcea9df63f
        """

        from_addr = conf['DEFAULT']['EmailUser']

        smtp_server = smtplib.SMTP(host=conf['DEFAULT']['EmailDomain'], port=conf['DEFAULT']['EmailSTARTTLSPort'])
        smtp_server.starttls()
        smtp_server.login(from_addr, conf['DEFAULT']['EmailPassword'])

        message = text + "\n\nTime is: " + str(datetime.datetime.now())
        print(f"Message reads '{message}'")

        for recipient in conf['DEFAULT']['EmailTarget'].split(','):
            msg = MIMEMultipart()       # create a message

            msg['From'] = from_addr
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            smtp_server.send_message(msg)

            log(f"Notification sent to {recipient}")

    def run(self):
        global threads_run
        global shared_timestamp

        log("Notifier sleeping...")
        time.sleep(TIMEOUT_IN_SECONDS)  # give time for everything to initialize

        state: CanaryStates = CanaryStates.CANARY_NEVER_SEEN

        while threads_run:
            timeout_point = datetime.datetime.now() - datetime.timedelta(seconds=TIMEOUT_IN_SECONDS)

            if state == CanaryStates.CANARY_NEVER_SEEN:
                if shared_timestamp is None:
                    log("Waiting for canary...")
                else:
                    log("Canary seen for the first time!")
                    state = CanaryStates.CANARY_ALIVE

            elif state == CanaryStates.CANARY_ALIVE:
                if shared_timestamp < timeout_point:
                    state = CanaryStates.CANARY_DEAD
                    log("Canary has died.")
                    Notifier.notify("The canary has died.", "Fridge down")
                else:
                    log("Canary still alive!")

            elif state == CanaryStates.CANARY_DEAD:
                if shared_timestamp < timeout_point:
                    log("Canary still dead.")
                else:
                    state = CanaryStates.CANARY_ALIVE
                    log("Canary has returned!")
                    Notifier.notify("The canary has returned", "Fridge back up")

            time.sleep(TIMEOUT_IN_SECONDS)


class Overseer(threading.Thread):
    def __init__(self, threads):
        super(Overseer, self).__init__(daemon=True)
        log("Starting overseer thread...")

    def run(self):
        global threads_run

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(("192.168.1.57", 5555))
        serversocket.listen()

        while threads_run:
            (clientsocket, address) = serversocket.accept()
            _ = Listener(clientsocket, address, daemon=True)
            _.start()

        serversocket.close()


def main():
    global threads_run
    global shared_list
    threads = []

    threads_run = True

    threads.append(Overseer(threads_run))
    threads.append(Notifier())

    for thread in threads:
        thread.start()

    while threads_run:

        instr = ""
        while instr != "stop":
            instr = input("enter 'stop' to stop.\n")

        threads_run = False

    log("Waiting for threads...")


main()
