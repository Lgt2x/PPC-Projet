"""
City object, to simulate a bunch of houses consuming electricity
"""
from multiprocessing import Barrier, Value
from random import randint, random

from colorama import Fore, Style, Back

from .ServerProcess import ServerProcess
from .home import Home


class City(ServerProcess):
    """
    City object, used to simulate a group of electricity-consuming houses
    """

    def __init__(
        self,
        compute_barrier: Barrier,
        write_barrier: Barrier,
        price_shared: Value,
        weather_shared: Value,
        ipc_key: int,
        ipc_key_houses: int,
        nb_houses: int,
        average_conso: int,
        max_prod: int,
        ipc_message_type: int,
    ):
        super(City, self).__init__(
            compute_barrier,
            write_barrier,
            price_shared,
            weather_shared,
            ipc_key,
            ipc_message_type,
        )

        self.nb_houses = nb_houses

        # once all the houses has called the barrier, we just need the city's call
        self.barrier = Barrier(self.nb_houses + 1)

        self.homes = [
            Home(
                house_type=randint(1, 3),  # type of house
                ipc_key=ipc_key_houses,
                home_barrier=self.barrier,
                weather_shared=weather_shared,
                average_conso=average_conso,
                prod_average=int(max_prod * random()),
                pid=i + 1,  # can't be null
            )
            for i in range(self.nb_houses)
        ]

        print(
            f"\nStarting city with {Fore.BLACK}{Back.WHITE}{self.nb_houses}{Style.RESET_ALL} houses"
        )
        for home in self.homes:
            home.start()

    def update(self):
        self.barrier.wait()

    def kill(self) -> None:
        print(f"{Fore.RED}Stopping city{Style.RESET_ALL}")
        super(City, self).kill()
