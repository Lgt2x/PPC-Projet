"""
Server class for the market simulation
Configured by a json file
"""
import signal
import sys
from multiprocessing import Array, Barrier, Value
import json
import os
from time import sleep

import sysv_ipc

from server.sync import ServerSync
from server.market import Market
from server.city import City
from server.weather import Weather


class Server:
    """
    Server class, used to communicate with the user
    through the client and launch and set the 3 main processes City,
    Market, and Weather
    """

    def __init__(self, config_file: str):
        with open(config_file) as file:
            # Load the json configuration file
            json_config = json.load(file)

            # Create the different IPC message queues we will be using
            self.client_mq = self.create_ipc(json_config["server"]["ipc_key_client"])
            self.house_mq = self.create_ipc(json_config["server"]["ipc_key_house"])
            self.processes_mq = self.create_ipc(
                json_config["server"]["ipc_key_processes"]
            )

            # Create a barrier for synchronization
            # 4 processes need to be synchronized : Weather, City, Market and Server Sync
            # If the server if configured as "auto", it runs on regular interval.
            # If it's not, run when requested by the client
            self.compute_barrier = Barrier(parties=4)

            # This other barrier is used to update shared memory used for the next iteration
            # of the simulation
            self.write_barrier = Barrier(parties=4)

            # Shared memory for the weather
            self.weather_shared = Array("i", 2)

            # Shared memory for the energy price
            self.price_shared = Value("d")

            # Declaring the simulation processes
            self.city = City(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                ipc_key_houses=json_config["server"]["ipc_key_house"],
                nb_houses=json_config["cities"]["nb_houses"],
                average_conso=json_config["cities"]["average_conso"],
                max_prod=json_config["cities"]["max_prod"],
                ipc_message_type=1,
            )

            self.market = Market(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                politics=json_config["market"]["political_score"],
                economy=json_config["market"]["economy_score"],
                nb_houses=json_config["cities"]["nb_houses"],
                ipc_house=json_config["server"]["ipc_key_house"],
                ipc_message_type=2,
            )

            self.weather = Weather(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                temperature=json_config["weather"]["temperature"],
                cloud_coverage=json_config["weather"]["cloud_coverage"],
                ipc_message_type=3,
            )

        self.sync = ServerSync(
            compute_barrier=self.compute_barrier,
            write_barrier=self.write_barrier,
            price_shared=self.price_shared,
            weather_shared=self.weather_shared,
            ipc_key=json_config["server"]["ipc_key_processes"],
            mode=json_config["server"]["sync"]["auto"],
            time_interval=json_config["server"]["sync"]["time_interval"],
            ipc_message_type=4,
        )

        # Starting all processes
        self.city.start()
        self.weather.start()
        self.market.start()
        self.sync.start()

        signal.signal(signal.SIGINT, self.signal_handler)

        print("Initialization complete")

    def signal_handler(self, _, _2):
        self.stop()

    def process(self, message: str) -> int:
        """
        Processes the message
        :param message: a string
        :return:
        """
        if not message:
            return 0

        message = message[0].decode()

        if message == "end":
            return self.stop()

        return self.error()

    def receive(self):
        """
        Receives a message from the ipc client
        :return:
        """
        sleep(0.1)
        try:
            message = self.client_mq.receive(type=1, block=False)
        except sysv_ipc.BusyError:
            message = None

        return message

    def error(self) -> int:
        """
        Error handling, when the server doesn't recognizes the request
        :return: 1
        """
        print("Couldn't parse client request")
        self.client_mq.send("-1".encode(), type=2)
        return 1

    def stop(self) -> int:
        """
        Terminates the server process
        Deletes message queue, and ends processes
        """

        print("\n***** Begin stop process")
        # Send a zero (termination) code to the client
        message = "0".encode()
        self.client_mq.send(message=message, type=2)

        # Killing all processes
        self.sync.kill()
        self.market.kill()
        self.weather.kill()
        for home in self.city.homes:
            home.kill()
        self.city.kill()

        print("All processes stopped")

        return -1

    @staticmethod
    def create_ipc(ipc_key: int) -> sysv_ipc.MessageQueue:
        """
        Create an IPC message queue given an ID.
        If it already exists, remove it using the os primitive and create if again
        :param ipc_key: the IPC Message Queue key id
        :return: the MessageQueue Object
        """
        try:
            message_queue = sysv_ipc.MessageQueue(ipc_key, sysv_ipc.IPC_CREX)
        except sysv_ipc.ExistentialError:
            print(f"Message queue {ipc_key} already exists, recreating it.")
            os.system(f"ipcrm -Q {hex(ipc_key)}")
            message_queue = sysv_ipc.MessageQueue(ipc_key, sysv_ipc.IPC_CREX)

        return message_queue


""" Main server program loop
    Takes a json config file as an argument,
    and runs until the clients asks the process to end
"""
if __name__ == "__main__":
    if len(sys.argv) == 2:
        server = Server(sys.argv[1])
    else:
        print("Usage : python server.py <config_file>")
        sys.exit(1)

    while response := server.process(server.receive()) != -1:
        # print(response)
        pass

    print("Stopping server, bye :)")
    sys.exit(0)
