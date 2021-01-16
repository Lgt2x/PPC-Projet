"""
Weather simulation, which communicates information
to the server through a shared memory
"""
from multiprocessing import Barrier, Value
from random import randint

from colorama import Fore, Style

from .ServerProcess import ServerProcess


class Weather(ServerProcess):
    """
    Object used to update the weather of the simulation
    weather_shared array : weather_shared[0] -> temperature ; weather_shared[1] -> cloud_coverage
    """

    def __init__(
        self,
        compute_barrier: Barrier,
        write_barrier: Barrier,
        price_shared: Value,
        weather_shared: Value,
        ipc_key: int,
        ipc_message_type: int,
    ):
        super(Weather, self).__init__(
            compute_barrier,
            write_barrier,
            price_shared,
            weather_shared,
            ipc_key,
            ipc_message_type,
        )

    def write(self):
        """
        Update weather conditions
        """
        with self.weather_shared.get_lock():
            self.weather_shared[0] += randint(-5, 5)  # Temperature
            self.weather_shared[0] = max(min(40, self.weather_shared[0]), -15)  # Stays in the interval [-15, 40]
            self.weather_shared[1] = randint(1, 100)  # Cloud coverage
            print(
                f"{Fore.YELLOW}Weather for next turn : {self.weather_shared[0]}°C, Cloud coverage {self.weather_shared[1]}%{Style.RESET_ALL}\n"
            )

    def kill(self) -> None:
        print(f"{Fore.RED}Stopping weather{Style.RESET_ALL}")
        super(Weather, self).kill()
