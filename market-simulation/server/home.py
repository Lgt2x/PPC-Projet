from multiprocessing import Process


class Home(Process):
    def __init__(self, nb_houses):
        super().__init__()
        self.nb_houses = nb_houses
