"""
Defines abstract class from which every server class derives
"""
from multiprocessing import Process
from sysv_ipc import MessageQueue


class ServerProcess(Process):
    """
    Abstract class used to define the common behavior between server subprocess
    """

    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, *args, **kwargs):
        super(ServerProcess, self).__init__()

        self.compute_barrier = compute_barrier
        self.write_barrier = write_barrier

        self.price_shared = price_shared
        self.price_mutex = price_mutex
        self.weather_shared = weather_shared
        self.weather_mutex = weather_mutex

        self.server_mq = MessageQueue(ipc_key)

    def run(self):
        """
        Method called when the process starts
        Calls compute and write barriers
        """

        # Wait for every simulation object to call the compute barrier
        self.compute_barrier.wait()
        self.update()

        # Wait for every simulation object to call the write barrier
        self.write_barrier.wait()
        self.write()

        # Then runs again
        self.run()

    def update(self):
        """
        Updates attributes to reflect changes in the simulation
        Overridden in sub-class
        """
        pass

    def write(self):
        """
        Writes attributes to the shared memory segments
        Overridden in sub-class
        """
        pass
