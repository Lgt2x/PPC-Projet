"""
Defines the class used for server_utils sync
"""
from multiprocessing import Barrier, Value
from time import sleep

from colorama import Back, Fore, Style

from .serverprocess import ServerProcess


class ServerSync(ServerProcess):
    """
    Class used for server_utils synchronization
    2 modes supported : auto for auto run (time interval)
    and manual, waiting for the user to manually advance in time
    """

    def __init__(
        self,
        compute_barrier: Barrier,
        write_barrier: Barrier,
        price_shared: Value,
        weather_shared: Value,
        time_interval: int,
    ):
        super().__init__(
            compute_barrier, write_barrier, price_shared, weather_shared,
        )

        self.time_interval = time_interval
        self.turn = 0

    def update(self):
        """
        Used to sync every other subprocess, waiting the barrier
        when timer expired OR when received the instruction to do so
        """
        print(
            f"\n\n{Back.LIGHTBLUE_EX}{Fore.BLACK}***** Turn {self.turn} ended, "
            f"begin turn {self.turn + 1} *****{Style.RESET_ALL}"
        )

    def write(self):
        """
        Used to begin the next turn once all houses have finished their exchanges
        """
        self.turn += 1
        sleep(self.time_interval)
        print("Timer expired, begin next turn")

    def kill(self) -> None:
        """
        Kills softly the process
        """
        print(f"{Fore.RED}Stopping sync{Style.RESET_ALL}")
        super().kill()
