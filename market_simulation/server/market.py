"""
Market process, simulating the electricity market,
reacting to external factors
"""
from random import random

from sysv_ipc import MessageQueue

from .ServerProcess import ServerProcess


class Market(ServerProcess):
    """
    Instantiated by the server, this class simulates the electricity market
    """

    def __init__(self, compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex, weather_shared,
                 ipc_key, politics, economy, speculation, nb_houses, ipc_house):
        super(Market, self).__init__(compute_barrier, write_barrier, price_shared, price_mutex, weather_mutex,
                                     weather_shared, ipc_key)

        self.politics = politics
        self.economy = economy
        self.speculation = speculation

    def update(self):
        # Characteristics change with a probability of 0.2
        self.economy = self.economy ^ (random() > 0.8)
        self.politics = self.economy ^ (random() > 0.8)
        self.speculation = self.speculation ^ (random() > 0.8)

        # Wait for each home to report usage
        # TODO : multithread that
        for _ in range(self.nb_houses):
            consumption, house = self.mq_house.receive()
            with self.price_mutex:
                self.mq_house.send(str(self.price_shared).encode())

            self.consumption += consumption

    def write(self):
        # Get the weather conditions
        with self.weather_mutex:
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]

        # Update the price
        with self.price_mutex:
            self.price_shared.value = self.gamma * self.price_shared.value \
                                + self.alpha[0] * temperature \
                                + self.alpha[1] * cloud_coverage \
                                + self.alpha[2] * self.consumption \
                                + self.beta[0] * (1 if self.politics else 0) \
                                + self.beta[1] * (1 if self.economy else 0) \
                                + self.beta[2] * (1 if self.speculation else 0)
