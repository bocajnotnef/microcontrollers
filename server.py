import socket
import threading
from typing import List

lock = threading.Condition()
shared_list: List[str] = []
threads_run = False


class Listener(threading.Thread):
    def __init__(self, clientsocket: socket.socket, address) -> None:
        super(Listener, self).__init__()
        print("Starting listener thread...")
        self.socket = clientsocket
        self.address = address
        self.buffer = ""

    def run(self):
        global lock
        global shared_list
        global threads_run

        while threads_run:
            data = self.socket.recv(128)
            datastr = self.buffer + data.decode('utf-8')
            self.buffer = ""
            split = datastr.split("\n")
            self.buffer = split[-1]
            split = split[:-1]

            with lock:
                shared_list.extend(split)
                lock.notify()

        self.socket.close()


class Overseer(threading.Thread):
    def __init__(self, threads):
        super(Overseer, self).__init__()
        print("Starting overseer thread...")

    def run(self):
        global threads_run

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(("192.168.1.172", 5555))
        serversocket.listen()

        while threads_run:
            (clientsocket, address) = serversocket.accept()
            l = Listener(clientsocket, address)
            l.start()

        serversocket.close()


def main():
    global threads_run
    global shared_list
    threads = []

    threads_run = True

    threads.append(Overseer(threads_run))
    threads[0].start()

    while threads_run:

        instr = ""
        while instr != "stop":
            instr = input("enter 'stop' to stop: ")

        threads_run = False

    print("Waiting for threads...")

    for thread in threads:
        thread.join()

    print("Dumping shared list to file....")

    with open("recieved_data.txt", 'w') as ofile:
        ofile.write("\n".join(shared_list) + "n")


main()
