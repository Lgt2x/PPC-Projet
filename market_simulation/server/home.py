"""
Home process, used to simulate a house
"""
import sysv_ipc
from multiprocessing import Process

from random import randint


class Home(Process):
    """
    Home class, instantiated by a city, which simulates a home
    consuming electricity following a specific behavior
    """
    def __init__(self, house_type, ipc_key, ipc_type, weather_shared, weather_mutex, compute_barrier, write_barrier, average_conso, max_prod):
        super().__init__()
        self.nb_houses = nb_houses
