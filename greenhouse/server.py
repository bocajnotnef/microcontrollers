#! /usr/bin/env python3

from collections import namedtuple, defaultdict
from typing import List
import datetime
import socket
import sqlite3
import threading
import time

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
        serversocket.bind(("192.168.1.149", 5555))
        serversocket.listen()

        while threads_run:
            (clientsocket, address) = serversocket.accept()
            l = Listener(clientsocket, address)
            l.start()

        serversocket.close()


class DBWriter(threading.Thread):
    def __init__(self):
        super(DBWriter, self).__init__()
        print("Starting DB writer thread...")

    def run(self):
        global threads_run
        global lock
        global shared_list

        connection = sqlite3.connect("greenhouse.db")
        connection.execute("CREATE TABLE if not exists readings "
                           "(source text, "
                           "airtemp real, "
                           "humidity real, "
                           "soil_moisture int, "
                           "timestamp text);")

        while threads_run:
            time.sleep(60)

            to_load_into_database = []
            with lock:
                if len(shared_list) > 0:
                    to_load_into_database = list(shared_list)
                    shared_list.clear()

            print(f"Condensing {len(to_load_into_database)} records...")
            by_source = defaultdict(list)
            record = namedtuple('SensorRecord', ['air_temp', 'air_hum', 'soil_moisture'])
            for line in to_load_into_database:
                line = line.split(';')
                mac = line[3].strip().split(" ")[1]
                by_source[mac].append(
                    record(
                        float(line[1].strip().split(" ")[1]),
                        float(line[2].strip().split(" ")[1]),
                        int(line[0].strip().split(" ")[1]),
                    )
                )

            for key in by_source:
                list_len = float(len(by_source[key]))

                avg_temp = 0
                avg_hum = 0
                avg_soil = 0

                for record in by_source[key]:
                    avg_temp += record.air_temp
                    avg_hum += record.air_hum
                    avg_soil += record.soil_moisture

                avg_temp /= list_len
                avg_hum /= list_len
                avg_soil /= list_len
                timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                values = f" ('{key}', {avg_temp}, {avg_hum}, {avg_soil}, '{timestamp}')"
                print(f"Writing {values} to DB")
                connection.execute(f"INSERT INTO readings VALUES {values};")
            print("Sleeping...")

        print("DB writer thread exiting.")
        connection.commit()
        connection.close()


def main():
    global threads_run
    global shared_list
    threads = []

    threads_run = True

    threads.append(Overseer(threads_run))
    threads.append(DBWriter())
    threads[0].start()
    threads[1].start()

    while threads_run:

        instr = ""
        while instr != "stop":
            instr = input("enter 'stop' to stop: ")

        threads_run = False

    print("Waiting for threads...")

    for thread in threads:
        thread.join()


main()
