from multiprocessing import Process


class Weather(Process):
    def __init__(self, temperature, cloud_coverage):
        super(Weather, self).__init__()
        self.temperature = temperature
        self.cloud_coverage = cloud_coverage

    def run(self):
        print("ok weather")
