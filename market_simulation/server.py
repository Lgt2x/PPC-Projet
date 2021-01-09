"""
Server class for the market simulation
Configured by a json file
"""

import sys
from multiprocessing import Process
import json
import os
import sysv_ipc

from market_simulation.server.sync import ServerSync
from server.market import Market
from server.city import City
from server.weather import Weather


class Server:
    """
    Server class, used to communicate with the user
    through the client and launch and set the 3 main processes City,
    Market, and Weather
    """

    def __init__(self, config_file):
        with open(config_file) as file:
            json_config = json.load(file)

            self.client_mq = self.create_ipc(json_config["server"]["ipc_key_client"])
            self.house_mq = self.create_ipc(json_config["server"]["ipc_key_house"])
            self.house_mq = self.create_ipc(json_config["server"]["ipc_key_processes"], )

            # Create a barrier for synchronization
            # 4 processes need to be synchronized : Weather, City, Market and Server Sync
            # If the server if configured as "auto", it runs on regular interval.
            # If it's not, run when requested by the client
            self.compute_barrier = Barrier(parties=4)

            # This other barrier is used to update shared memory used for the next iteration
            # of the simulation
            self.write_barrier = Barrier(parties=4)

            # Shared memory for the weather
            self.weather_mutex = Lock()
            self.weather_shared = Array('i', 2)

            # Shared memory for the energy price
            self.price_mutex = Lock()
            self.price_shared = Value('d')

            # Declaring the simulation processes

            self.city = City(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                price_mutex=self.price_mutex,
                weather_mutex=self.weather_mutex,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                ipc_key_houses=json_config["server"]["ipc_key_house"],
                nb_houses=json_config["cities"]["nb_houses"],
                average_conso=json_config["cities"]["average_conso"],
                max_prod=json_config["cities"]["max_prod"],
            )

            self.market = Market(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                price_mutex=self.price_mutex,
                weather_mutex=self.weather_mutex,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                politics=json_config["market"]["political"],
                economy=json_config["market"]["economy"],
                speculation=json_config["market"]["speculation"],
                nb_houses=json_config["cities"]["nb_houses"],
                ipc_house=json_config["server"]["ipc_key_house"]
            )

            self.weather = Weather(
                compute_barrier=self.compute_barrier,
                write_barrier=self.write_barrier,
                price_shared=self.price_shared,
                price_mutex=self.price_mutex,
                weather_mutex=self.weather_mutex,
                weather_shared=self.weather_shared,
                ipc_key=json_config["server"]["ipc_key_processes"],
                temperature=json_config["weather"]["temperature"],
                cloud_coverage=json_config["weather"]["cloud_coverage"],
            )

        self.sync = ServerSync(
            compute_barrier=self.compute_barrier,
            write_barrier=self.write_barrier,
            price_shared=self.price_shared,
            price_mutex=self.price_mutex,
            weather_mutex=self.weather_mutex,
            weather_shared=self.weather_shared,
            ipc_key=json_config["server"]["ipc_key_processes"],
            mode=json_config["server"]["sync"]["auto"],
            time_interval=json_config["server"]["sync"]["time_interval"],
        )

        # Starting all processes
        self.city.start()
        self.weather.start()
        self.market.start()
        self.sync.start()

        print("Initialization complete")

    def process(self, message):
        """
        Processes the message
        :param message: a string
        :return:
        """
        print(message)
        message = message[0].decode

        if message == "end":
            return self.terminate()
        return self.error()

    def receive(self):
        """
        Receives a message from the ipc client
        :return: 0 if end, something else if not
        """
        return self.client_mq.receive(type=1)

    def error(self):
        """
        Error handling, when the server doesn't recognizes the request
        :return: 1
        """
        print("Couldn't parse client request")
        self.client_mq.send("-1".encode(), type=2)
        return 1

    def terminate(self):
        """
        Terminates the server process
        Deletes message queue, and ends processes
        """

        # Send a zero (termination) code to the client
        message = "0".encode()
        self.client_mq.send(message=message, type=2)

        # Message them to suicide
        self.city.join()
        self.weather.join()
        self.market.join()

        return 0

    @staticmethod
    def create_ipc(ipc_key):
        """
        Create an IPC message queue given an ID.
        If it already exists, remove it using the os primitive and create if again
        :param ipc_key: the IPCMQ key id
        :return: the MessageQueue Object
        """
        try:
            message_queue = sysv_ipc.MessageQueue(
                ipc_key, sysv_ipc.IPC_CREX
            )
        except sysv_ipc.ExistentialError:
            print(
                f"Message queue {ipc_key} already exsits, recreating it."
            )
            os.system(f"ipcrm -Q {hex(ipc_key)}")
            message_queue = sysv_ipc.MessageQueue(
                ipc_key, sysv_ipc.IPC_CREX
            )

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

    # Stops when response = 0
    # while response := server.process(server.receive()):
    #     print(response)
