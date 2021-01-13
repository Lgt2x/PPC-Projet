"""
Defines the class used for server sync
"""
from multiprocessing import Barrier, Value
from time import sleep

from sysv_ipc import MessageQueue

from .ServerProcess import ServerProcess


class ServerSync(ServerProcess):
    """
    Class used for server synchronization
    2 modes supported : auto for auto run (time interval)
    and manual, waiting for the user to manually advance in time
    """

    def __init__(
        self,
        compute_barrier: Barrier,
        write_barrier: Barrier,
        price_shared: Value,
        weather_shared: Value,
        ipc_key: int,
        mode: str,
        time_interval: int,
        ipc_message_type: int,
    ):
        super(ServerSync, self).__init__(
            compute_barrier,
            write_barrier,
            price_shared,
            weather_shared,
            ipc_key,
            ipc_message_type,
        )
        self.mode = mode
        self.ipc_key = ipc_key
        self.time_interval = time_interval
        self.message_queue = MessageQueue(ipc_key)

        self.turn = 0

    def update(self):
        """
        Used to sync every other subprocess, waiting the barrier
        when timer expired OR when received the instruction to do so
        """
        print(f"\n\n***** Turn {self.turn} ended, begin turn {self.turn + 1} *****")

    def write(self):
        print(f"\n***** Write phase begin for turn {self.turn} *****")
        self.turn += 1

        if self.mode:  # auto
            sleep(self.time_interval)
        else:  # Manual : not implemented
            self.message_queue.receive()

        print("Timer expired, begin next turn")

    def kill(self) -> None:
        print("Stopping sync")
        super(ServerSync, self).kill()
