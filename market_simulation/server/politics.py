"""
Contains Politics class, which simulates political events happening
"""
import os
import signal
from multiprocessing import Process
from random import randint
from time import sleep


class Politics(Process):
    """
    Simulates political events, sending signal to the market randomly
    """

    def __init__(self, ppid):
        super(Politics, self).__init__()
        self.ppid = ppid

    def run(self) -> None:
        """
        Loops infinitely and sends signals to parent process
        """
        while True:
            self.signal(randint(1, 4))

    def signal(self, time: int) -> None:
        """
        Sends a signal to the market (parent) process,
        after sleeping specified time
        :param time: time to sleep in seconds before sending the signal
        :return:
        """
        sleep(time)
        os.kill(int(self.ppid), signal.SIGUSR1)
