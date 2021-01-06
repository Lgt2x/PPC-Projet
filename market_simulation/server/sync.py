"""
Defines the class used for server sync
"""

from multiprocessing import Process
from time import sleep
from sysv_ipc import MessageQueue


class ServerSync(Process):
    """
    Class used for server synchronization
    2 modes supported : auto for auto run (time interval)
    and manual, waiting for the user to manually advance in time
    """

    def __init__(self, barrier, mode, time_interval, ipc_key):
        super(ServerSync, self).__init__()
        self.barrier = barrier
        self.mode = mode
        self.ipc_key = ipc_key
        self.time_interval = time_interval
        self.message_queue = MessageQueue(ipc_key)

    def run(self):
        """
        Used to sunc every other subprocess, waiting the barrier
        when timer expired OR when received the instruction to do so
        """
        if self.mode:  # auto
            sleep(self.time_interval)
        else:  # Manual
            self.message_queue.receive()

        self.barrier.wait()
        self.run()
