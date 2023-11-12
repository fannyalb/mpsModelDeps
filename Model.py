class Model:
    def __init__(self):
        self.ref = ""
        self.name = ""
        self.outgoing_deps = []
        self.incoming_deps = []
        self.isProjectModel = True
        self.isToIgnore = False
        self.weight = 0

    def getInstability(self):
        fan_in = len(self.incoming_deps)
        fan_out = len(self.outgoing_deps)
        if((fan_in + fan_out) == 0):
            return 1
        instability = fan_out / (fan_in + fan_out)
        return instability

    def dependsOn(self, other):
        return other in self.outgoing_deps

    def __eq__(self, other):
        if isinstance(other, Model):
            return self.ref == other.ref
        return False

    def __ne__(self, other):
        equal = self.__eq__(other)
        if isinstance(other, Model):
            return not equal
        return True

