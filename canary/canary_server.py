#! /usr/bin/env python3

from typing import List, Optional
import datetime
import socket
import threading
import time

lock = threading.Condition()
shared_list: List[str] = []
threads_run = False
shared_timestamp: Optional[datetime.datetime] = None

TIMEOUT_IN_SECONDS = 10


class Listener(threading.Thread):
    def __init__(self, clientsocket: socket.socket, address) -> None:
        super(Listener, self).__init__()
        print("Starting listener thread...")
        self.socket = clientsocket
        self.address = address
        self.buffer = ""

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
        print("Starting notifier thread...")

    def run(self):
        global threads_run
        global shared_timestamp

        print("Notifier sleeping...")
        time.sleep(20) # give time for everything to initialize

        while threads_run:
            timeout_point = datetime.datetime.now() - datetime.timedelta(seconds=TIMEOUT_IN_SECONDS)
            if shared_timestamp is None:
                print("Something odd happened.... (Have we made a connection yet?)")
            elif shared_timestamp < timeout_point:
                print("OH GOD WHERE ARE THEY SOUND THE ALARM")
            else:
                print("Notifier sleeps")
            time.sleep(TIMEOUT_IN_SECONDS)


class Overseer(threading.Thread):
    def __init__(self, threads):
        super(Overseer, self).__init__()
        print("Starting overseer thread...")

    def run(self):
        global threads_run

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(("192.168.1.57", 5555))
        serversocket.listen()

        while threads_run:
            (clientsocket, address) = serversocket.accept()
            _ = Listener(clientsocket, address)
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
            instr = input("enter 'stop' to stop: ")

        threads_run = False

    print("Waiting for threads...")

    for thread in threads:
        thread.join()


main()
