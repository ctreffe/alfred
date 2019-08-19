class DataManager():
    def __init__(self, exp):
        self._experiment = exp


class Experiment():
    def __init__(self, input):
        self.input = input
        self.datamanager = DataManager(self)

exp = Experiment(3)
exp.input = 4

print(exp.input)
print(exp.datamanager._experiment.input)