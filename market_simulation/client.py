"""
Simulation client, used to give orders to the server
"""
import sys
import sysv_ipc


class Client:
    """
    Client class, used to communicate to the server using an IPC message queue
    """

    def __init__(self, key: int):
        try:
            self.message_queue = sysv_ipc.MessageQueue(key)
        except sysv_ipc.ExistentialError:
            print(f"Cannot connect to message queue {key}, terminating.")
            sys.exit(1)

        print('Connection established. Enter "end" to end the simulation')

    def process(self, message: str) -> int:
        """
        sends a message to the server and wait for it to respond
        :param message: a string message
        :return: 0 to end, -1 for an error, 1 if ok
        """
        message = message.encode()

        # Send the message
        self.message_queue.send(message=message, type=1)

        # Wait for a response
        server_response, _ = self.message_queue.receive(type=2)
        return int(server_response)


"""
    Main client loop
    takes an only argument, the ipc key id to communicate with the server
"""
if __name__ == "__main__":
    IPC_KEY = 128

    if len(sys.argv) == 2:
        IPC_KEY = int(sys.argv[1])

    client = Client(IPC_KEY)

    # Stops when response = 0
    while response := client.process(input(" > ")):
        print(
            "Request processed"
            if response == 1
            else "Server could not interpret the response"
        )

    client.message_queue.remove()
    print("client stopped")
