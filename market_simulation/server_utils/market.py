"""
Market process, simulating the electricity market,
reacting to external factors
"""
import collections
import concurrent.futures
import multiprocessing
import os
import signal
from multiprocessing import Value

from colorama import Fore, Style
from sysv_ipc import MessageQueue

from .serverprocess import ServerProcess
from .externalfactor import ExternalFactor


class Market(ServerProcess):
    """
    Instantiated by the server_utils, this class simulates the electricity market
    """

    def __init__(
        self,
        compute_barrier: multiprocessing.Barrier,
        write_barrier: multiprocessing.Barrier,
        price_shared: multiprocessing.Value,
        weather_shared: multiprocessing.Array,
        politics: int,
        economy: int,
        nb_houses: int,
        ipc_house: int,
        time_interval: int,
    ):
        super().__init__(
            compute_barrier, write_barrier, price_shared, weather_shared,
        )

        # Political climate, rated from 0 to 100
        self.politics = Value("i")
        with self.politics.get_lock():
            self.politics.value = politics

        # Economics climate, rated from 0 to 100
        self.economy = Value("i")
        with self.economy.get_lock():
            self.economy.value = economy

        self.nb_houses = nb_houses  # Number of houses
        self.price_shared = price_shared  # Price of kWh
        self.mq_house = MessageQueue(
            ipc_house
        )  # Message queue to communicate with houses
        self.daily_consumption = Value(
            "d"
        )  # Total consumption of the houses on this day
        self.surplus = Value("d")  # Surplus of production
        self.waiting_houses = collections.deque()  # Free energy waiting queue
        self.waiting_lock = multiprocessing.Lock()  # Lock to access this queue

        # Set default values
        with self.daily_consumption.get_lock():
            self.daily_consumption.value = 0
        with self.surplus.get_lock():
            self.surplus.value = 0

        self.workers = 5

        # Coefficients for energy price
        self.gamma = 0.98
        self.alpha = [0.0001, 0.0001, 0.000001]
        self.beta = [0.025, 0.025, 0.025]

        # Politics : score between 0 and 100.
        # SIGUSR1 : politics situation deteriorates
        # SIGUSR2 : economics situation deteriorates
        self.market_pid = os.getpid()
        self.politics_process = ExternalFactor(
            ppid=self.market_pid,
            name="politics",
            signal_code=signal.SIGUSR1,
            delay=time_interval * 6,
        )
        self.economics_process = ExternalFactor(
            ppid=self.market_pid,
            name="economics",
            signal_code=signal.SIGUSR2,
            delay=time_interval * 7,
        )
        self.economics_process.start()
        self.politics_process.start()

        # Listen for signals
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.signal_handler)

    def signal_handler(self, sig, _):
        """
        Decreases the economical or political score when a signal is sent
        :param sig: signal_type
        :param _: ignored
        """
        if sig == signal.SIGUSR1:
            with self.politics.get_lock():
                self.politics.value = max(1, self.politics.value - 30)

        elif sig == signal.SIGUSR2:
            with self.economy.get_lock():
                self.economy.value = max(1, self.economy.value - 30)

    def transaction(self, message: str, house: int):
        """
        Performs a transaction asynchronously with a house
        :param message: the ipc queue raw message received
        :param house: the pid of the house process
        """
        behaviour, consumption = map(float, message.decode().split(";"))
        behaviour = int(behaviour)

        # Increase the daily energy sold and bought
        with self.daily_consumption.get_lock():
            self.daily_consumption.value += consumption

        # Send back the bill price, which is :
        #   - Positive if the total consumption is greater than 0 after free energy had been taken
        #   - Null if the house gives away its surplus energy and has consumption < 0
        #   - Negative if the house sells its surplus energy and has consumption < 0

        if consumption > 0:  # If production < consumption
            with self.surplus.get_lock():  # Use the surplus given for free by other houses
                if self.surplus.value >= consumption:
                    # The surplus can cover all consumption
                    self.surplus.value -= consumption
                    print(
                        f"House {house} took {'{:.2f}'.format(consumption)}kWh from surplus. "
                        f"Surplus is now {'{:.2f}'.format(self.surplus.value)}kWh\n",
                        end="",
                    )
                    consumption = 0
                else:  # The surplus can't cover all consumption
                    consumption -= self.surplus.value
                    print(
                        f"House {house} took {'{:.2f}'.format(self.surplus.value)}"
                        f"kWh from surplus, which is now null\n",
                        end="",
                    )
                    self.surplus.value = 0

            with self.waiting_lock:  # Use free givers if the house still has to pay
                while consumption > 0 and self.waiting_houses:  # While there is a giver
                    house_giving, surplus_house = self.waiting_houses.popleft()
                    if surplus_house >= consumption:
                        surplus_house -= (
                            consumption  # decrease the surplus of this house
                        )
                        print(
                            f"House {house} took {'{:.2f}'.format(consumption)} kWh from house {house_giving} "
                            f"surplus, which has now {'{:.2f}'.format(surplus_house)}kWh to give\n",
                            end="",
                        )
                        # and put it back in the first position of the queue
                        self.waiting_houses.appendleft((house_giving, surplus_house))
                        consumption = 0
                    else:  # All the surplus energy is consumed
                        print(
                            f"House {house} took all {'{:.2f}'.format(surplus_house)} "
                            f"kWh from house {house_giving}'s giveaway\n",
                            end="",
                        )
                        consumption -= surplus_house
                        # Tell the giver house its energy has been taken for free
                        self.mq_house.send("0".encode(), type=house_giving + 10 ** 6)

        else:  # If production > consumption
            if behaviour == 1:  # Gives away production
                with self.surplus.get_lock():
                    self.surplus.value -= consumption  # consumption is negative
                print(
                    f"House {house} gave away {'{:.2f}'.format(-consumption)}kWh, "
                    f"surplus is now {'{:.2f}'.format(self.surplus.value)}kWh\n",
                    end="",
                )
                consumption = 0
            elif behaviour == 2:  # The house sells its excess production
                print(
                    f"House {house} sold {'{:.2f}'.format(-consumption)}kWh.\n", end=""
                )
            elif (
                behaviour == 3
            ):  # Put energy on wait queue to give it later, and eventually sell it if no takers
                print(
                    f"Put {'{:.2f}'.format(-consumption)}kWh from house {house} on giveaway queue\n",
                    end="",
                )
                with self.waiting_lock:
                    self.waiting_houses.append((house, consumption))
                return  # Don't return the bill now, do it later

        # Get the current price
        with self.price_shared.get_lock():
            # Send back the bill price to the house
            self.mq_house.send(
                str(consumption * self.price_shared.value).encode(),
                type=house + 10 ** 6,
            )

    def update(self) -> None:
        """
        Wait for each home to report usage
        Do it in a thread of a thread pool
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            for _ in range(self.nb_houses):
                message, house = self.mq_house.receive()
                pool.submit(self.transaction, message, house)

        with self.price_shared.get_lock():
            price_kwh = self.price_shared.value

        # Type 3 houses (sell if no takers) if all the surplus isn't totally consumed
        while self.waiting_houses:
            house_giving, surplus_house = self.waiting_houses.popleft()
            bill = price_kwh * surplus_house
            self.mq_house.send(str(bill).encode(), type=house_giving + 10 ** 6)
            print(
                f"No takers, buying {'{:.2f}'.format(-surplus_house)}kWh from house {house_giving}"
            )

        # Reset surplus
        with self.surplus.get_lock():
            self.surplus.value = 0

    def write(self) -> None:
        """
        Update the cost of a kWh after the turn is over
        """

        # Get the weather conditions
        with self.weather_shared.get_lock():
            temperature = self.weather_shared[0]
            cloud_coverage = self.weather_shared[1]

        # Update the price
        self.daily_consumption.get_lock().acquire()
        self.politics.get_lock().acquire()
        self.economy.get_lock().acquire()
        with self.price_shared.get_lock():
            self.price_shared.value = (
                self.gamma * self.price_shared.value
                + self.alpha[0] * 1 / (16 + temperature)
                + self.alpha[1] * cloud_coverage
                + self.alpha[2] * self.daily_consumption.value
                + self.beta[0] * 1 / self.politics.value
                + self.beta[1] * 1 / self.economy.value
            )
            print(
                f"{Fore.BLUE}New price is {round(self.price_shared.value, 2)} €/kWh{Style.RESET_ALL}"
            )
        self.daily_consumption.get_lock().release()
        self.politics.get_lock().release()
        self.economy.get_lock().release()

        # Politics and economy tension go down, score goes up, with a limit of 100
        with self.economy.get_lock():
            self.economy.value = min(100, self.economy.value + 10)
            print(
                f"{Fore.MAGENTA}Economy situation: {self.economy.value}/100{Style.RESET_ALL}"
            )

        with self.politics.get_lock():
            self.politics.value = min(100, self.politics.value + 10)
            print(
                f"{Fore.MAGENTA}Politics situation: {self.politics.value}/100{Style.RESET_ALL}"
            )

    def kill(self):
        """
        Kills softly the child processes and then himself
        """

        print(f"{Fore.RED}Stopping market, politics and economics{Style.RESET_ALL}")

        self.politics_process.kill()
        self.economics_process.kill()

        super().kill()
