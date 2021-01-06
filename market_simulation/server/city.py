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

    def __init__(self, compute_barrier, write_barrier, ipc_key_houses, nb_houses, weather_mutex,
                 weather_shared, average_conso, max_prod):
        super(City, self).__init__()

        self.nb_houses = nb_houses

    def run(self):
        print("ok city", self.nb_houses)
