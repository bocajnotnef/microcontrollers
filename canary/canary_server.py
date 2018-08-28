#! /usr/bin/env python3

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import List, Optional
import argparse
import datetime
import json
import smtplib
import socket
import threading
import time

lock = threading.Condition()
shared_list: List[str] = []
threads_run = False
shared_timestamp: Optional[datetime.datetime] = None

CONFIG_FILENAME = "server_config.json"

TIMEOUT_IN_SECONDS = 10
config = None


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
        global config

        from_addr = config['email']['user']

        smtp_server = smtplib.SMTP(host=config['email']['domain'],
                                   port=config['email']['STARTLSPort'])
        smtp_server.starttls()
        smtp_server.login(config['email']['user'], config['email']['password'])

        message = text + "\n\nTime is: " + str(datetime.datetime.now())
        log(f"Message reads '{message}'")

        for recipient in config['email']['targets']:
            msg = MIMEMultipart()       # create a message

            msg['From'] = from_addr
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            if config['debug']:
                print(f"Debug mode; notification not sent. Text is: \n{msg}\n{msg}\nNot sent to {config['email']['targets']}")
            else:
                smtp_server.send_message(msg)

            log(f"Notification sent to {recipient}")

    def run(self):
        global threads_run
        global shared_timestamp
        global config

        log("Notifier sleeping...")
        time.sleep(config['timeout'])  # give time for everything to initialize

        state: CanaryStates = CanaryStates.CANARY_NEVER_SEEN

        while threads_run:
            timeout_point = datetime.datetime.now() - datetime.timedelta(seconds=config['timeout'])
            Notifier.notify("this is a test and you shouldn't get this message", "teeeeessssttt")

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

            time.sleep(config['timeout'])


class Overseer(threading.Thread):
    def __init__(self, threads):
        super(Overseer, self).__init__(daemon=True)
        log("Starting overseer thread...")

    def run(self):
        global threads_run

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind((config['server']['address'], config['server']['port']))
        serversocket.listen()

        while threads_run:
            (clientsocket, address) = serversocket.accept()
            _ = Listener(clientsocket, address, daemon=True)
            _.start()

        serversocket.close()


def get_args_and_config():
    global config

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', help="path to json config file",
                        default="server_config.json")
    parser.add_argument('--debug-mode', help="enable debug mode", action="store_true")
    parser.add_argument('--server-port', help="specify the server port", type=int)
    parser.add_argument('--timeout', help="timeout in seconds", type=int)
    parser.add_argument('--email-password', help="password to the email account")
    parser.add_argument('--server-address', help="the IP address of this server")

    args = parser.parse_args()

    with open(args.config_file) as conf_file:
        config = json.loads(conf_file.read())

    if args.debug_mode is not None:
        config['debug'] = args.debug_mode
    if args.timeout is not None:
        config['timeout'] = args.timeout
    if args.server_port is not None:
        config['server']['port'] = args.server_port
    if args.email_password is not None:
        config['email']['password'] = args.email_password

    return config


def main():
    global threads_run
    global shared_list
    global conf
    threads = []

    config = get_args_and_config()

    if config['debug']:
        print("Debug config dump")
        print(config)
        # return 0

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
