import sysv_ipc
import sys
from multiprocessing import Process
import json
import os

from server.market import Market
from server.city import City
from server.weather import Weather


class Server:
    """
    Server class, used to communicate with the user through the client and launch and set the 3 main processes City,
    Market, and Weather
    """

    def __init__(self, config_file):
        with open(config_file) as file:
            json_config = json.load(file)

            # Remove ipc queue

            try:
                self.message_queue = sysv_ipc.MessageQueue(json_config["ipc_key"], sysv_ipc.IPC_CREX)
            except sysv_ipc.ExistentialError:
                print(f"Message queue {json_config['ipc_key']} already exsits, recreating it.")
                os.system(f"ipcrm -Q {hex(json_config['ipc_key'])}")
                self.message_queue = sysv_ipc.MessageQueue(json_config["ipc_key"], sysv_ipc.IPC_CREX)


            self.city = Process(target=City, args=(json_config["nb_houses"],))
            self.market = Process(target=Market,
                                  args=(json_config["political"], json_config["economy"], json_config["speculation"]))
            self.weather = Process(target=Weather, args=(json_config["temperature"], json_config["cloud_coverage"]))

            self.city.start()
            self.weather.start()
            self.market.start()

            print("Initialization complete")

    def process(self, message):
        """
        Processes the message
        :param message: a string
        :return:
        """
        print(message)
        m, t = message
        m = m.decode()

        if m == "end":
            return self.terminate()
        else:
            return self.error()

    def receive(self):
        """
        Receives a message from the ipc client
        :return:
        """
        return self.message_queue.receive(type=1)

    def error(self):
        print("Couldn't parse client request")
        self.message_queue.send("-1".encode(), type=2)
        return 1

    def terminate(self):
        """
        Terminates the server process
        Deletes message queue, and ends processes
        """

        # Send a zero (termination) code to the client
        message = "0".encode()
        self.message_queue.send(message=message, type=2)

        # Message them to suicide
        self.city.join()
        self.weather.join()
        self.market.join()

        return 0


if __name__ == "__main__":
    if len(sys.argv) == 2:
        server = Server(sys.argv[1])
    else:
        print("Usage : python server.py <config_file>")
        sys.exit(1)

    # Stops when response = 0
    while response := server.process(server.receive()):
        print(response)

    print("Process stopped")
