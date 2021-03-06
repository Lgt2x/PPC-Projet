"""
City object, to simulate a bunch of houses consuming electricity
"""
from multiprocessing import Barrier
from random import randint, random

from colorama import Fore, Style, Back

from .serverprocess import ServerProcess
from .home import Home
from .sharedvars import SharedVariables


class City(ServerProcess):
    """
    City object, used to simulate a group of electricity-consuming houses
    Basically creates a bunch of home processes
    """

    def __init__(
        self,
        shared_variables: SharedVariables,
        ipc_key_houses: int,
        nb_houses: int,
        average_conso: int,
        max_prod: int,
    ):
        super().__init__(shared_variables)
        self.nb_houses = nb_houses

        # once all the houses has called the barrier, we just need the city's call
        self.home_barrier = Barrier(self.nb_houses + 1)

        self.homes = [
            Home(
                house_type=randint(1, 3),  # type of house
                ipc_key=ipc_key_houses,
                home_barrier=self.home_barrier,
                weather_shared=shared_variables.weather_shared,
                average_conso=average_conso,
                prod_average=int(max_prod * random()),
                pid=home_pid + 1,  # can't be null
            )
            for home_pid in range(self.nb_houses)
        ]

        print(
            f"\nStarting city with {Fore.BLACK}{Back.WHITE}{self.nb_houses}{Style.RESET_ALL} houses"
        )
        for home in self.homes:
            home.start()

    def update(self):
        """
        For the update phase, the city
        """
        self.home_barrier.wait()

    def kill(self) -> None:
        """
        Kills softly the process
        """
        print(f"{Fore.RED}Stopping city{Style.RESET_ALL}")
        super().kill()
