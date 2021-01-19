"""
Weather simulation, which communicates information
to the server_utils through a shared memory
"""
from random import randint

from colorama import Fore, Style

from .serverprocess import ServerProcess


class Weather(ServerProcess):
    """
    Object used to update the weather of the simulation
    weather_shared array : weather_shared[0] -> temperature ; weather_shared[1] -> cloud_coverage
    """

    def write(self):
        """
        Update weather conditions
        """
        with self.shared_variables.weather_shared.get_lock():
            self.shared_variables.weather_shared[0] += randint(-5, 5)  # Temperature
            self.shared_variables.weather_shared[0] = max(
                min(40, self.shared_variables.weather_shared[0]), -15
            )  # Stays in the interval [-15, 40]
            self.shared_variables.weather_shared[1] = randint(1, 100)  # Cloud coverage
            print(
                f"{Fore.YELLOW}Weather for next turn : {self.shared_variables.weather_shared[0]}°C, "
                f"Cloud coverage {self.shared_variables.weather_shared[1]}%{Style.RESET_ALL}\n"
            )

    def kill(self) -> None:
        """
        Kills softly the process
        """
        print(f"{Fore.RED}Stopping weather{Style.RESET_ALL}")
        super().kill()
