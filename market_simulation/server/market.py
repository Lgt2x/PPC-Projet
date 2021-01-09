"""
Market process, simulating the electricity market,
reacting to external factors
"""
import concurrent.futures
from multiprocessing import Lock
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
        self.nb_houses = nb_houses

        self.mq_house = MessageQueue(ipc_house)

        self.consumption_lock = Lock()
        self.consumption = 0

        self.surplus_lock = Lock()
        self.surplus = 0
        self.workers = 5

        # Coefficients for energy price
        self.gamma = 0.98
        self.alpha = [0.1, 0.1, 0.1]
        self.beta = [0.1, 0.1, 0.1]

    def transaction(self, message, house):
        """
        Perform a transaction asynchronously with a house
        :param message: the ipc queue raw message received
        :param house: the pid of the house process
        """
        behaviour, consumption = map(float, message.decode().split(";"))
        behaviour = int(behaviour)

        # Send back the bill price, which is :
        #   - Positive if the total consumption is greater than 0,
        #   - Null if the house gives away its surplus energy and has consumption < 0
        #   - Negative if the house sells its surplus energy and has consumption < 0

        with self.price_mutex:
            price_kwh = self.price_shared.value

        if consumption > 0:  # If production < consumption
            with self.surplus_lock:  # Use the surplus given for free by other houses
                if self.surplus > consumption:  # The surplus can cover all consumption
                    self.surplus -= consumption
                    bill = 0
                else:  # The surplus can't cover all consumption
                    bill = price_kwh * (consumption - self.surplus)
                    self.surplus = 0
                print(f"House {house} payed ${bill}. Surplus is now ${self.surplus}")
                print("")
        else:  # If production > consumption
            if behaviour == 1:  # Gives away prudiction
                with self.surplus_lock:
                    self.surplus -= consumption  # consumption is negative
                bill = 0
                print(f"House {house} gave ${-consumption}. Surplus is now ${self.surplus}")
            else:  # The house sells its excess production
                bill = price_kwh * consumption  # Bill < 0
                print(f"House {house} gave ${-consumption}. Surplus is now ${self.surplus}")

        # Send back the bill price to the house
        self.mq_house.send(str(bill).encode(), type=house+10**6)

        # Increase the daily energy consumption
        with self.consumption_lock:
            self.consumption += consumption

    def update(self):
        # Characteristics change with a probability of 0.2
        self.economy = self.economy ^ (random() > 0.8)
        self.politics = self.economy ^ (random() > 0.8)
        self.speculation = self.speculation ^ (random() > 0.8)

        # Wait for each home to report usage
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for _ in range(self.nb_houses):
                message, house = self.mq_house.receive()
                pool.submit(self.transaction, message, house)

        print("out of it !")

    def write(self):
        # Get the weather conditions
        with self.weather_mutex:
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]

        # Update the price
        self.consumption_lock.acquire()
        with self.price_mutex:
            self.price_shared.value = self.gamma * self.price_shared.value \
                                + self.alpha[0] * temperature \
                                + self.alpha[1] * cloud_coverage \
                                + self.alpha[2] * self.consumption \
                                + self.beta[0] * (1 if self.politics else 0) \
                                + self.beta[1] * (1 if self.economy else 0) \
                                + self.beta[2] * (1 if self.speculation else 0)
            print(f"New prize is {self.price_shared.value}")
        self.consumption_lock.release()
