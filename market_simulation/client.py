"""
Simulation client, used to give orders to the server_utils
"""
import sys
import sysv_ipc


class Client:
    """
    Client class, used to communicate to the server_utils using an IPC message queue
    """

    def __init__(self, key: int):
        try:
            self.message_queue = sysv_ipc.MessageQueue(key)
        except sysv_ipc.ExistentialError:
            print(f"Cannot connect to message queue {key}, terminating.")
            sys.exit(1)

        print(
            'Connection established. Enter "report" to see the current state of the simulation,'
            'or "end" to end the simulation'
        )

    def send_mq(self, message: str) -> str:
        """
        sends a message to the server_utils and wait for it to respond
        :param message: a string message
        :return: the message sent back by the server
        """
        message = message.encode()

        # Send the message
        self.message_queue.send(message=message, type=1)

        # Wait for a response
        server_response, _ = self.message_queue.receive(type=2)
        return server_response.decode()

    @staticmethod
    def process(message: str) -> str:
        """
        Process the message received by the server
        """
        if message == "end":
            return "Server terminated, deleting the message queue"
        if message == "error":
            return "Server couldn't process the request"

        # Explicit format for server reports
        # "price;temp;coverage"
        price, temp, coverage = message.split(";")
        return f"Price of kWh : {price}€/kWh ── Temperature : {temp}°C ── Cloud coverage : {coverage}%"


# Main client loop*
# takes an only argument, the ipc key id to communicate with the server_utils
if __name__ == "__main__":
    IPC_KEY = 128

    if len(sys.argv) == 2:
        IPC_KEY = int(sys.argv[1])

    client = Client(IPC_KEY)

    # Stops when response = "end"
    while (response := client.send_mq(input(" > "))) != "end":
        print(" >", Client.process(response))

    client.message_queue.remove()
    print("client stopped")
