from multiprocessing import Process


class Market(Process):
    def __init__(self, politics, economy, speculation):
        super().__init__()
        self.politics = politics
        self.economy = economy
        self.speculation = speculation

    def run(self):
        print("ok market")
