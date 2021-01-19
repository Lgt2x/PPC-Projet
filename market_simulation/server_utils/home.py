"""
Home process, used to simulate a house
"""

from sys import setrecursionlimit
from multiprocessing import Process, Barrier, Array
from random import randint, random

import sysv_ipc
from colorama import Fore, Style

setrecursionlimit(10 ** 6)  # Don't judge me okay
TYPES = {1: "Give", 2: "Sell", 3: "Both"}  # Defining household types


class Home(Process):
    """
    Home class, instantiated by a city, which simulates a home
    consuming electricity following a specific behavior
    """

    def __init__(
        self,
        house_type: int,
        ipc_key: int,
        home_barrier: Barrier,
        weather_shared: Array,
        average_conso: int,
        prod_average: int,
        pid: int,
    ):
        super().__init__()

        self.house_type = house_type
        self.weather_shared = weather_shared
        self.home_barrier = home_barrier
        self.base_production = prod_average
        self.production = prod_average  # initial conditions
        self.conso = average_conso  # initial conditions
        self.bill = 0

        self.market_mq = sysv_ipc.MessageQueue(ipc_key)
        self.home_pid = pid

    def run(self) -> None:
        """
        Run the exchange with the market, and catch the interruption
        """
        try:
            self.transaction()
        except KeyboardInterrupt:
            print(f"Killing softly the house process {self.home_pid}\n", end="")

    def transaction(self) -> None:
        """
        Used in every exchange between the house and the market
        Computes the production and consumption of the house
        """

        # Home inhabitants check local weather
        # which influences their decisions on whether or not
        # they'll use electric heating or not (which is a major energy sink)
        with self.weather_shared.get_lock():
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]

        self.conso = Home.get_cons(temperature)

        # Random consumption based on the base value

        # Add the cloud coverage factor, diminishing the production
        if 0 <= cloud_coverage <= 70:
            # compute the solar production of each house with a small random factor
            self.production = (
                self.base_production + 10 * 1 / cloud_coverage + 2 * random()
            )
        elif cloud_coverage > 90 or temperature > 35:
            self.production = 0

        # Compute the energy situation of the house
        total = self.conso - self.production

        # Depending on their type, houses might :
        # `1` : give away the surplus of production
        # `2` : sell it to the market
        # `3` : sell it if no takers
        message = str(self.house_type) + ";" + str(total)
        self.market_mq.send(message.encode(), type=self.home_pid)

        # Get the bill from the market
        self.bill = float(
            self.market_mq.receive(type=self.home_pid + 10 ** 6)[0].decode()
        )
        color = Fore.RED if self.bill > 0 else Fore.GREEN
        color_bill = Fore.RED if total > 0 else Fore.GREEN

        print(
            f"Updated home {self.home_pid} \t── Type : {Home.get_type(self.house_type)} "
            f"\t── Bill : {color} {'{:.2f}'.format(self.bill)} "
            f"€{Style.RESET_ALL} ── "
            f"Consumed : {color_bill}{'{:.2f}'.format(total)} kWh{Style.RESET_ALL}\n",
            end="",
        )

        self.bill = 0  # after the turn the bill is reinitialized

        # All done, now wait the barrier
        self.home_barrier.wait()
        # And update again
        self.run()

    @staticmethod
    def get_cons(temp: int) -> int:
        """
        Works out the home energy consumption, taking weather into account
        :param temp: the temperature of the day
        :return: the daily energy consumption in kWh
        """

        cons = 70 + randint(-5, 5)  # Random small variations
        if temp <= 0:  # Heating
            cons += 15
        if temp >= 32:  # Air Conditionner
            cons += 10

        return cons

    @staticmethod
    def get_type(behaviour_id: int) -> str:
        """
        Returns the name of the type of the house considered for display purposes
        :param behaviour_id: int
        :return: str
        """
        return TYPES[behaviour_id]

    def kill(self) -> None:
        """
        Kills softly the process
        """
        print(f"{Fore.RED}Stopping house {self.home_pid} {Style.RESET_ALL}")
        super().kill()
