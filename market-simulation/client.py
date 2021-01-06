import sysv_ipc
import sys


class Client:
    """
    Client class, used to communicate to the server using an IPC message queue
    """

    def __init__(self, key):
        try:
            self.message_queue = sysv_ipc.MessageQueue(key)
        except sysv_ipc.ExistentialError:
            print(f"Cannot connect to message queue {key}, terminating.")
            sys.exit(1)

        print("Connection established. Enter \"begin\" to start the simulation")

    def process(self, message):
        """
        sends a message to the server and wait for it to respond
        :param message: a string message
        :return: 0 to end, -1 for an error, 1 if ok
        """
        message = message.encode()

        # Send the message
        self.message_queue.send(message=message, type=1)

        # Wait for a response
        a, t = self.message_queue.receive(type=2)
        return int(a)


if __name__ == "__main__":
    ipc_key = 128

    if len(sys.argv) == 2:
        ipc_key = int(sys.argv[1])

    client = Client(ipc_key)

    # Stops when response = 0
    while response := client.process(input(" > ")):
        print("Request processed" if response == 1 else "Server could not interpret the response")

    client.message_queue.remove()
    print("client stopped")
