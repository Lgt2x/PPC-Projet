"""
Contains Politics class, which simulates political events happening
"""
import os
from multiprocessing import Process
import signal
from random import randint
from time import sleep


class Politics(Process):
    """
    Simulates political events, sending signal to the market randomly
    """
    def __init__(self):
        super(Politics, self).__init__()

    def run(self) -> None:
        """
        Loops infinitely and sends signals to parent process
        """
        while True:
            self.signal(randint(1, 4))

    @staticmethod
    def signal(time: int) -> None:
        """
        Sends a signal to the market (parent) process,
        after sleeping specified time
        :param time: time to sleep in seconds before sending the signal
        :return:
        """
        sleep(time)
        os.kill(int(os.getppid()), signal.SIGUSR1)
