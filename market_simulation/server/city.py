"""
City object, to simulate a bunch of houses consuming electricity
"""
from multiprocessing import Process
from multiprocessing.dummy import Barrier
from random import randint

import sysv_ipc
import os

from market_simulation.server.ServerProcess import ServerProcess
from market_simulation.server.home import Home


class City(ServerProcess):
    """
    City object, used to simulate a group of electricity-consuming houses
    """

    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, ipc_key_houses, nb_houses, average_conso, max_prod):
        super(City, self).__init__(compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex,
                                   weather_shared, ipc_key)

        self.nb_houses = nb_houses

    def run(self):
        print("ok city", self.nb_houses)
        
    def start(self) -> None:
        super(City, self).start()

        for home in self.homes:
            home.start()
