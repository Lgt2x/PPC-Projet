"""
Contains Politics class, which simulates political events happening
"""
import os
from multiprocessing import Process
from random import random
from time import sleep


class ExternalFactor(Process):
    """
    Simulates political events, sending signal to the market randomly
    """

    def __init__(self, ppid: int, name: str, signal_code: int, delay: int):
        super(ExternalFactor, self).__init__()
        self.ppid = ppid
        self.name = name
        self.signal_code = signal_code
        self.delay = delay

    def run(self) -> None:
        """
        Loops infinitely and sends signals to parent process
        """
        while True:
            self.signal(randint(1, 4))

    def signal(self, time: float) -> None:
        """
        Sends a signal to the market (parent) process,
        after sleeping specified time
        :param time: time to sleep in seconds before sending the signal
        :return:
        """
        try:
            sleep(time)
        except KeyboardInterrupt:
            print(f"Killing softly {self.name}\n", end="")

        os.kill(int(self.ppid), self.signal_code)
