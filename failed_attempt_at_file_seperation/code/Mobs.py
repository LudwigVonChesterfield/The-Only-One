from code.Atoms import *

class Mob(Moveable):
    priority = 21

    def process(self):
        self.life()

    def life(self):
        return