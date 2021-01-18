"""
Generic external factor class, sending a signal to the market
"""
import os
from multiprocessing import Process
from random import random
from time import sleep


class ExternalFactor(Process):
    """
    Process that simulates an external event, such as politics or stock market
    It sends a given signal to the market process when the situation deteriorates,
    with a random waiting time
    """

    def __init__(self, ppid: int, name: str, signal_code: int, delay: int):
        super().__init__()
        self.ppid = ppid  # The market process id
        self.name = name  # Factor name
        self.signal_code = signal_code  # id of the signal to be sent
        self.delay = delay  # maximum time between two signals

    def run(self) -> None:
        """
        Loops infinitely and sends signals to parent process
        """
        while True:
            self.signal(random() * self.delay)

    def signal(self, time: float) -> None:
        """
        Sends a signal to the market (parent) process,
        after sleeping specified time
        :param time: time to sleep in seconds before sending the signal
        """
        try:
            sleep(time)
        except KeyboardInterrupt:  # Interrupt softly the process
            print(f"Killing softly {self.name}\n", end="")

        # Send signal
        os.kill(int(self.ppid), self.signal_code)
