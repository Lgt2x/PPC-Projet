from multiprocessing import Process


class City(Process):
    def __init__(self, nb_houses):
        super(City, self).__init__()
        self.nb_houses = nb_houses

    def run(self):
        print("ok city", self.nb_houses)
