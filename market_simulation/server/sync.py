"""
Defines the class used for server sync
"""

from time import sleep
from sysv_ipc import MessageQueue

from market_simulation.server.ServerProcess import ServerProcess


class ServerSync(ServerProcess):
    """
    Class used for server synchronization
    2 modes supported : auto for auto run (time interval)
    and manual, waiting for the user to manually advance in time
    """

    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, mode, time_interval):
        super(ServerSync, self).__init__(compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex,
                                   weather_shared, ipc_key)
        self.mode = mode
        self.ipc_key = ipc_key
        self.time_interval = time_interval
        self.message_queue = MessageQueue(ipc_key)

        self.turn = 0

    def update(self):
        """
        Used to sunc every other subprocess, waiting the barrier
        when timer expired OR when received the instruction to do so
        """
        self.write_barrier.reset()

        if self.mode:  # auto
            sleep(self.time_interval)
        else:  # Manual
            self.message_queue.receive()

        print("timer expired")

    def write(self):
        self.compute_barrier.reset()
        print(f"***** Turn {self.turn} ended, begin turn {self.turn+1}*****\n")
