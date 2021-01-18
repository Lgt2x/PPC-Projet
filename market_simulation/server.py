"""
Server class for the market simulation
Configured by a json file
"""
import sys
import signal
import json
from time import sleep
from multiprocessing import Array, Barrier, Value

import sysv_ipc
from colorama import Fore, Style, Back

from server_utils.sync import ServerSync
from server_utils.market import Market
from server_utils.city import City
from server_utils.weather import Weather


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
            self.client_mq = self.get_ipc_queue(json_config["server"]["ipc_key_client"])
            self.house_mq = self.get_ipc_queue(json_config["server"]["ipc_key_house"])

            # Create a barrier for synchronization
            # 4 processes need to be synchronized : Weather, City, Market and Server Sync
            # If the server_utils if configured as "auto", it runs on regular interval.
            # If it's not, run when requested by the client
            compute_barrier = Barrier(parties=4)

            # This other barrier is used to update shared memory used for the next iteration
            # of the simulation
            write_barrier = Barrier(parties=4)

            # Shared memory for the weather
            self.weather_shared = Array("i", 2)
            with self.weather_shared.get_lock():
                self.weather_shared[0] = json_config["weather"]["temperature"]
                self.weather_shared[1] = json_config["weather"]["cloud_coverage"]

            # Shared memory for the energy price
            self.price_shared = Value("d")
            with self.price_shared.get_lock():
                self.price_shared.value = json_config["market"]["initial_price"]

            # Declaring the simulation processes
            self.city = City(
                compute_barrier=compute_barrier,
                write_barrier=write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
                ipc_key_houses=json_config["server"]["ipc_key_house"],
                nb_houses=json_config["cities"]["nb_houses"],
                average_conso=json_config["cities"]["average_conso"],
                max_prod=json_config["cities"]["max_prod"],
            )

            self.market = Market(
                politics=json_config["market"]["political_score"],
                economy=json_config["market"]["economy_score"],
                nb_houses=json_config["cities"]["nb_houses"],
                ipc_house=json_config["server"]["ipc_key_house"],
                time_interval=json_config["server"]["time_interval"],
                compute_barrier=compute_barrier,
                write_barrier=write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
            )

            self.weather = Weather(
                compute_barrier=compute_barrier,
                write_barrier=write_barrier,
                price_shared=self.price_shared,
                weather_shared=self.weather_shared,
            )

        self.sync = ServerSync(
            compute_barrier=compute_barrier,
            write_barrier=write_barrier,
            price_shared=self.price_shared,
            weather_shared=self.weather_shared,
            time_interval=json_config["server"]["time_interval"],
        )

        # Starting all processes
        self.city.start()
        self.weather.start()
        self.market.start()
        self.sync.start()

        signal.signal(signal.SIGINT, self.signal_handler)

        print(f"{Fore.GREEN}Initialization complete{Style.RESET_ALL}")

    def signal_handler(self, _, _2):
        """
        Intercept the stop signal and shut down properly
        """
        self.stop()
        sys.exit(1)

    def receive(self) -> str:
        """
        Receives a message from the ipc client
        :return: the message if there is one, None otherwise
        """
        sleep(0.1)
        try:
            message = self.client_mq.receive(type=1, block=False)
        except sysv_ipc.BusyError:
            message = None

        return message

    def process(self, message: str) -> bool:
        """
        Processes the message
        :param message: a string
        :return: True if continue, False otherwise
        """
        if not message:
            return True  # Continue

        print(f"{Fore.LIGHTMAGENTA_EX}Received a message from client{Style.RESET_ALL}")
        message = message[0].decode()

        if message == "end":
            return self.stop()
        elif message == "report":
            return self.send_report()

        return self.error()

    def receive(self):
        """
        Receives a message from the ipc client
        :return: the message if there is one, None otherwise
        """
        message = []

        with self.price_shared.get_lock():
            message.append("{:.2f}".format(self.price_shared.value))

        with self.weather_shared.get_lock():
            message.extend(map(str, self.weather_shared))

        message_sent = ";".join(message).encode()
        self.client_mq.send(message_sent, type=2)

        print(f"{Fore.LIGHTMAGENTA_EX}Send report to client{Style.RESET_ALL}")

        return True

    def error(self) -> bool:
        """
        Error handling, when the server_utils doesn't recognizes the request
        :return: 1
        """
        print(f"{Fore.LIGHTMAGENTA_EX}Couldn't parse client request{Style.RESET_ALL}")
        self.client_mq.send("error".encode(), type=2)
        return True

    def stop(self) -> bool:
        """
        Terminates the server_utils process
        Deletes message queue, and ends processes
        """

        print(
            f"\n{Back.RED}{Fore.WHITE}***** Begin server_utils "
            f"stop process *****{Style.RESET_ALL}"
        )

        # Killing all processes
        self.sync.kill()
        self.market.kill()
        self.weather.kill()
        for home in self.city.homes:
            home.kill()
        self.city.kill()

        self.house_mq.remove()

        print(f"{Fore.LIGHTRED_EX}All processes stopped{Style.RESET_ALL}")

        # Send a zero (termination) code to the client
        message = "end".encode()
        self.client_mq.send(message=message, type=2)

        return False  # Continue

    @staticmethod
    def get_ipc_queue(ipc_key: int) -> sysv_ipc.MessageQueue:
        """
        Create an IPC message queue given an ID.
        If it already exists, remove it using the os primitive and create if again
        :param ipc_key: the IPC Message Queue key id
        :return: the MessageQueue Object
        """
        try:
            message_queue = sysv_ipc.MessageQueue(ipc_key, sysv_ipc.IPC_CREX)
        except sysv_ipc.ExistentialError:
            print(
                f"{Fore.BLUE}Message queue {ipc_key} already exists, recreating it.{Style.RESET_ALL}"
            )
            sysv_ipc.MessageQueue(ipc_key).remove()
            message_queue = sysv_ipc.MessageQueue(ipc_key, sysv_ipc.IPC_CREX)

        return message_queue


# Main server_utils program loop
# Takes a json config file as an argument,
# and runs until the clients asks the process to end
if __name__ == "__main__":
    if len(sys.argv) == 2:
        server = Server(sys.argv[1])
    else:
        print("Usage : python server_utils.py <config_file>")
        sys.exit(1)

    # When server is set up, listen for messages from the client
    while response := server.process(server.receive()):
        pass

    print(f"{Fore.LIGHTMAGENTA_EX}Stopping server_utils, bye :){Style.RESET_ALL}")
    sys.exit(0)
