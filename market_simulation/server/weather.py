"""
Weather simulation, which communicates information
to the server through a shared memory
"""
from multiprocessing import Barrier, Value
from random import randint

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
        temperature: int,
        cloud_coverage: int,
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
        with self.weather_shared.get_lock():
            self.weather_shared[0] = temperature
            self.weather_shared[1] = cloud_coverage

    def write(self):
        """
        Update weather conditions
        """
        with self.weather_shared.get_lock():
            self.weather_shared[0] += randint(-5, 5)  # Temperature
            self.weather_shared[1] = randint(0, 100)  # Cloud coverage
            print(
                f"Weather for next turn : {self.weather_shared[0]}°C, Cloud coverage {self.weather_shared[1]}%\n"
            )

    def kill(self) -> None:
        print("Stopping weather")
        super(Weather, self).kill()
