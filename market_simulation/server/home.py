"""
Home process, used to simulate a house
"""
import os

import sysv_ipc
from multiprocessing import Process

from random import randint


class Home(Process):
    """
    Home class, instantiated by a city, which simulates a home
    consuming electricity following a specific behavior
    """
    def __init__(self, house_type, ipc_key, compute_barrier, weather_shared, weather_mutex,
                 average_conso, max_prod):
        super(Home, self).__init__()

        self.house_type = house_type
        self.weather_shared = weather_shared
        self.weather_mutex = weather_mutex
        self.compute_barrier = compute_barrier
        self.production = max_prod/2  # initial conditions
        self.conso = average_conso  # initial conditions
        self.bill = 0

        self.market_mq = sysv_ipc.MessageQueue(ipc_key)
        self.home_pid = os.getpid()

    def update(self):

        # Home inhabitants check local weather
        # which influences their decisions on whether or not
        # they'll use electric heating or not (which is a major energy sink)
        with self.weather_mutex:
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]
        
        self.conso = Home.get_cons(temperature)

        # Random consumption based on the base value

        # Add the cloud coverage factor, diminishing the production
        # TODO : verify the formula ?
        if 0 <= cloud_coverage <= 60:
            self.production = self.production + 0.1*cloud_coverage
        elif cloud_coverage > 60 or temperature > 35:
            self.production = 0

        # Compute the energy situation of the house
        total = self.conso - self.production

        # Depending on their type, houses might :
        # `1` : give away the surplus of production
        # `2` : sell it to the market
        message = str(self.house_type) + ";" + str(total)
        self.market_mq.send(message.encode(), type=self.home_pid)

        # Get the bill from the market
        self.bill = self.market_mq.receive(type=self.home_pid)

        # All done, now wait the barrier
        self.compute_barrier.wait()

        # And update again
        self.update()

    @staticmethod
    def get_cons(temp):
        """
        Works out the home energy consumption, taking weather into account
        :param temp: the temperature of the day
        :return: the daily energy consumption in kWh
        """

        cons = 70 + randint(-5, 5)  # Random small variations
        if temp <= 0: # Heating
            cons += 15
        if temp >= 32: # Air Conditionner
            cons += 10

        return cons
