"""
Defines abstract class from which every server class derives
"""
from multiprocessing import Process, Barrier, Value
from sysv_ipc import MessageQueue


class ServerProcess(Process):
    """
    Abstract class used to define the common behavior between server subprocess
    """

    def __init__(
        self,
        compute_barrier: Barrier,
        write_barrier: Barrier,
        price_shared: Value,
        weather_shared: Value,
        ipc_key: int,
    ):
        super(ServerProcess, self).__init__()

        self.compute_barrier = compute_barrier
        self.write_barrier = write_barrier

        self.price_shared = price_shared
        self.weather_shared = weather_shared

        self.server_mq = MessageQueue(ipc_key)

    def run(self):
        """
        Method called when the process starts
        Calls compute and write barriers
        """
        # Wait for every simulation object to call the compute barrier
        self.update()
        self.compute_barrier.wait()

        # Wait for every simulation object to call the write barrier
        self.write()
        self.write_barrier.wait()

        # Then runs again
        self.run()

    def update(self):
        """
        Updates attributes to reflect changes in the simulation
        Overridden in sub-class
        """

    def write(self):
        """
        Writes attributes to the shared memory segments
        Overridden in sub-class
        """
