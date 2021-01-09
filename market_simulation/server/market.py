"""
Market process, simulating the electricity market,
reacting to external factors
"""
import concurrent.futures
import multiprocessing
import signal
from multiprocessing import Value

from sysv_ipc import MessageQueue

from .ServerProcess import ServerProcess
from .economics import Economics
from .politics import Politics


class Market(ServerProcess):
    """
    Instantiated by the server, this class simulates the electricity market
    """

    def __init__(self, compute_barrier: multiprocessing.Barrier,
                 write_barrier: multiprocessing.Barrier,
                 price_shared: multiprocessing.Value,
                 weather_shared: multiprocessing.Array,
                 ipc_key: int, politics: int, economy: int, speculation: int,
                 nb_houses: int, ipc_house: int):
        super(Market, self).__init__(compute_barrier, write_barrier, price_shared,
                                     weather_shared, ipc_key)

        self.politics = Value('i')
        with self.politics.get_lock():
            self.politics.value = politics

        self.economy = Value('i')
        with self.economy.get_lock():
            self.economy.value = economy

        # self.speculation = speculation
        self.nb_houses = nb_houses
        self.price_shared = price_shared

        self.mq_house = MessageQueue(ipc_house)

        self.consumption = Value('d')
        self.surplus = Value('d')

        # Set default values
        with self.consumption.get_lock():
            self.consumption.value = 0
        with self.surplus.get_lock():
            self.surplus.value = 0

        self.workers = 5

        # Coefficients for energy price
        self.gamma = 0.98
        self.alpha = [0.1, 0.1, 0.1]
        self.beta = [0.1, 0.1, 0.1]

        self.economics_process = Economics()
        self.politics_process = Politics()
        self.economics_process.start()
        self.politics_process.start()

        # Politics : score between 0 and 100.
        # SIGUSR1 : politics situation deteriorates
        # SIGUSR2 : economics situation deteriorates
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.signal_handler)

    def signal_handler(self, sig, _):
        """
        Decreases the economical or political score when a signal is sent
        :param sig: signal_type
        :param _:
        :return:
        """
        if sig == signal.SIGUSR1:
            with self.politics.get_lock():
                self.politics.value = max(0, self.politics.value-30)
                print("\n\nPolitics score goes down :" + str(self.politics.value) + "/100\n\n")

        elif sig == signal.SIGUSR2:
            with self.economy.get_lock():
                self.economy.value = max(0, self.economy.value-30)
                print("\n\nEconomy score goes down :" + str(self.economy.value) + "/100\n\n")

    def transaction(self, message: str, house: int):
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

        with self.price_shared.get_lock():
            price_kwh = self.price_shared.value

        if consumption > 0:  # If production < consumption
            with self.surplus.get_lock():  # Use the surplus given for free by other houses
                if self.surplus.value > consumption:  # The surplus can cover all consumption
                    self.surplus.value -= consumption
                    bill = 0
                else:  # The surplus can't cover all consumption
                    bill = price_kwh * (consumption - self.surplus.value)
                    self.surplus.value = 0
                print(f"House {house} payed ${bill}. Surplus is now ${self.surplus.value}")
        else:  # If production > consumption
            if behaviour == 1:  # Gives away prudiction
                with self.surplus.get_lock():
                    self.surplus.value -= consumption  # consumption is negative
                bill = 0
                print(f"House {house} gave ${-consumption}. Surplus is now ${self.surplus.value}")
            else:  # The house sells its excess production
                bill = price_kwh * consumption  # Bill < 0
                print(f"House {house} gave ${-consumption}. Surplus is now ${self.surplus.value}")

        # Send back the bill price to the house
        self.mq_house.send(str(bill).encode(), type=house + 10 ** 6)

        # Increase the daily energy consumption
        with self.consumption.get_lock():
            self.consumption.value += consumption

    def update(self) -> None:
        """
        Wait for each home to report usage
        Do it in a thread of a threadpool
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            for _ in range(self.nb_houses):
                message, house = self.mq_house.receive()
                pool.submit(self.transaction, message, house)

    def write(self) -> None:
        """
        Update the cost of a kWh after the turn is over
        """

        # Get the weather conditions
        with self.weather_shared.get_lock():
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]

        # Update the price
        self.consumption.get_lock().acquire()
        self.politics.get_lock().acquire()
        self.economy.get_lock().acquire()
        with self.price_shared.get_lock():
            self.price_shared.value = self.gamma * self.price_shared.value \
                                      + self.alpha[0] * temperature \
                                      + self.alpha[1] * cloud_coverage \
                                      + self.alpha[2] * self.consumption.value \
                                      + self.beta[0] * self.politics.value \
                                      + self.beta[1] * self.economy.value
            print(f"New prize is {self.price_shared.value}$/kWh")
        self.consumption.get_lock().release()
        self.politics.get_lock().release()
        self.economy.get_lock().release()

        # Politics and economy tension go down, score goes up, with a limit of 100
        with self.economy.get_lock():
            self.economy.value = min(100, self.economy.value + 10)
            print(f"Economy situation: {self.economy.value}/100")

        with self.politics.get_lock():
            self.politics.value = min(100, self.politics.value + 10)
            print(f"Politics situation: {self.politics.value}/100")
