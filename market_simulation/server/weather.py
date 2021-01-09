"""
Weather simulation, which communicates information
to the server through a shared memory
"""
from random import randint

from .ServerProcess import ServerProcess


class Weather(ServerProcess):
    """
    Object used to update the weather of the simulation
    weather_shared array : weather_shared[0] -> temperature ; weather_shared[1] -> cloud_coverage
    """
    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, temperature, cloud_coverage):
        super(Weather, self).__init__(compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex,
                                      weather_shared, ipc_key)

    def write(self):
        """
        Update weather conditions
        """
        with self.weather_mutex:
            self.weather_shared[0] += randint(-5, 5)  # Temperature
            self.weather_shared[1] = randint(0, 100)  # Cloud coverage

        print(f"Weather for next turn : ")
