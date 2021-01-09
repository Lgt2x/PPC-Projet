"""
City object, to simulate a bunch of houses consuming electricity
"""
from multiprocessing import Barrier
from random import randint

from .ServerProcess import ServerProcess
from .home import Home


class City(ServerProcess):
    """
    City object, used to simulate a group of electricity-consuming houses
    """

    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, ipc_key_houses, nb_houses, average_conso, max_prod):
        super(City, self).__init__(compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex,
                                   weather_shared, ipc_key)

        self.nb_houses = nb_houses

        # once all the houses has called the barrier, we just need the city's call
        self.barrier = Barrier(self.nb_houses)

        self.homes = [Home(
            house_type=randint(1, 2),  # type of house
            ipc_key=ipc_key_houses,
            compute_barrier=self.barrier,
            weather_shared=weather_shared,
            weather_mutex=weather_mutex,
            average_conso=average_conso,
            max_prod=max_prod,
            id=i + 1  # can't be null
        ) for i in range(self.nb_houses)]

        print(f"Starting city with {self.nb_houses} houses")
        for home in self.homes:
            home.start()

    def update(self):
        self.barrier.wait()

    def terminate(self):
        for home in self.homes:
            home.join()

        print("all house processes finished")
