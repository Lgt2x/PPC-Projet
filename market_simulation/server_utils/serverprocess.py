"""
Defines abstract class from which every server_utils class derives
"""
from multiprocessing import Process
from .sharedvars import SharedVariables


class ServerProcess(Process):
    """
    Abstract class used to define the common behavior between server_utils subprocess
    """

    def __init__(self, shared_variables: SharedVariables):
        super().__init__()
        self.shared_variables = shared_variables

    def run(self):
        """
        Method called when the process starts
        Calls compute and write barriers
        """

        try:
            # Wait for every simulation object to call the compute barrier
            self.update()
            self.shared_variables.compute_barrier.wait()

            # Wait for every simulation object to call the write barrier
            self.write()
            self.shared_variables.write_barrier.wait()

            # Then runs again
            self.run()
        except KeyboardInterrupt:
            print(
                "Process received interruption signal, killing softly the process\n",
                end="",
            )

    def update(self) -> None:
        """
        Updates attributes to reflect changes in the simulation
        Overridden in sub-class
        """

    def write(self) -> None:
        """
        Writes attributes to the shared memory segments
        Overridden in sub-class
        """
