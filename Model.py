class Model:
    def __init__(self):
        self.ref = ""
        self.name = ""
        self.deps = []
        self.outgoing_deps = []
        self.isProjectModel = True
        self.isToIgnore = False
        self.weight = 0

